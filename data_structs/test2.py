## @package data_structs.test2

from data_structs.base_objects import DBObject
from db.bll_database import DBConstants

import pickle

## This class contains information for a single block that has been reviewed by the user (for the Reliability2 App).
# Each Check2 represents an entire testing run, and contains a list of Test2 objects that represent the individual blocks.
class Test2(DBObject):
    ## Constructor
    # @param self
    # @param check2_id (int) the DB id of the parent check2 object for this test2
    # @param wav_filename (string) path to the wav file from which a sound clip for this test2 will be played
    # @param child_code (string) this is a string built from several columns in the input spreadsheet (see parsers.reliability2_parser's get_child_code() method. It looks like this: 'C002_20090831'
    # @param spreadsheet_timestamp (string) built from spreadsheet column, in the format "dd mm yyyy <elapsed seconds as a float>" (this, together with child_code, uniquely identifies a row)
    # @param child_vocs (int=0) the number of child vocalizations - this is grabbed from a user-adjustable spin button control in the UI
    # @param transcription (string) the user-entered transcription text
    # @param ui_save_data (dictionary=None) a dictionary of data with keys corresponding to the names of UI controls. This is pickled and stored here so that we can restore the UI state when a saved Check2 is loaded back up. See the Reliability2 UI classes for how this dictionary is populated.
    # @param db_id (int) the primary key value of the row corresponding to this instance from the checks2 db table. This should be set to None if the instance is not in the database.
    def __init__(
        self,
        check2_id,
        wav_filename,
        child_code,
        spreadsheet_timestamp,
        child_vocs=0,
        transcription='',
        ui_save_data=None,
        db_id = None
        ):

        super(Test2, self).__init__()

        self.check2_id = check2_id
        self.wav_filename = wav_filename
        self.child_code = child_code
        self.spreadsheet_timestamp = spreadsheet_timestamp
        self.child_vocs = child_vocs
        self.transcription = transcription
        self.ui_save_data = ui_save_data        
        self.db_id = db_id

    ## Retrieves a value (in seconds) indicating how far we are from the start of the entire wav file.
    # @param self
    # @returns (float) offset value in seconds
    def get_start_time_offset(self):
        #timestamp format is "dd mm yyyy <elapsed seconds as a float>"
        return int(self.spreadsheet_timestamp.split()[-1])

    ## See superclass description
    def db_insert(self, db):
        super(Test2, self).db_insert(db)

        #raise a fuss if the enclosing Check2 object is not in the DB (silently inserting child objects is reasonably sane, but this is a parent object, and silently inserting them makes things insane)
        if self.check2_id == None:
            raise Exception('Cannot insert Test2 object whose parent Check2 object is not in the database.')

        cols = 'check2_id wav_file child_vocs transcription ui_save_data child_code spreadsheet_timestamp'.split()
        #we pickle the ui_save_data dictionary (i.e. store the actual object instance in the DB)
        row = [self.check2_id, self.wav_filename, self.child_vocs, self.transcription, pickle.dumps(self.ui_save_data), self.child_code, self.spreadsheet_timestamp]

        #grab the last inserted id and use it to assign this object's db_id
        last_ids = db.insert('tests2', cols, [row])
        self.db_id = last_ids[0]

    ## See superclass description.
    def db_delete(self, db):
        super(Test2, self).db_delete(db)

        num_rows = db.delete('tests2', 'id=?', [self.db_id])
        if num_rows == 1:
            self.db_id = None

        return num_rows

    ## Static method to construct a list of Test2 objects from a list of database rows (from the test2 table).
    # @param rows (list) a list of lists, one sublist per row.
    # @returns (list) a list of Test2 instances
    @staticmethod
    def _build_from_db_rows(rows):
        test2_list = []
        for cur_row in rows:
            test2 = Test2(
                cur_row[0],
                cur_row[1],
                cur_row[2],
                cur_row[3],
                cur_row[4],
                cur_row[5],
                #we unpickle the ui_save_data to get the dictionary object back
                pickle.loads(cur_row[6]),
                cur_row[7],
                )

            test2_list.append(test2)

        return test2_list

    ## See superclass description.
    @staticmethod
    def db_select(db, ids=[]):
        DBObject.db_select(db, ids)

        where_cond = DBObject._build_where_cond_from_ids(ids)

        rows = db.select('tests2', 'check2_id wav_file child_code spreadsheet_timestamp child_vocs transcription ui_save_data id'.split(), where_cond)

        return Test2._build_from_db_rows(rows)

    ## Static method to (query the DB and) construct a list of Test2 instances corresponding to a particular Check2 object.
    # @param db (BLLDatabase) a database object to query
    # @param check2_id (int) primary key value of the check2 whose test2's we're looking for
    # @returns (list) list of Test2 instances, ordered by db_id
    @staticmethod
    def db_select_by_check2(db, check2_id):
        DBObject.db_select(db, [check2_id])

        rows = db.select('tests2', 'check2_id wav_file child_code spreadsheet_timestamp child_vocs transcription ui_save_data id'.split(), ' check2_id=?', [check2_id], order_by='id')

        return Test2._build_from_db_rows(rows)
