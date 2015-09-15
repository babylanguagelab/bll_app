## @package data_structs.check2

from data_structs.base_objects import DBObject
from db.bll_database import DBConstants
from data_structs.test2 import Test2
from datetime import datetime

import pickle

## This class represents one trial's worth of data for the reliability2 app.
class Check2(DBObject):
    ## Constructor
    # @param self
    # @param csv_filename (string) path to the csv file that will be used - blocks will be picked from this file and presented to the user (see parsers.csv_parser for a list of the columns that must be present. In addition to those, we also need "environment" and "activity" columns.)
    # @param wav_foldername (string) path to a folder containing all the wav files that correspond to blocks that could be picked from the csv file
    # @param activities (list) list of strings, one for each activity that will be run (within each environment). E.g. ['mealtime', 'playtime', ...]
    # @param environments (list) list of strings, one for each environment that will be run. E.g ['home', 'daycare centre', ...]
    # @param blocks_per_activity (int) the number of 5 minute blocks that will be picked for each activity (blocks will be picked for each activity, separately for each environment)
    # @param completed (string=None) timestamp string representing the date/time when this check2 was completed. Is None if it has not yet been completed by the user.
    # @param created (string=None) timestamp string representing the date/time when this check2 was created by the user. This is assigned by the database in the insert() method. So if the check2 is not in the DB, this may be None.
    # @param modified (string=None) timestamp string representing the last time this check2 was modified by the user. For example, the last time the progress in the application was saved when working on this check. This is assigned by the DB. It will be None if the check2 has never been saved in an incomplete trial. It is possible for check2s to be completed, but not modified (if the user goes through the whole trial without saving/quitting).
    # @param test2s (list=[]) a list of all the Test2 data structure objects for this trial. Each Test2 object represents (and contains all the data for) the input for a single block that the user has completed.
    # @param test2_index (int=0) the index we are currently sitting at in the test2 list (previous param). This information is used to restore the state of the app to where the user left off, when a saved check2 is loaded back up.
    # @param db_id (int=None) the primary key value of this check2 in the check2 database table. In general, code should not set this. It's set from db_select(), and upon db_insert(). Will be None if object is not yet in the DB.
    def __init__(
        self,
        csv_filename,
        wav_foldername,
        activities, #array
        environments, #array
        blocks_per_activity,
        completed=None, #timestamp
        created=None, #timestamp
        modified=None, #timestamp
        test2s=[], #array of Test2 objects
        test2_index=0, #index of the test2 to display in the UI
        db_id=None
        ):

        super(Check2, self).__init__()

        self.csv_filename = csv_filename
        self.wav_foldername = wav_foldername
        self.activities = activities
        self.environments = environments
        self.blocks_per_activity = blocks_per_activity
        self.completed = completed
        self.created = created
        self.modified = modified
        self.test2s = test2s
        self.test2_index = test2_index
        self.db_id = db_id

    ## Overwrites the completed timestamp (both in the DB and the object attribute for this instance) with the current date/time.
    # @param self
    # @param db (BLLDatabase) a database object
    def update_completed(self, db):
        #allow the DB to set the timestamp value
        self._update_timestamp(db, 'completed')
        #then re-select it and update the instance attribute
        self.completed = db.select('checks2', ['datetime(completed,\'localtime\')'], 'id=?', [self.db_id])

    ## Overwrites the modified timestamp (both in the DB and the object attribute for this instance) with the current date/time.
    # @param self
    # @param db (BLLDatabase) a database object
    def update_modified(self, db):
        #allow the DB to set the timestamp value
        self._update_timestamp(db, 'modified')
        #select it back and update the instance attribute
        self.modified = db.select('checks2', ['datetime(modified,\'localtime\')'], 'id=?', [self.db_id])

    ## Updates the test2_index value in the database. It is set to the current value for this instance. If the instance is not already in the dd, an exception is raised.
    # @param self
    # @param db (BLLDatabase) a database object
    def update_test2_index(self, db):
        if self.db_id != None:
            db.update('checks2', ['test2_index'], 'id=?', [self.test2_index, self.db_id])
        else:
            raise Exception('Cannot update test2_index on Check2 instance that is not in the databse.')

    ## Performs a db update of a timestamp column, setting it to the date/time at the point this method is executed. If this instance is not already in the db, an exception is raised.
    # @param self
    # @param db (BLLDatabase) a database object
    # @param col (string) name of the timestamp column from the checks2 database table to update.
    def _update_timestamp(self, db, col):
        if self.db_id != None:
            db.update_timestamp_col('checks2', col, 'id=?', [self.db_id])
        else:
            raise Exception('Cannot update timestamp because Check2 instance is not in the database.')

    ## See superclass description.
    # If any of this instance's test2 objects are not yet in the DB, this method will insert them as well.
    def db_insert(self, db):
        super(Check2, self).db_insert(db)

        cols = 'csv_file wav_folder activities environments blocks_per_activity completed test2_index'.split() #omit the 'modified' and 'created' columns - they will default to current timestamp

        #pickle the lists of activities and environments (convert them to a format in which we can just store the object instance in the database), as they are of variable length.
        row = [self.csv_filename, self.wav_foldername, pickle.dumps(self.activities), pickle.dumps(self.environments), self.blocks_per_activity, self.completed, self.test2_index]

        #grab the last inserted id and use it to assign this object's db_id
        last_ids = db.insert('checks2', cols, [row])
        self.db_id = last_ids[0]

        #re-select and update this instance's timestamp attributes (these are always assigned by the DB)
        checks2_rows = db.select('checks2', ["datetime(created,'localtime')", "datetime(modified,'localtime')"], 'id=?', [str(self.db_id)])
        self.created = datetime.strptime(checks2_rows[0][0], DBConstants.DB_DATETIME_FMT)
        self.modified = datetime.strptime(checks2_rows[0][1], DBConstants.DB_DATETIME_FMT)

        #ensure that all of this check2's test2 objects are in the DB
        if self.test2s:
            for t in self.test2s:
                if t.db_id == None:
                    t.db_insert(db)

    ## See superclass description.
    def db_delete(self, db):
        super(Check2, self).db_delete(db)

        #this will cascade and remove all corresponding test2 rows
        num_rows = db.delete('checks2', 'id=?', [self.db_id])
        if num_rows == 1:
            self.db_id = None

        return num_rows

    ## See superclass description.
    @staticmethod
    def db_select(db, ids=[]):
        DBObject.db_select(db, ids)

        #build the SQL where clause using the ids passed in
        where_cond = DBObject._build_where_cond_from_ids(ids)

        #do the select to retrieve the a list of raw data
        rows = db.select('checks2', 'csv_file wav_folder activities environments blocks_per_activity datetime(completed,\'localtime\') datetime(created,\'localtime\') datetime(modified,\'localtime\') test2_index id'.split(), where_cond)

        #create Check2 objects from the selected data and return them
        check2_list = []
        for cur_row in rows:
            #each check2 has zero or more Test2s, which can be retrieved using this static method
            test2s = Test2.db_select_by_check2(db, cur_row[9])

            check2 = Check2(
                cur_row[0],
                cur_row[1],
                #un-pickle the lists of activities and environments (the loads() call will return an instance of a list)
                pickle.loads(cur_row[2]),
                pickle.loads(cur_row[3]),
                cur_row[4],
                cur_row[5],
                cur_row[6],
                cur_row[7],
                test2s,
                cur_row[8],
                cur_row[9]
                )

            check2_list.append(check2)

        return check2_list
