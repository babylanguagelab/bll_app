#!/usr/bin/python2
## @package db.database

import sqlite3
import logging
import traceback
import sys
import csv

## This class provides a basic API layer on top of an SQLite database.
#  Ideally, all SQL should be restricted to this file. Calling code can form queries using the select() method. You can also update(), insert(), and delete().
class Database(object):
    ## Constructor
    #  @param self
    #  @param db_filename (string) absolute path to the sqlite3 database file (if this does not exist, a new database file will be created)
    def __init__(self, db_filename):
        #self.logger = logging.getLogger(__name__)

        #create/open the database
        self.conn = sqlite3.connect(db_filename)

        #grab a cursor object that can be used to execute statements
        self.cursor = self.conn.cursor()

        #turn on foreign keys - they're disabled by default in sqlite
        self.conn.execute("PRAGMA foreign_keys = ON")

    ## Closes the database connection, releasing any resources that it was using.
    #  @param self
    def close(self):
        self.cursor.close()
        self.conn.close()

    ## Executes a verbatim SQL statement.
    # This is used for the custom processing scripts (custom_scripts/ directory), and shouldn't
    # really be used by any general apps, since it doesn't do any sanitization.
    # @param self
    # @param stmt (string) a complete sql statement to execute.
    def execute_stmt(self, stmt):
        try:
            self.cursor.executescript(stmt)
            self.conn.commit()

        except Exception as err:
            logging.error('Error executing SQL statement "%s":\n%s' % (stmt, err))
            #print 'Error executing SQL statement "%s":\n%s' % (stmt, err)
            self.conn.rollback()

    ## Reads and executes a sql script file.
    #  @param self
    #  @param filename (string) full path to sql file
    def execute_script(self, filename):
        try:
            sql_file = open(filename, 'r')
            sql = sql_file.read()
            sql_file.close()
            self.cursor.executescript(sql)
            self.conn.commit()

        #rollback on error
        except Exception as err:
            logging.error('Error executing SQL script "%s":\n%s' % (filename, err))
            self.conn.rollback()

    ## Inserts one or more rows into a table in the database.
    #  @param self
    #  @param table (string) name of the table to insert into
    #  @param cols (string) column names of this table (can omit autogenerated/defaulted cols)
    #  @param rows (list) a list of lists, (one sublist for each row) containing the data values to insert. These must all be the same length
    #  @returns (list) list of all the primary key values of the inserted rows
    def insert(self, table, cols, rows):
        last_ids = []
        if table and len(rows) > 0:
            num_cols = len(cols)
            num_rows = len(rows)

            sql = 'INSERT INTO %s (%s) VALUES (%s);' % (table, ','.join(cols), '?,' * (num_cols - 1) + '?');

            try:
                #SQLite does not support inserting multiple values in a single INSERT statement, so we have to loop...
                for i in range(num_rows):
                    self.cursor.execute(sql, rows[i])
                    last_ids.append(int(self.cursor.lastrowid))

                #only commit after all rows have been successfully inserted
                self.conn.commit()
                    
            except Exception as error:
                logging.error('Database error on insert()')
                logging.error('Statement: %s' % (sql))
                logging.error("Stack trace: %s" % (traceback.format_exc()))
                self.conn.rollback()

        return last_ids

    ## Selects rows from a table in the database.
    #  @param table (string) name of the table to select from (can be multiple joined tables - eg. 'table1 join table2 on x=y')
    #  @param cols (list) list of column names (string) to select
    #  @param where_cond (string=None) a boolean condition like ('x=y'). Will generate 'WHERE x=y'. Set to None if no where condition should be generated. Note: Can use '?' as a placeholder for raw data values, then pass the raw values in using the 'params' parameter. Eg. passing 'x=?' for where_cond and [2] for params generates 'WHERE x=2'. Advantage here is that the DB ensures the raw values are properly escaped/quoted.
    #  @param params (list=[]) list of values to stick in '?' placeholders passed in via the where_cond parameter (or any other parameter). These values are automatically quoted/escaped by the SQLite API.
    #  @param order_by (string=None) a column name, or multiple comma-separated column names, to order by. Eg. passing in 'time, id' generates 'ORDER BY time, id'. Pass None if no order by clause is needed.
    #  @param dump_sql (boolean=False) Set to True if you wish to print the generated statement (before '?' substitution - unfortunately sqlite api restrictions make it difficult to access the final sustituted verison...) to standard output.
    #  @param group_by (string) This string is inserted into to SQL statement after the where clause. It can be a single column name, or multiple names separated with commas (Eg. 'child_id', or 'child_id, awc').
    #  @returns (list) list of lists, one sub-list per row. Each sublist contains data in the order specified by cols.
    def select(self, table, cols, where_cond=None, params=[], order_by=None, dump_sql=False, group_by=None):
        sql = 'SELECT %s FROM %s' % (','.join(cols), table)
        if where_cond:
            sql += ' WHERE %s' % (where_cond)

        if group_by:
            sql += ' GROUP BY %s' % (group_by)
            
        if order_by:
            sql += ' ORDER BY %s' % (order_by)
            
        sql += ';'

        if dump_sql:
            logging.debug(sql)

        try:
            self.cursor.execute(sql, params)
            
        except Exception as error:
            logging.error('Database error on select()')
            logging.error('Query: %s' % (sql))
            logging.error("Stack trace: %s" % (traceback.format_exc()))

        return self.cursor.fetchall()

    ## Deletes rows from a table in the database.
    #  @param self
    #  @param table (string) name of the table to delete from
    #  @param where_cond (string=None) a boolean condition like ('x=y'). Will generate 'WHERE x=y'. Set to None if no where condition should be generated (deletes all rows in table). Note: Can use '?' as a placeholder for raw data values, then pass the raw values in using the 'params' parameter. Eg. passing 'x=?' for where_cond and [2] for params generates 'WHERE x=2'. Advantage here is that the DB ensures the raw values are properly escaped/quoted.
    #  @param params (list=[]) list of values to stick in '?' placeholders passed in via the where_cond parameter (or any other parameter). These values are automatically quoted/escaped by the SQLite API.
    #  @returns (int) the number of rows deleted.
    def delete(self, table, where_cond=None, params=[]):
        sql = 'DELETE FROM %s' % (table)
        if where_cond:
            sql += ' WHERE %s' % (where_cond)

        sql += ';'

        rowcount = 0
        try:
            self.cursor.execute(sql, params)
            rowcount = self.cursor.rowcount
            self.conn.commit()
            
        except Exception as error:
            logging.error('Database error on delete()')
            logging.error('Statement: %s' % (sql))
            logging.error("Stack trace: %s" % (traceback.format_exc()))
            self.conn.rollback()

        return rowcount

    ## Updates the value of a timestamp column to the current date/time.
    #  @param self
    #  @param table (string) name of table to update
    #  @param col (string) name of timestamp column
    #  @param where_cond (string=None) a boolean condition like ('x=y'). Will generate 'WHERE x=y'. Set to None if no where condition should be generated. Note: Can use '?' as a placeholder for raw data values, then pass the raw values in using the 'params' parameter. Eg. passing 'x=?' for where_cond and [2] for params generates 'WHERE x=2'. Advantage here is that the DB ensures the raw values are properly escaped/quoted.
    #  @param params (list=[]) list of values to stick in '?' placeholders passed in via the where_cond parameter (or any other parameter). These values are automatically quoted/escaped by the SQLite API.
    #  @returns (int) number of rows updated
    def update_timestamp_col(self, table, col, where_cond=None, params=[]):
        sql = 'UPDATE %s SET %s=CURRENT_TIMESTAMP' % (table, col)
        if where_cond:
            sql += ' WHERE %s' % (where_cond)

        sql += ';'
        rowcount = 0

        try:
            self.cursor.execute(sql, params)
            rowcount = self.cursor.rowcount
            self.conn.commit()

        except Exception as error:
             logging.error('Database error on update_timestamp_col()')
             logging.error('Statement: %s' % (sql))
             logging.error("Stack trace: %s" % (traceback.format_exc()))
             self.conn.rollback()

        return rowcount

    ## Updates rows in a table.
    #  @param table (string) name of table to update
    #  @param cols (list) list of names of columns (strings) to update
    #  @param where_cond (string=None) a boolean condition like ('x=y'). Will generate 'WHERE x=y'. Set to None if no where condition should be generated. Note: Can use '?' as a placeholder for raw data values, then pass the raw values in using the 'params' parameter. Eg. passing 'x=?' for where_cond and [2] for params generates 'WHERE x=2'. Advantage here is that the DB ensures the raw values are properly escaped/quoted.
    #  @param params (list=[]) list of values to stick in '?' placeholders generated for each column we are updating. The last param is in this list is used for the where_cond parameter (if any). These values are automatically quoted/escaped by the SQLite API.
    #  @param dump_sql (boolean=False) Set to True if you wish to print the generated statement (before '?' substitution - unfortunately sqlite api restrictions make it difficult to access the final sustituted verison...) to standard output.
    #  @returns (int) number of rows updated
    def update(self, table, cols, where_cond=None, params=[], dump_sql=False):
        rowcount = 0
        sql = 'UPDATE %s SET ' % (table)
        
        for i in range(len(cols)):
            sql += '%s=?' % cols[i]
            if i < len(cols) - 1:
                sql += ','

        if where_cond:
            sql += ' WHERE %s' % (where_cond)

        sql += ';'

        if dump_sql:
            logging.debug(sql)

        try:
            self.cursor.execute(sql, params)
            rowcount = self.cursor.rowcount
            self.conn.commit()
            
        except Exception as error:
            logging.error('Database error on update()')
            logging.error('Statement: %s' % (sql))
            logging.error("Stack trace: %s" % (traceback.format_exc()))
            self.conn.rollback()

        return rowcount

    ## Writes out all of the data in a table to a csv file.
    #  @param self
    #  @param path (string) The location in which you'd like to save the csv file. (Eg. 'C:/Wayne/data.csv')
    #  @param table (string) Name of the database table to read data from.
    def write_to_file(self, path, table):
        file_out = open(path, 'wb')
        writer = csv.writer(file_out)

        self.cursor.execute('PRAGMA table_info(%s)' % (table)) #This SQLite pragma selects the column names from the table
        rows = self.cursor.fetchall()

        #throw away everything except the column names
        col_names = map(lambda cur_row: cur_row[1], rows)

        #write the column names in the csv file
        writer.writerow(col_names)

        #write the table rows to the csv file
        rows = self.select(table, col_names, order_by='id') #select *
        for cur_row in rows:
            writer.writerow(cur_row)
        
        file_out.close()
