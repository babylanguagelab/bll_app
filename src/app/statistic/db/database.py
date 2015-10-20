import sqlite3
import csv


class Database(object):
    def __init__(self, db_filename):

        self.conn = sqlite3.connect(db_filename)

        # grab a cursor object that can be used to execute statements
        self.cursor = self.conn.cursor()

        # turn on foreign keys - they're disabled by default in sqlite
        self.conn.execute("PRAGMA foreign_keys = ON")

    # Closes the database connection
    def close(self):
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

    # Inserts one or more rows into a table in the database.
    def insert(self, table, cols, rows):
        last_ids = []
        if table and len(rows) > 0:
            num_cols = len(cols)
            num_rows = len(rows)

            sql = 'INSERT INTO %s (%s) VALUES (%s);' % (table, ','.join(cols), '?,' * (num_cols - 1) + '?');

            try:
                for i in range(num_rows):
                    self.cursor.execute(sql, rows[i])
                    last_ids.append(int(self.cursor.lastrowid))

                # only commit after all rows have been successfully inserted
                self.conn.commit()

            except Exception:
                self.conn.rollback()

        return last_ids

    def select(self, table, cols, where_cond=None, params=[], order_by=None,
               dump_sql=False, group_by=None):
        sql = 'SELECT %s FROM %s' % (','.join(cols), table)
        if where_cond:
            sql += ' WHERE %s' % (where_cond)

        if group_by:
            sql += ' GROUP BY %s' % (group_by)

        if order_by:
            sql += ' ORDER BY %s' % (order_by)

        sql += ';'

        self.cursor.execute(sql, params)

        return self.cursor.fetchall()

    # Deletes rows from a table in the database.
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

        except Exception:
            self.conn.rollback()

        return rowcount

    # Updates the value of a timestamp column to the current date/time.
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

        except Exception:
            self.conn.rollback()

        return rowcount

    # Updates rows in a table.
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

        try:
            self.cursor.execute(sql, params)
            rowcount = self.cursor.rowcount
            self.conn.commit()

        except Exception:
            self.conn.rollback()

        return rowcount

    # Writes out all of the data in a table to a csv file.
    def write_to_file(self, path, table):
        file_out = open(path, 'wb')
        writer = csv.writer(file_out)

        # This SQLite pragma selects the column names from the table
        self.cursor.execute('PRAGMA table_info(%s)' % (table))
        rows = self.cursor.fetchall()

        # throw away everything except the column names
        col_names = map(lambda cur_row: cur_row[1], rows)

        # write the column names in the csv file
        writer.writerow(col_names)

        # write the table rows to the csv file
        rows = self.select(table, col_names, order_by='id')
        for cur_row in rows:
            writer.writerow(cur_row)

        file_out.close()
