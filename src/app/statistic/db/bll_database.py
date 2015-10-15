#!/usr/bin/python2
import os
import re
import logging
from collections import OrderedDict
from database import Database
from enum import Enum

# common database for general purpose
DB_LOCATION = 'bll.db'

# inserts 'constant' data upon DB creation
# speaker_codes, transcriber_codes, etc.
SQL_INIT_SCRIPT = 'init.sql'

NUM_TRANS_CODES = 4


class BLLDatabase(Database):
    def __init__(self):
        tables_exist = os.path.exists(DB_LOCATION)

        # this will create the database file if it doesn't exists
        super(BLLDatabase, self).__init__(DB_LOCATION)

        if not tables_exist:
            logging.info('No database found - creating one...')
            self.execute_script(SQL_INIT_SCRIPT)

    def get_speaker_types_enum(self):
        rows = self.select('speaker_types', 'id code_name'.split())
        ids, code_names = zip(*rows)

        return Enum(code_names, ids)

    def get_speaker_distances_enum(self):
        return Enum(['NA', 'NEAR', 'FAR'])

    def get_speaker_props_enum(self):
        return Enum(['MEDIA', 'OVERLAPPING', 'NON_VERBAL_NOISE'])

    def _get_combo_groups_enum(self):
        rows = self.select('combo_groups', 'id code_name'.split())
        ids, code_names = zip(*rows)
        return Enum(code_names, ids)

    def _get_common_regexs_enum(self):
        rows = self.select('common_regexs', 'code_name regex'.split())
        code_names, regexs = zip(*rows)

        return Enum(code_names, regexs)

    def _get_combo_options_enum(self):
        options = {}
        groups = self._get_combo_groups_enum()
        for i in range(len(groups)):
            rows = self.select('combo_options', 'id code_name'.split(), 'combo_group_id=?', [groups[i]], 'id ASC')
            ids, code_names = zip(*rows)
            options[groups[i]] = Enum(code_names, ids)

        return options

    def _get_settings_enum(self):
        settings = None
        rows = self.select('settings', 'code_name val'.split())
        (names, vals) = zip(*rows)
        settings = Enum(names, vals)

        return settings

    def select_transcriber_codes(self):
        rows = self.select('transcriber_codes',
                           ['id',
                            'code',
                            'trans_index',
                            'display_desc',
                            'speaker_type_id'])
        distances = self.get_speaker_distances_enum()

        # construct CodeInfo objects for each option within each of the
        # transcriber codes
        options_dicts = []
        for i in range(NUM_TRANS_CODES):
            options_dicts.append(OrderedDict())

        for cur_row in rows:
            code_info = CodeInfo(
                cur_row[0],  # db_id
                cur_row[1],  # code
                cur_row[3],  # desc
                False,       # is_linkable
                distances.NA,  # distance
                cur_row[4],    # speaker_type
                )
            cur_dict = options_dicts[cur_row[2] - 1]
            cur_dict[cur_row[1]] = code_info

        # create the Code objects, using the newly created CodeInfo objects
        codes = []
        for i in range(NUM_TRANS_CODES):
            new_code = Code(options_dicts[i])
            codes.append(new_code)

        return codes

    def _select_lena_notes_codes(self):
        #select the data
        rows = self.select('lena_notes_codes', 'id code speaker_type_id display_desc'.split())
        distances = self.select_enum('speaker_distances')

        #create a dictionary of CodeInfo objects (one for each option)
        codes = {}
        for cur_row in rows:
            code_info = CodeInfo(
                cur_row[0], #db_id,
                cur_row[1], #code
                cur_row[3], #desc
                cur_row[1] == 'VOC' or cur_row[1] == 'FAN', #is_linkable
                distances.NA, #distance
                cur_row[2], #speaker_type
                )
            codes[cur_row[1]] = code_info

        return Code(codes)

    def _select_speaker_codes(self):
        # select the data
        rows = self.select('speaker_codes',
                           'id code speaker_type_id display_desc distance is_linkable is_media is_nonverbal_noise is_overlapping'.split())
        props_enum = self._get_speaker_props_enum()

        #build a dictionary of CodeInfo objects, one for each option
        codes = {}
        for cur_row in rows:
            #append any special properties recorded in the table
            props = []
            if cur_row[6]:
                props.append(props_enum.MEDIA)
            if cur_row[7]:
                props.append(props_enum.NON_VERBAL_NOISE)
            if cur_row[8]:
                props.append(props_enum.OVERLAPPING)

            code_info = CodeInfo(
                cur_row[0], #db_id
                cur_row[1], #code
                cur_row[3], # desc
                cur_row[5], #is_linkable
                cur_row[4], #distance
                cur_row[2], #speaker_type
                props, #properties
                )
            codes[cur_row[1]] = code_info

        return Code(codes)


class DBConstants(object):
    DB_DATETIME_FMT = '%Y-%m-%d %H:%M:%S'
    TRANS_CODES = None
    LENA_NOTES_CODES = None
    SPEAKER_CODES = None
    SPEAKER_TYPES = None
    SPEAKER_DISTANCES = None
    SPEAKER_PROPS = None
    SETTINGS = None
    COMMON_REGEXS = None
    COMBO_GROUPS = None
    COMBO_OPTIONS = None
    COMBOS = None


def _get_combos(db):
    groups = db.select_enum('combo_groups')
    rows = db.select('combo_options',
                     'id code_name combo_group_id disp_desc hidden'.split(),
                     None,
                     [],
                     'id ASC')
    options = {}

    for cur_row in rows:
        group_id = cur_row[2]
        opt_id = cur_row[0]
        if group_id not in options:
            options[group_id] = {}

        options[group_id][opt_id] = ComboOption(*cur_row)

    return options


def _get_constants():
    db = BLLDatabase()
    DBConstants.TRANS_CODES = db.select_codes('transcriber_codes')
    DBConstants.LENA_NOTES_CODES = db.select_codes('lena_notes_codes')
    DBConstants.SPEAKER_CODES = db.select_codes('speaker_codes')

    DBConstants.SPEAKER_TYPES = db.select_enum('speaker_types')
    DBConstants.SPEAKER_DISTANCES = db.select_enum('speaker_distances')
    DBConstants.SPEAKER_PROPS = db.select_enum('speaker_props')
    DBConstants.COMMON_REGEXS = db.select_enum('common_regexs')
    DBConstants.SETTINGS = db.select_enum('settings')

    DBConstants.COMBO_GROUPS = db.select_enum('combo_groups')
    DBConstants.COMBO_OPTIONS = db.select_enum('combo_options')
    DBConstants.COMBOS = _get_combos(db)

    db.close()

# Note: this is only executed once,
# the first time the Python interpreter encounters the file
# _get_constants()

mDB = BLLDatabase()
print mDB.get_speaker_types_enum()
