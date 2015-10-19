import os
import logging
from collections import OrderedDict

from codes import Code, CodeInfo
from database import Database
from enum import Enum

# common database for general purpose
DB_LOCATION = 'bll.db'

# inserts 'constant' data upon DB creation
# speaker_codes, transcriber_codes, etc.
SQL_INIT_SCRIPT = 'init.sql'

# number of codes in transcriber manual
NUM_TRANS_CODES = 4


class BLLDatabase(Database):
    def __init__(self):
        tables_exist = os.path.exists(DB_LOCATION)

        # this will create the database file if it doesn't exists
        super(BLLDatabase, self).__init__(DB_LOCATION)

        if not tables_exist:
            logging.info('No database found - creating one...')
            self.execute_script(SQL_INIT_SCRIPT)

        self.TRANS_CODES = self.select_transcriber_codes()
        self.LENA_NOTES_CODES = self.select_lena_notes_codes()

        self.SPEAKER_CODES = self.select_speaker_codes()
        self.SPEAKER_TYPES = self.get_speaker_types_enum()
        self.SPEAKER_DISTANCES = self.get_speaker_distances_enum()
        self.SPEAKER_PROPS = self.get_speaker_props_enum()

    def get_speaker_types_enum(self):
        rows = self.select('speaker_types', ['id', 'code_name'])
        ids, code_names = zip(*rows)

        return Enum(code_names, ids)

    def get_speaker_distances_enum(self):
        return Enum(['NA', 'NEAR', 'FAR'])

    def get_speaker_props_enum(self):
        return Enum(['MEDIA', 'OVERLAPPING', 'NON_VERBAL_NOISE'])

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

            # position for transcriber code eg. 1, 2, 3, 4
            cur_dict = options_dicts[cur_row[2] - 1]
            # hash: code -> code_info
            cur_dict[cur_row[1]] = code_info

        # create the Code objects, using the newly created CodeInfo objects
        codes = []
        for i in range(NUM_TRANS_CODES):
            new_code = Code(options_dicts[i])
            codes.append(new_code)

        return codes

    def select_lena_notes_codes(self):
        rows = self.select('lena_notes_codes',
                           ['id', 'code', 'speaker_type_id', 'display_desc'])
        distances = self.get_speaker_distances_enum()

        # create a dictionary of CodeInfo objects (one for each option)
        codes = {}
        for cur_row in rows:
            code_info = CodeInfo(
                cur_row[0],  # db_id,
                cur_row[1],  # code
                cur_row[3],  # desc
                cur_row[1] == 'VOC' or cur_row[1] == 'FAN',  # is_linkable
                distances.NA,  # distance
                cur_row[2],    # speaker_type
                )
            codes[cur_row[1]] = code_info

        return Code(codes)

    def select_speaker_codes(self):
        # select the data
        rows = self.select('speaker_codes',
                           ['id',
                            'code',
                            'speaker_type_id',
                            'display_desc',
                            'distance',
                            'is_linkable',
                            'is_media',
                            'is_nonverbal_noise',
                            'is_overlapping'])

        props_enum = self.get_speaker_props_enum()

        # build a dictionary of CodeInfo objects, one for each option
        codes = {}
        for cur_row in rows:
            # append any special properties recorded in the table
            props = []
            if cur_row[6]:
                props.append(props_enum.MEDIA)
            if cur_row[7]:
                props.append(props_enum.NON_VERBAL_NOISE)
            if cur_row[8]:
                props.append(props_enum.OVERLAPPING)

            code_info = CodeInfo(
                cur_row[0],  # db_id
                cur_row[1],  # code
                cur_row[2],  # speaker_type
                cur_row[3],  # desc
                cur_row[4],  # distance
                cur_row[5],  # is_linkable
                props,  # properties
                )
            codes[cur_row[1]] = code_info

        return Code(codes)
