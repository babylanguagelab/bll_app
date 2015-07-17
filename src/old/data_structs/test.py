## @package data_structs.test

from data_structs.base_objects import DBObject
from data_structs.segment import Segment

## This class represents an instance of a single step in a Check (Reliability Application).
#  When a check is run, a Check object is created, and a number of Tests are performed (the exact number is specified by the user.). Each test consists of playing a sound clip (either with or without context), and recording the user's response (the user attempts to identify the type of segment being played).
class Test(DBObject):
    ## Constructor
    #  @param self
    #  @param category_input (int) this is the user's response that they've selected from the dropdown. It corresponds to one of the options from DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.RELIABILITY_CATEGORIES]
    #  @param segment (Segment) the segment being played
    #  @param check (Check) pointer to the instance of the check this test is being performed for
    #  @param with_context (boolean) True if sound clip is being padded on both sides, False otherwise
    #  @param db_id (int) primary key from the tests DB table. Should be None if this test is not yet in the DB.
    #  @param adjusted_padding(int) The user can adjust this value on the fly for each test that is presented with context. If you pass None, this will be inferred from the with_context and/or check (context_padding attribute) parameters. Regardless of what you pass here, if with_context==False, then the DB will contain a zero for this attribute.
    #  @param syllables(int=0) number of syllables in sound clip (entered by user)
    #  @param adjusted_start (float) the user-specified absolute start time (in seconds)
    #  @param adjusted_end (float) the user-specified absolute end time (in seconds)
    def __init__(self, check_id, category_input, syllables_w_context, syllables_wo_context, segment, is_uncertain, context_padding, db_id=None):
        self.check_id = check_id
        self.category_input = category_input
        self.syllables_w_context = syllables_w_context
        self.syllables_wo_context = syllables_wo_context
        self.seg = segment
        self.is_uncertain = is_uncertain
        self.context_padding = context_padding
        self.db_id = db_id

    ## See superclass description. This Test's corresponding Check object must already have been inserted into the database before this method is called. If not, an excpetion will be raised.
    def db_insert(self, db):
        super(Test, self).db_insert(db)

        #make sure the Check is already in the DB. If it's not, this object's check_id will be None. If we stored the Test anyway, we'd have a NULL value for the check_id column, and  we would
        #have no way of matching this Test up with its Check when it is selected from the DB.
        if self.check_id == None:
            raise Exception('Attempting to insert Test object whose corresponding Check object is not yet in the database. Insertion aborted.')

        #insert the Segment, if necessary
        if self.seg.db_id == None:
            self.seg.db_insert(db)

        #insert this test
        self.db_id = db.insert('tests',
                               'check_id category_input syllables_w_context syllables_wo_context segment_id is_uncertain context_padding'.split(),
                               [[self.check_id, self.category_input, self.syllables_w_context, self.syllables_wo_context, self.seg.db_id, self.is_uncertain, self.context_padding]])[0]

    ## See superclass description.
    def db_delete(self, db):
        super(Test, self).db_delete(db)
        
        if self.db_id != None:
            db.delete('tests', 'id=?', [self.db_id])
            self.db_id = None
            
            self.seg.db_delete(db)

    def db_update_user_inputs(self, db):
        if self.db_id != None and self.seg.db_id != None:
            db.update('tests', 'category_input syllables_w_context syllables_wo_context is_uncertain context_padding'.split(), ' id=?', [self.category_input, self.syllables_w_context, self.syllables_wo_context, self.is_uncertain, self.context_padding, self.db_id])

            db.update('segments', 'user_adj_start user_adj_end'.split(), ' id=?', [self.seg.user_adj_start, self.seg.user_adj_end, self.seg.db_id])

    @staticmethod
    def _build_from_db_rows(db, rows):
        #select the corresponding Segments, create the Test objects
        test_list = []
        for cur_row in rows:
            seg = Segment.db_select(db, [cur_row[5]])[0]
            
            test = Test(
                cur_row[1],
                cur_row[2],
                cur_row[3],
                cur_row[4],
                seg,
                cur_row[6],
                cur_row[7],
                cur_row[0],
                )
            test_list.append(test)

        return test_list

    ## See superclass description.
    @staticmethod
    def db_select(db, ids=[]):
        DBObject.db_select(ids)

        #select the test data
        rows = db.select('tests',
                         'id check_id category_input syllables_w_context syllables_wo_context segment_id is_uncertain context_padding'.split(),
                         DBObject._build_where_cond_from_ids(ids)
                         )

        return Test._build_from_db_rows(db, rows)

    @staticmethod
    def db_select_by_check(db, check_id):
        rows = db.select('tests', 'id check_id category_input syllables_w_context syllables_wo_context segment_id is_uncertain context_padding'.split(), ' check_id=?', [check_id], order_by='id')

        return Test._build_from_db_rows(db, rows)
