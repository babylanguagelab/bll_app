import sqlite3
import sys
import logging as lg

class Database:
    def __init__(self, db_filename):
        try:

            self.conn = sqlite3.connect(db_filename)
            self.cursor = self.conn.cursor()

            # turn on foreign keys - they're disabled by default in sqlite
            self.conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            lg.error(e.args[0] + db_filename)
            sys.exit(1)

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()

    # Reads and executes a sql script file.
    def execute_script(self, sql_string):
        # lg.debug(sql_string)
        try:
            self.cursor.executescript(sql_string)
            self.conn.commit()
            result = self.cursor.fetchall()
            if len(result) == 0:
                return None;

            return result

        # rollback on error
        except sqlite3.Error as e:
            lg.error(e.args[0])
            self.conn.rollback()
            return None

    # insert one row(tuple) into a table
    def insert(self, table, cols, lvalues):
        sql = "INSERT INTO " + table + \
              ' (' + ','.join(cols) + ') ' + \
              "VALUES(" + (len(cols) - 1) * '?,' + '?)'

        # lg.debug(sql + str(lvalues))
        try:
            self.cursor.execute(sql, lvalues)
            self.conn.commit()
        except sqlite3.Error as e:
            lg.error(e.args[0])
            self.conn.rollback()

    # insert one 2-d array into a table
    def insert_table(self, table, cols, tvalues):
        sql = "INSERT INTO " + table + \
              ' (' + ','.join(cols) + ') ' + \
              "VALUES(" + (len(cols) - 1)*'?,' + '?)'

        # lg.debug(sql + str(tvalues))
        try:
            self.cursor.executemany(sql, tvalues)
            self.conn.commit()
        except sqlite3.Error as e:
            lg.error(e.args[0])
            self.conn.rollback()


    # select rows from a table
    # cols must be a list
    def select(self, table, cols, distinct=False, where=None, group_by=None, order_by=None):
        if distinct:
            sql = 'SELECT DISTINCT %s FROM %s' % (','.join(cols), table)
        else:
            sql = 'SELECT %s FROM %s' % (','.join(cols), table)

        if where:
            sql += " WHERE %s" % (where)

        if group_by:
            sql += " GROUP BY %s" % (group_by)

        if order_by:
            sql += " ORDER BY %s" % (order_by)

        sql += ';'

        # lg.debug(sql)

        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            if len(result) == 0:
                return None;

            return result
        except sqlite3.Error as e:
            lg.error(e.args[0])
            return None

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
            lg.error(e.args[0])
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
            lg.error(e.args[0])
            self.conn.rollback()
