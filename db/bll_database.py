## package db.bll_database

import sqlite3
import os
import datetime
import re
import logging
import traceback

from db.database import Database
from data_structs.combo_option import ComboOption
from data_structs.codes import CodeInfo, Code, TranscriberCode124, TranscriberCode3
from utils.enum import Enum
from collections import OrderedDict

## Provides BLL-app-specific data retreival and storage routines, building on the base database class.
# Constants needed for segment and utterance parsing/manipulation (lena speaker codes, transcriber codes, etc.), application-wide settings (info needed to launch Praat and Excel), common UI combobox options, and any associated information are retreived from database tables and put into Enums by routines in this class.
# The DBConstants class (see bottom of file) is populated using these methods. DBConstants' public attributes (Enums) can then be used anywhere in the application code.
class BLLDatabase(Database):
    DB_LOCATION = 'db/bll_db.db'
    CREATE_TABLES_SCRIPT = 'db/sql/init/create_tables.sql' #this script creates the DB if it doesn't exist
    INSERT_DATA_SCRIPT = 'db/sql/init/insert_data.sql' #inserts 'constant' data upon DB creation (speaker_codes, transcriber_codes, etc.)
    UPDATE_SCRIPT_DIR = 'db/sql/updates/' #must include trailing '/'
    NUM_TRANS_CODES = 4

    ## Constructor
    #  @param self
    def __init__(self):
        #check if the DB is present
        tables_exist = os.path.exists(BLLDatabase.DB_LOCATION)

        #this will create the database file if it doesn't exist
        super(BLLDatabase, self).__init__(BLLDatabase.DB_LOCATION)
        
        #create the tables and insert the initial data if the DB was just generated
        if not tables_exist:
            logging.info('No database found - creating one...')
            self.execute_script(BLLDatabase.CREATE_TABLES_SCRIPT)
            self.execute_script(BLLDatabase.INSERT_DATA_SCRIPT)

        #apply any previously unapplied update scripts in UPDATE_SCRIPT_DIR
        self.apply_update_scripts()

    ## Runs any sql scripts in UPDATE_SCRIPT_DIR that haven't been run yet.
    #  In order to do this, scripts must follow a naming convention: "update-x.sql", where x is an integer.
    #  The files in UPDATE_SCRIPT_DIR are sorted by this integer before being applied.
    #  If previous update scripts have been applied, the last script number is recorded in the settings table.
    #  Only scripts with numbers greater than this number are applied when this method is called.
    #  @param self
    def apply_update_scripts(self):
        settings = self._get_settings_enum() #this is not defined in DBConstants.SETTINGS at the time this method is called...it's an enum of everything in the settings table (attribute names from 'code_name' col, values from 'val' col)

        #grab the filenames of all the scripts in the directory and insert them into a dictionary, keyed by script number
        filenames = {}
        for name in os.listdir(BLLDatabase.UPDATE_SCRIPT_DIR):
            #filter out any files that don't match the naming convention
            match = re.match('^update-(\d+)\.sql$', name)
            if match:
                script_num = int(match.groups()[0])
                
                #filter out scripts that have already been executed
                if script_num > int(settings.LAST_UPDATE_SCRIPT_NUM):
                    filenames[script_num] = name

        #sort by script num and execute
        try:
            nums = filenames.keys()
            if nums:
                nums.sort()
                for key in nums:
                    logging.info("Executing script: '%s'" % (filenames[key]))
                    sql_file = open('%s%s' % (BLLDatabase.UPDATE_SCRIPT_DIR, filenames[key]), 'r')
                    sql = sql_file.read()
                    sql_file.close()
                    self.cursor.executescript(sql)

                #update the last script number in the settings table
                new_update_num = nums[-1]
                self.cursor.execute('UPDATE settings SET val=? WHERE code_name=?', [new_update_num, 'LAST_UPDATE_SCRIPT_NUM'])
                DBConstants.SETTINGS = self.select_enum('settings')
                self.conn.commit()

        #rollback on error
        except sqlite3.OperationalError as err:
            logging.error('Error executing update script:\n%s' % (err))
            self.conn.rollback()  

    ## Builds an Enum of recognized speaker types from the speaker_types table.
    # These are derrived from transcriber code 1's possible options (see transcriber manual) like 'MALE_ADULT', 'FEMALE_ADULT', 'OTHER_CHILD', etc.
    #  @param self
    #  @returns (Enum) attributes are from code_name column, values from id column
    def _get_speaker_types_enum(self):
        rows = self.select('speaker_types', 'id code_name'.split())
        ids, code_names = zip(*rows)

        return Enum(code_names, ids)

    ## Builds an enum of possible speaker 'distances' (eg. FAN speaker has distance of 'near', FAF speaker has distance of 'far', 'SIL' speaker has distance of 'not applicable').
    #  @param self
    #  @param returns (Enum) attributes are 'NA, NEAR, FAR', values are 0, 1, 2 (respectively)
    def _get_speaker_distances_enum(self):
        #Note: for now, it doesn't really pay to have a table for this - just don't change the ordering in the enum...the items' values should map directly to the id used the database
        return Enum(['NA', 'NEAR', 'FAR'])

    ## Builds an Enum of possible speaker 'properties' (Eg. speakers can be overlapping, be non-verbal noise, or be tv/radio sound)
    #  @param self
    #  @returns (Enum) attributes are 'MEDIA', 'OVERLAPPING', 'NON_VERBAL_NOISE', values are 0, 1, 2, (respectively)
    def _get_speaker_props_enum(self):
        #Note: for now, it doesn't really pay to have a table for this - just don't change the ordering in the enum...
        return Enum(['MEDIA', 'OVERLAPPING', 'NON_VERBAL_NOISE'])

    ## Builds an Enum of all possible combo groups. Each combo group corresponds to a single dropdown box in the UI, and maps to one or more combo options. The Enum is built from the combo_groups table.
    #  @param self
    #  @returns (Enum) attributes are from the 'code_name' column, values are from the 'id' column
    def _get_combo_groups_enum(self):
        rows = self.select('combo_groups', 'id code_name'.split())
        ids, code_names = zip(*rows)
        
        return Enum(code_names, ids)

    ## Builds an Enum of common regular expressions from the common_regex DB table.
    # @param self
    # @returns (Enum) attributes are from the 'code_name' column, values are from the 'id' column
    def _get_common_regexs_enum(self):
        rows = self.select('common_regexs', 'code_name regex'.split())
        code_names, regexs = zip(*rows)

        return Enum(code_names, regexs)

    ## Builds a dictionary (of Enums - one for each combo group), containing all prossible combo box options that the UI can use.
    # @param self
    # @returns (dictionary) a dictionary of Enums. The dictionary contains a key for each id from the combo_groups table. Each entry contains an Enum of all possible combo options for that group (Retreived from the combo_options table. Enum attributes are from the 'code_name' column, values are from the 'id' column).
    def _get_combo_options_enum(self):
        options = {}
        groups = self._get_combo_groups_enum()
        for i in range(len(groups)):
            rows = self.select('combo_options', 'id code_name'.split(), 'combo_group_id=?', [groups[i]], 'id ASC')
            ids, code_names = zip(*rows)
            options[groups[i]] = Enum(code_names, ids)

        return options

    ## Builds an Enum of the application settings from the settings table.
    # @param self
    # @returns (Enum) Enum attributes are from the 'code_name' column, values are from the 'id' column).
    def _get_settings_enum(self):
        settings = None
        rows = self.select('settings', 'code_name val'.split())
        (names, vals) = zip(*rows)
        settings = Enum(names, vals)
        
        return settings

    ## This method creates Code objects containing all the options for a particular type of code (transcriber, lena_notes, speaker).
    # @param self
    #  @param table (string) name of the table to select from.
    #  @returns (Code/list of Code) a Code object (or list of Code objects, if selecting transcriber codes) that contains code options and properties from the DB table
    def select_codes(self, table):
        return {'transcriber_codes': self._select_transcriber_codes,
                  'lena_notes_codes': self._select_lena_notes_codes,
                  'speaker_codes': self._select_speaker_codes,
                  }[table]()

    ## Builds an Enum based upon a selection from a particular property or table.
    #  @param self
    #  @param table (string) name of the table to select from
    #  @returns (Enum) an Enum with attributes for all of the options within the table (attributes are from the code_name column, values from the id column).
    def select_enum(self, table):
        return {'speaker_types': self._get_speaker_types_enum,
                'speaker_distances': self._get_speaker_distances_enum, #this is not an actual DB table...
                'speaker_props': self._get_speaker_props_enum, #this is not an actual DB table...
                'combo_groups': self._get_combo_groups_enum,
                'combo_options': self._get_combo_options_enum,
                'common_regexs': self._get_common_regexs_enum,
                'settings': self._get_settings_enum,
                  }[table]()

    ## Builds a list of Code objects for transcriber codes. The Code objects contain information from the transcriber_codes database table.
    #  @param self
    #  @returns (list) list of Code objects, one for each transcriber code.
    def _select_transcriber_codes(self):
        #select the data
        rows = self.select('transcriber_codes', 'id code trans_index display_desc speaker_type_id'.split())
        distances = self.select_enum('speaker_distances')

        #construct CodeInfo objects for each option within each of the transcriber codes
        options_dicts = []
        for i in range(BLLDatabase.NUM_TRANS_CODES):
            options_dicts.append(OrderedDict())
        
        for cur_row in rows:
            code_info = CodeInfo(
                cur_row[0], #db_id
                cur_row[1], #code
                cur_row[3], #desc
                False, #is_linkable
                distances.NA, #distance
                cur_row[4], #speaker_type
                )
            cur_dict = options_dicts[cur_row[2] - 1]
            cur_dict[cur_row[1]] = code_info

        #create the Code objects, using the newly created CodeInfo objects
        codes = []
        for i in range(BLLDatabase.NUM_TRANS_CODES):
            new_code = None
            #transcriber code 3 can have multiple characters, so there's a special subclass for it...
            if i in (0, 1, 3,):
                new_code = TranscriberCode124(options_dicts[i])
            elif i == 2: #2 because of 0-indexed array
                new_code = TranscriberCode3(options_dicts[i])
                
            codes.append(new_code)
        
        return codes

    ## Creates a Code object containing information about options from the lena_notes_codes table. ('LENA notes codes' look like 'VOC', 'SIL', etc.)
    #  @param self
    #  @returns (Code) Code object that can be used to access info about different lena notes code options.
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

    ## Creates a Code object containing information about options from the speaker_codes table. (LENA speaker codes like 'MAN', 'FAN', etc.)
    #  @param self
    #  returns (Code) a Code object that can be used to access info about different speaker code options.
    def _select_speaker_codes(self):
        #select the data
        rows = self.select('speaker_codes', 'id code speaker_type_id display_desc distance is_linkable is_media is_nonverbal_noise is_overlapping'.split())
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

