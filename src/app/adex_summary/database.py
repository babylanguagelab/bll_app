import sqlite3
import logging as lg

class Database(object):
    def __init__(self, db_filename):
        try:

            self.conn = sqlite3.connect(db_filename)
            self.cursor = self.conn.cursor()

            # turn on foreign keys - they're disabled by default in sqlite
            self.conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            logging.error("Error " + e.args[0])
            sys.exit(1)

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close() 

    # Reads and executes a sql script file.
    def execute_script(self, filename):
        try:
            sql_file = open(filename, 'r')
            sql = sql_file.read()
            sql_file.close()
            self.cursor.executescript(sql)
            self.conn.commit()

        # rollback on error
        except Exception:
            self.conn.rollback()

    # insert one row(tuple) into a table
    def insert(self, table, cols, lvalues):
        sql = "INSERT INTO " + table + \
              ' (' + ','.join(cols) + ') ' + \
              "VALUES(" + (len(lvalues) - 1) * '?,' + '?)'

        lg.debug(sql + str(lvalues))
        try:
            self.cursor.execute(sql, lvalues)
            self.conn.commit()

        except sqlite3.Error as e:
            lg.error("Error " + e.args[0])
            self.conn.rollback()

    # select rows from a table
    def select(self, table, cols, where=None, group_by=None, order_by=None):
        sql = 'SELECT %s FROM %s' % (','.join(cols), table)
        if where:
            sql += ' WHERE %s' % (where)

        if group_by:
            sql += ' GROUP BY %s' % (group_by)

        if order_by:
            sql += ' ORDER BY %s' % (order_by)

        sql += ';'

        lg.debug(sql)
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    # deletes rows from a table
    def delete(self, table, where=None):
        sql = 'DELETE FROM %s' % (table)
        if where:
            sql += ' WHERE %s' % (where)

        sql += ';'

        try:
            self.cursor.execute(sql)
            self.conn.commit()

        except sqlite3.Error as e:
            logging.error("Error " + e.args[0])
            self.conn.rollback()

    # Updates rows in a table.
    def update(self, table, cols, lvalues, where=None):
        sql = 'UPDATE %s SET ' % (table)
        sql += (',').join(tuple([x+'=?' for x in cols]))

        if where:
            sql += ' WHERE %s' % (where)

        sql += ';'

        try:
            self.cursor.execute(sql, lvalues)
            self.conn.commit()

        except sqlite3.Error as e:
            logging.error("Error " + e.args[0])
            self.conn.rollback()
