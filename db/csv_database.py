## @package db.csv_database

from collections import OrderedDict
from db.mem_database import MemDatabase
from datetime import datetime
from utils.enum import Enum
import csv
import os
#from db.database import Database

## This class provides a way to convert a csv file into an in-memory database.
# This allows you to do SQL-operations on the data, which in some circumstances can be much more convenient than implementing
# search (query), sort, or data modification methods in straight Python. The cost for doing this is a little extra time inserting all the data - however, this
# cost isn't usually too bad because in-memory databases are up to an order of magnitude faster than file-based ones.
# This class was implemented on a per-need basis, so some things (like delete(), or update for named
# columns added using add_column()) are not implemented yet. You can use the superclass's update() and
# delete() methods to do this yourself, or extend this class when the functionality is needed.
#
# Sample usage:
# \code{.py}
#
# #create a list of data types corresponding to the format of (a row in) your csv file
# data_types = [str, int, float, bool, str, str, str]
#
# #this will create a single in-memory table, whose columns can be referred to by an integer index value (see select()
# #call below)
# db = CSVDatabase(data_types)
#
# #insert the data from the csv file - don't forget to skip over the header row
# csv_reader.next()
# for row in csv_reader:
#   db.csv_insert(row)
#
# #you can add extra named columns to the db that do not exist in the csv file
# #Currently, these extra columns are not updatable - only selectable... This would not be too hard to change if
# #future code requires it.
# db.add_column('Extra column', bool)
#
# #update a value in column 3 (setting it to 2 wherever the value in column number 3 is equal to 5) - see
# #Database.update() for a more detailed description. Right now the where_cond requires the
# #column name, which is 'col<index>', making things less pretty than they could be...
# #The first column has an index of 0.
# db.update([3], where_cond='col3=?', params=[2, 5])
#
# #select some values from column with index 4 (where column index 3 is equal to the value 2)
# rows = db.select([4], where_cond='col3=?', params=[2])
#
# #dump the selected data to another csv file
# for line in rows:
#  csv_writer.writerow(line)
# \endcode
class CSVDatabase(MemDatabase):
    TABLE_NAME = 'data'
    COL_PREFIX = 'col' #column names are like "COL_PREFIX<index>" - e.g. col0, col1, col2, ...
    DATA_TYPES = {
        str: 'TEXT',
        float: 'REAL',
        int: 'INTEGER',
        bool: 'INTEGER', #sqlite does not have a separate boolean type. It's no trouble to convert these to integers for DB operations.
        datetime: 'TEXT', #sqlite doesn't have a datetime type, but provides functions that allows us to interpret strings as dates.
        #These should be entered in the form 'yyyy-mm-dd hh:mm:ss.sss'
        }
    ORDER_DIRS = Enum(['ASC', 'DESC'], ['ASC', 'DESC'])

    ## Constructor
    # @param self
    # @param col_datatypes (list) List of data type functions (these must be keys from the static CSVDatabase.DATA_TYPES dictionary) corresponding to the columns in your csv file.
    def __init__(self, header_row, col_datatypes):
        super(CSVDatabase, self).__init__()

        self.name_lookup = OrderedDict( zip(header_row, range(len(col_datatypes))) )
        self.header_row = list(header_row)
        self.col_datatypes = list(col_datatypes)
        self._create_data_table()

    #first row must be header
    @staticmethod
    def create_with_rows(rows, col_datatypes):
        db = CSVDatabase(rows[0], col_datatypes)
        
        for i in range(1, len(rows)):
            db.csv_insert(rows[i])

        return db
        
    @staticmethod
    def create_with_files(file_list, col_datatypes):
        file_in = open(file_list[0], 'rb')
        reader = csv.reader(file_in)
        db = CSVDatabase(reader.next(), col_datatypes)
        file_in.close()
        
        for cur_file in file_list:
            file_in = open(cur_file, 'rb')
            reader = csv.reader(file_in)
            cur_header = reader.next()

            if db.header_row == cur_header:
                for row in reader:
                    db.csv_insert(row)

                file_in.close()
            else:
                raise Exception('File %s has different column headers than the other files.' % (cur_file))

        return db

    ## Creates the single table used by this in-memory database.
    # @param self
    def _create_data_table(self):
        col_sql = 'id INTEGER PRIMARY KEY AUTOINCREMENT'
        for i in range(len(self.col_datatypes)):
            col_sql += ', %s%d %s NULL' % (CSVDatabase.COL_PREFIX, i, CSVDatabase.DATA_TYPES[self.col_datatypes[i]])

        data_sql = 'CREATE TABLE ' + CSVDatabase.TABLE_NAME + '(' + col_sql + ')'
        
        self.cursor.execute(data_sql)

    ## Inserts a row of data straight from a csv file. The data must have the types given in the col_datatypes param that was passed to the constructor or this will cause an exception.
    # @param self
    # @param csv_row (list) list of data from a csv file (corresponding to a single row)
    #  @returns (list) list of all the primary key values of the inserted rows    
    def csv_insert(self, csv_row):
        return super(CSVDatabase, self).insert(
            'data',
            map(lambda num: '%s%d' % (CSVDatabase.COL_PREFIX, num), range(len(self.col_datatypes))), [csv_row]
        )

    ## Selects data from the database. For a full list or parameters, see the database.py (superclass) select method. For the where_cond and order_by params, use column names like 'col<index>'.
    # @param col_indices (list=None) a list of the indices of the columns you'd like to select.
    #  @returns (list) list of lists, one sub-list per row. Each sublist contains data in the order specified by cols.
    def csv_select_by_index(
            self,
            col_indices=None,
            where_cond=None,
            params=[],
            order_by_indices=None,
            order_by_dirs=None,
            dump_sql=False,
            fcn_indices=None,
            fcns=None,
            group_by_index=None
    ):
        if col_indices == None:
            col_indices = range(len(self.col_datatypes))

        cols = []
        for index in col_indices:
            name = '%s%d' % (CSVDatabase.COL_PREFIX, index)
            cols.append(name)

        #add in any aggregate functions
        if fcn_indices and fcns:
            for i in range(len(fcn_indices)):
                for j in range(len(col_indices)):
                    if fcn_indices[i] == col_indices[j]:
                        cols[j] = '%s(%s)' % (fcns[i], cols[j])

        group_by = None
        if group_by_index != None:
            group_by = '%s%d' % (CSVDatabase.COL_PREFIX, group_by_index)

        order_by = None
        if order_by_indices != None:
            order_by = ''
            for i in range(len(order_by_indices)):
                index = order_by_indices[i]
                order_by += '%s%d %s' % (CSVDatabase.COL_PREFIX, index, order_by_dirs[i])
                if i < len(order_by_indices) - 1:
                    order_by += ', '

            #order_by = '%s%d' % (CSVDatabase.COL_PREFIX, order_by_index)
                
        return super(CSVDatabase, self).select(
            CSVDatabase.TABLE_NAME,
            #['id'] + map(lambda num: '%s%d' % (CSVDatabase.COL_PREFIX, num), col_indices),
            cols,
            where_cond=where_cond,
            params=params,
            order_by=order_by,
            dump_sql=dump_sql,
            group_by=group_by
            )

    def _get_col_indices(self, col_names):
        col_indices = None
        if col_names == None:
            col_indices = self.name_lookup.values()
        else:
            col_indices = [self.name_lookup[name] for name in col_names]

        return col_indices

    def _build_where_clause(self, where_body, where_cols):
        where_cond = None
        if where_body and where_cols:
            db_col_names = []
            for col in where_cols:
                db_col_names.append( '%s%d' % (CSVDatabase.COL_PREFIX, self.name_lookup[col]) )
            where_cond = where_body % tuple(db_col_names)

        return where_cond

    # def get_db_col_names(self, col_names):
    #     return map(lambda i: '%s%d' % (CSVDatabase.COL_PREFIX, i), self._get_col_indices(col_names))

    def get_db_col_names(self):
        return dict(zip(
                self.header_row,
                map(lambda i: '%s%d' % (CSVDatabase.COL_PREFIX, i), self._get_col_indices(self.header_row))
            ))

    def csv_select_by_name(
            self,
            col_names=None,
            where_body=None,
            where_cols=None,
            params=[],
            order_by=None,
            order_by_dirs=None,
            dump_sql=False,
            fcn_col_names=None,
            fcns=None,
            group_by=None
    ):
        col_indices = self._get_col_indices(col_names)
        where_cond = self._build_where_clause(where_body, where_cols)
        fcn_indices = self._get_col_indices(fcn_col_names)
        
        group_by_index = None
        if group_by != None:
            group_by_index = self._get_col_indices([group_by])[0]

        order_by_indices = None
        if order_by != None:
            order_by_indices = self._get_col_indices(order_by)
            #order_by_index = self._get_col_indices([order_by])[0]

        return self.csv_select_by_index(
            col_indices=col_indices,
            where_cond=where_cond,
            params=params,
            order_by_indices=order_by_indices,
            order_by_dirs=order_by_dirs,
            dump_sql=dump_sql,
            fcn_indices=fcn_indices,
            fcns=fcns,
            group_by_index=group_by_index
        )

    ## Updates data in the database. For a full list or parameters, see the database.py (superclass) select method. For the where_cond param, use column names like 'col<index>'.
    # @param col_indices (list) a list of the indices of the columns you'd like to update.
    #  @returns (int) number of rows updated
    def csv_update_by_index(self, col_indices, where_cond=None, params=[], dump_sql=False):
        cols = map(lambda num: '%s%d' % (CSVDatabase.COL_PREFIX, num), col_indices)
        
        return super(CSVDatabase, self).update(
            CSVDatabase.TABLE_NAME,
            cols,
            where_cond=where_cond,
            params=params,
            dump_sql=dump_sql
            )

    def csv_delete_by_index(
            self,
            where_cond=None,
            params=[]
    ):
        return super(CSVDatabase, self).delete(
            CSVDatabase.TABLE_NAME,
            where_cond,
            params
        )

    def csv_delete_by_name(
            self,
            where_body=None,
            where_cols=None,
            params=[]
    ):
        where_cond = self._build_where_clause(where_body, where_cols)

        return self.csv_delete_by_index(
            where_cond,
            params
        )

    #Example:
    #col_names = ['File_Name', 'Child_Gender']
    #where_body = '%s > ? and %s > ?'
    #where_cols = ('FAN, 'CHN')
    #params = (23.3, 45.5, 20.0, 10.0)
    # will generate the following SQL:
    # 'update data set col0=23.3, col3=45.5 where col10 > 20.0 and col11 > 10.0;'
    # Assuming 'File_Name' -> col0, 'Child_Gender' -> col3, 'FAN' -> col10, 'CHN' -> col11.
    def csv_update_by_name(self, col_names, where_body=None, where_cols=None, params=[], dump_sql=False):
        col_indices = None
        if col_names == None:
            col_indices = self.name_lookup.values()
        else:
            col_indices = [self.name_lookup[name] for name in col_names]

        where_cond = None
        if where_body and where_cols:
            db_col_names = []
            for col in where_cols:
                db_col_names.append( '%s%d' % (CSVDatabase.COL_PREFIX, self.name_lookup[col]) )
            where_cond = where_body % tuple(db_col_names)

        return self.csv_update_by_index(col_indices, where_cond, params, dump_sql)

    def get_db_col_name(self, text_name):
        return '%s%d' % (CSVDatabase.COL_PREFIX, self.name_lookup[name])

    ## Adds a named column to the this database's single table.
    # Currently, these columns are not updatable using the csv_update method above.
    # You'll need to do it manually using the superclass' update() method, or implement something new.
    # The values in the newly added column are all set to NULL.
    # @param self
    # @param name (string) name of the column to add.
    # @param datatype (fcn) a data-type function (must be in the keys of the static CSVDatabase.DATA_TYPES dictionary) corresponding to the type of data that this column will hold
    def add_column(self, name, datatype):
        col_index = len(self.col_datatypes)
        
        self.cursor.execute('ALTER TABLE %s ADD COLUMN %s %s NULL' % (
                CSVDatabase.TABLE_NAME,
                '%s%d' % (CSVDatabase.COL_PREFIX, col_index),
                CSVDatabase.DATA_TYPES[datatype],
                            ))
        
        self.col_datatypes.append(datatype)
        self.header_row.append(name)
        self.name_lookup[name] = col_index

    def _remove_cols(self, row, col_indices):
        filtered_row = []
        for i in range(len(row)):
            if not (i in col_indices):
                filtered_row.append(row[i])

        return filtered_row

    def write_to_file(self, path, omit_col_indices=[]):
        file_out = open(path, 'wb')
        writer = csv.writer(file_out)
        rows = self.csv_select_by_index() #select *

        header = self.header_row
        if omit_col_indices:
            header = self._remove_cols(header, omit_col_indices)
            
        writer.writerow(header)
        for cur_row in rows:
            if omit_col_indices:
                cur_row = self._remove_cols(cur_row, omit_col_indices)
            writer.writerow(cur_row)
        
        file_out.close()

    def read_file(self, path):
        file_in = open(path, 'rb')
        reader = csv.reader(file_in)

    def set_blanks_to_null(self):
        for col in self.header_row:
            self.csv_update_by_name(
                [col],
                where_body="%s = ?",
                where_cols=[col],
                params=[None, '']
            )
        
