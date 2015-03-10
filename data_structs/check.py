## @package data_structs.check

from data_structs.base_objects import DBObject
from data_structs.seg_filters import *
from db.bll_database import DBConstants
from datetime import datetime
from data_structs.test import Test

## A saved collection of settings that can be used to generate stats from a TRS file (for the Reliability App).
class Check(DBObject):
    ## Constructor
    #  @param self
    #  @param name (string) user-defined name for this check
    #  @input_filename (string) absolute path to the trs/csv file that this check will be run on
    #  @wav_filename (string) absolute path to the wav file that this check will use
    #  @num_segs (int) integer representing the upper limit on the number of segs that can be picked (takes precidence over previous param when limit is exceeded). WIll be set to 0 if no limit is to be enforced.
    #  @param default_context_padding (int) number of seconds to pad sound clip, on each side, when context is being used
    #  @param completed (string=None) timestamp string representing the date/time of this check's first run. In general, code should not set this. It's set from db_select(). Will be None if this check has not yet been run.
    #  @param db_id (int=None) Primary key value of this check in the Checks database table. In general, code should not set this. It's set from db_select(), and upon db_insert(). Will be None if object is not yet in the DB.
    #  @param filters (list=[]) List of SegFilter objects to filter the segments from the trs file before picking the clips to test on.
    #  @param pick_randomly (boolean=False) Set to True if user elected to randomly pick segments, False if they want continuous segments to be used.
    #  @param last_run (string=None) String timestamp representing the last time this check was run. Set to None if it has never been run before.
    def __init__(self,
                 name,
                 input_filename,
                 wav_filename,
                 num_segs,
                 default_context_padding,
                 tests,
                 test_index,
                 completed=None,
                 created=None,
                 db_id=None,
                 filters=[],
                 pick_randomly=False,
                 last_run=None):
        
        super(Check, self).__init__()
        
        self.name = name
        self.created = created
        self.input_filename = input_filename
        self.wav_filename = wav_filename
        self.num_segs = num_segs
        self.default_context_padding = default_context_padding
        self.tests = tests
        self.test_index = test_index
        self.completed = completed
        self.db_id = db_id
        self.filters = filters
        self.pick_randomly = pick_randomly
        self.last_run = last_run

    ## See superclass description.
    def db_insert(self, db):
        super(Check, self).db_insert(db)
        
        cols = 'name input_filename wav_filename num_segs default_context_padding test_index completed pick_randomly'.split()
        row = [self.name, self.input_filename, self.wav_filename, self.num_segs, self.default_context_padding, self.test_index, self.completed, self.pick_randomly]

        #grab the last inserted id and use it to assign this object's db_id
        last_ids = db.insert('checks', cols, [row])
        self.db_id = last_ids[0]

        #insert this object's filters, if they haven't already been inserted
        for cur_filter in self.filters:
            if cur_filter.db_id == None:
                cur_filter.db_insert(db)

            #always insert a row in this relational table, to link this check to its filters
            db.insert('checks_to_seg_filters', 'seg_filter_id check_id'.split(), [[cur_filter.db_id, self.db_id]])

        #this will also update the corresponding attribute in self
        self._update_timestamp('last_run', db)

        #we allow the DB to set the created timestamp - we do an additional select here to retrieve it right after the row was inserted
        #Note 1: The DB stores all timestamps in GMT format. When selecting, we must convert back to local time zone (datetime function does this)
        #Note 2: for some reason, sqlite complains if id param is not a string
        checks_rows = db.select('checks', ["datetime(created,'localtime')"], 'id=?', [str(self.db_id)])
        self.created = datetime.strptime(checks_rows[0][0], DBConstants.DB_DATETIME_FMT)

        for cur_test in self.tests:
            if cur_test.db_id == None:
                cur_test.db_insert(db)

    ## See superclass description.
    #  @returns (int) the number of rows that were soft deleted.
    def db_delete(self, db):
        super(Check, self).db_delete(db)

        #this will cascade and delete from checks_to_seg_filters table
        for cur_filter in self.filters:
            cur_filter.db_delete(db)

        for cur_test in self.tests:
            cur_test.db_delete(db)

        #this will cascade and delete from tests table
        rows = db.delete('checks', 'id=?', [self.db_id])

        self.db_id = None

        return rows

    ## See superclass description.
    #  @returns (list) list of Check objects
    @staticmethod
    def db_select(db, ids=[]):
        DBObject.db_select(db, ids)

        #build the SQL where clause using the ids passed in
        where_cond = None
        if ids:
            where_cond = DBObject._build_where_cond_from_ids(ids)

        #perform the select and create Check objects for each row
        rows = db.select('checks', 'name input_filename wav_filename num_segs default_context_padding test_index datetime(completed,\'localtime\') datetime(created,\'localtime\') id pick_randomly datetime(last_run,\'localtime\')'.split(), where_cond)
        checks = []
        for cur_row in rows:
            check_id = cur_row[8]
            #select the corresponding filters via a relation table
            filters = SegFilter.db_select_by_ref(db, 'checks_to_seg_filters', 'seg_filter_id', 'check_id', check_id)

            tests = Test.db_select_by_check(db, cur_row[8])
            
            checks.append( Check(cur_row[0],
                                 cur_row[1],
                                 cur_row[2],
                                 cur_row[3],
                                 cur_row[4],
                                 tests,
                                 cur_row[5],
                                 datetime.strptime(cur_row[6], DBConstants.DB_DATETIME_FMT) if cur_row[6] != None else None,
                                 datetime.strptime(cur_row[7], DBConstants.DB_DATETIME_FMT) if cur_row[7] != None else None,
                                 cur_row[8],
                                 pick_randomly=bool(int(cur_row[9])),
                                 last_run=datetime.strptime(cur_row[10], DBConstants.DB_DATETIME_FMT) if cur_row[10] != None else None,
                                 filters=filters) )
            
        return checks

    ## Updates a timestamp column in the DB, and in this object instance. If the instance is not in the database, an exception is raised.
    # @param self
    # @param attr_name (string) name of the instance attribute we will be updating - this name must match the name of the column in the DB checks table.
    # @param db (BLLDatabase) a database instance
    def _update_timestamp(self, attr_name, db): #attr name must match db col name
        if self.db_id != None:
            #allow the DB to insert the timestamp
            db.update_timestamp_col('checks', attr_name, 'id=?', [self.db_id])

            #select the timestamp and convert it to localtime
            rows = db.select('checks', ["datetime(%s,'localtime')" % (attr_name)], 'id=?', [self.db_id])
            #convert it to a more readable format for display in the UI
            setattr(self, attr_name, datetime.strptime(rows[0][0], DBConstants.DB_DATETIME_FMT))
        else:
            raise Exception('Cannot update timestamp because Check object is not in the database.')

    ## Sets the 'completed' attribute (a timestamp in string form) of this Check to the current date/time
    #  @param self
    #  @param db (BLLDatabase) the DB handle object to use for the update operation
    def mark_as_completed(self, db):
        self._update_timestamp('completed', db)

    ## Updates the "last run" attribute/database column value.
    #  @param self
    #  @param db (BLLDatabase) the DB handle object to use for the update operation
    def mark_last_run(self, db):
        self._update_timestamp('last_run', db)

    ## Updates the test_index property/database column value. This allows us to restore a saved check to the position where the user left off. If the instance is not in the database, an exception is raised.
    #  @param self
    #  @param db (BLLDatabase) the DB handle object to use for the update operation
    def db_update_test_index(self, db):
        if self.db_id != None:
            db.update('checks', ['test_index'], 'id=?', [self.test_index, self.db_id])
        else:
            raise Exception('Cannot update test_index because Check instance is not in the database.')
