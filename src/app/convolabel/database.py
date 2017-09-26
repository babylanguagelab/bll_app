import sqlite3 as sql
import cPickle
import os
import utils

class Database(object):

    def __init__(self, program_path):
        self.coder = None
        self.db = {}

        self.conn = None
        self.c = None

        self.program_path = program_path
        self.audio_path = os.path.join(self.program_path, 'output')
        self.db_path = os.path.join(self.program_path, 'labelled_data')

    def set_coder(self, name):
        self.coder = name

    @property
    def pkl_file(self):
        return os.path.join(self.db_path, self.coder + '.pkl')


    def submit_labels(self, rec, block, part, labels_dic):
        if not self.has_key(rec):
            self.db[rec] = {}
        if not self.has_key(rec, block):
            self.db[rec][block] = {}

        self.db[rec][block][part] = labels_dic
        self.insert_block(rec, block, part, labels_dic) # sql



    def has_key(self, rec, block = None, part = None):
        try:
            if part:
                return part in self.db[rec][block].keys()
            elif block:
                return block in self.db[rec].keys()
            else:
                return rec in self.db.keys()
        except KeyError:
            return False

    def total_labelled(self, rec):
        try:
            labelled = len(self.db[rec])
            if '_ads_sample' in self.db[rec].keys():
                labelled -= 1
            if '_cds_sample' in self.db[rec].keys():
                labelled -= 1
            return labelled
        except KeyError:
            return 0


    def save_data(self):
        with open(self.pkl_file, 'wb') as f:
            cPickle.dump(self.db, f, cPickle.HIGHEST_PROTOCOL)

    def load_data(self):
        with open(self.pkl_file, 'rb') as f:
            self.db = cPickle.load(f)

################# SQL backups ##################################


    @ property
    def sql_file(self):
        return os.path.join(self.db_path, self.coder + '.db')

    def connect_sql(self):
        self.conn = sql.connect(self.sql_file)
        self.c = self.conn.cursor()

    def create_table(self):
        self.c.execute("""CREATE TABLE IF NOT EXISTS {} (
            time            TEXT,
            rec             TEXT,
            block           TEXT,
            part            TEXT,
            length          TEXT,
            junk            INT,
            sensitive       INT,
            other_langue    INT,
            ads             INT,
            cds             INT,
            ocs             INT,
            mother          INT,
            other_fem       INT,
            male            INT,
            unsure          INT,
            target_child    INT,
            other_child     INT,
            directive        INT,
            nondirective    INT,
            comments        TEXT
            )""".format(self.coder))

    def insert_block(self, rec, block, part, labels_dic):

        labels_dic['rec'] = rec
        labels_dic['block'] = block
        labels_dic['part'] = part

        with self.conn:
            self.c.execute("INSERT INTO {} VALUES (:time, :rec, :block, :part, :length, :junk, :sensitive, :other_langue, :ads, :cds, :ocs, :mother, :other_fem, :male, :unsure, :target_child, :other_child, :directive, :nondirective, :comments)".format(self.coder), labels_dic)

    def close_sql(self):
        if self.conn:
            self.conn.close()




