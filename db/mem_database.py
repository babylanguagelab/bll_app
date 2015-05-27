## @package db.mem_database

from db.database import Database

## This class provides all the functionality of database.py, but using an in-memory database (non-persistent).
# An in-memory database is significantly faster than a disk-based one. This can be useful if you want
# simple SQL-query/sort functionality to sift through some data. You can build youself a temporary DB and
# even dump the results to a csv file when you're done. See CSVDatabase.py for more info on that sort of thing.
class MemDatabase(Database):
    ## Constructor
    # @param self
    def __init__(self):
        #create an in-memory SQLite database, just pass in this special identifier instead of a filename
        super(MemDatabase, self).__init__(':memory:')

    ## Writes this in-memory database to a *.db file on disk
    #  @param self
    #  @param filename (string) path to the *.db file you wish to write to (will be created if it doesn't exist)
    def dump_to_file(self, filename):
        file_db = Database(filename)
        sql_iter = self.conn.iterdump()

        for line in sql_iter:
            file_db.execute_stmt(line)
        
        file_db.close()