## This class does an initial SQL select on database 'lookup tables' (tables containing information that is frequently used, but never updated while the program is running), and provides acess to this information in the form of a number of static data structures.
# This way, the lookup table info is only retreived from the database once at the start of the application. In addition, code that needs this data can retrieve it without worrying about building SQL statements and executing them.
# See the code for an in-comment description of each data structure.
class DBConstants(object):
    #this is the format that SQLite stores timestamps in. See Python documentation on Time.strftime() for placeholder definitions
    DB_DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

    #list of Code objects, one for each transcriber code
    TRANS_CODES = None
    #Code object for lena codes (like 'VOC', 'SIL')
    LENA_NOTES_CODES = None
    #Code object for lena speakers codes (like 'MAN', 'FAN')
    SPEAKER_CODES = None

    #Enum of speaker types (as defined in the transcriber manual for code 1) like 'MALE_ADULT', 'FEMALE_ADULT', 'OTHER_CHILD', etc.
    SPEAKER_TYPES = None
    #Enum of speaker distances (like 'NEAR', 'FAR', 'NA')
    SPEAKER_DISTANCES = None
    #Enum of speaker properties (like 'MEDIA', 'OVERLAPPING', 'NON_VERBAL_NOISE')
    SPEAKER_PROPS = None

    #Enum of all (code_name, val) pairs from the settings table (stuff like path to MS Excel, etc.)
    SETTINGS = None
    #Enum of common regular expressions from the common_regexs table
    COMMON_REGEXS = None

    #an Enum of all options in the combo_groups table
    COMBO_GROUPS = None
    #this is a dictionary. keys are group_ids from the COMBO_GROUPS enum above, and values are enums (enum properties are code_name column values from the combo_options table in the DB)
    COMBO_OPTIONS = None
    #this is a dictionary - keys are elements of the enum COMBO_GROUPS, values are sub-dictionaries. Sub-dictionary keys are values of the enum COMBO_OPTIONS[group_id], values are ComboOption objects.
    COMBOS = None
    
    #In other words, to access the option objects for the combo group with code_name LENA_CATEGORIES, you would do the following:
    #lena_options_dict = COMBOS[COMBO_GROUPS.LENA_CATEGORIES]
    #lena_options_dict_keys_enum = COMBO_OPTIONS[COMBO_GROUPS.LENA_CATEGORIES]
    #for i in range(len(lena_options_dict_keys_enum)):
    #    group_option_key = lena_options_dict_keys_enum[i]
    #    option_obj = COMBOS[COMBO_GROUPS.LENA_CATEGORIES][group_option_key]

## This function constructs the data structure used to initialize the DBConstants.COMBOS constant.
# This is a dictionary - keys are elements of the enum COMBO_GROUPS, values are sub-dictionaries. Sub-dictionary keys are values of the enum COMBO_OPTIONS[group_id], values are ComboOption objects.
# @param db (BLLDatabase) database handle object
# @returns (dictionary) a dictionary, as described above
def _get_combos(db):
    groups = db.select_enum('combo_groups')
    rows = db.select('combo_options', 'id code_name combo_group_id disp_desc hidden'.split(), None, [], 'id ASC')
    options = {}

    for cur_row in rows:
        group_id = cur_row[2]
        opt_id = cur_row[0]
        if not group_id in options:
            options[group_id] = {}

        options[group_id][opt_id] = ComboOption(*cur_row)

    return options

## Populates the constants in the DBConstants class.
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

#Note: this is only executed once, the first time the Python interpreter encounters the file
_get_constants()
