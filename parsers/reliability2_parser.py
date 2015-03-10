## @package parsers.reliability2_parser

import csv
import os
import glob
import random

from data_structs.test2 import Test2
from utils.backend_utils import BackendUtils
from db.bll_database import BLLDatabase

## This class parses information from an ADEX-exported csv file, for use in the Reliability2 program. It provides tools
# to obtain a list of the possible activity and environment categories present in the file, and to pick a given number of segments that belong to
# a specific environment-activity group.
# The csv file this class operates upon should contain the usual ADEX columns (but with one 5 minute block per row rather than one segment per row - you
# can set this up using an option in ADEX), in addition to two columns called "Activity" and "environment".
# Environment is the type of daycare in which the recording took place (eg. "home", "home daycare", or "daycare centre"). This generally stays the same for
# all 5 minute blocks in a csv file (though it need not).
# Activity is something the child is engaged in like "mealtime", "playtime - organized", "naptime", etc., and often differs every couple of blocks (depending on
# the attention span of the child :)
class Reliability2Parser(object):
    ## Constructor
    # @param self
    # @param filename (string) path to the csv file to read. 
    def __init__(self, filename):
        self.csv_file = open(filename, 'rb')
        self.reader = csv.DictReader(self.csv_file)

        #this is a list of all unique environments in the file
        self.envs = []

        #this is a list of all unique activities in the file
        self.acts = []

        #data from the csv file will be pushed into this multi-level dictionary, in the format:
        # self.parse_dict[environment][activity]
        # each element of this 2 level dictionary is another dictionary, with one of two keys: 'used' or 'unused'
        # Finally, each of the 'used' and 'unused' keys map to an array of rows from the csv file.
        # Rows in the 'used' array have already been picked for used by the user. 'unused' rows have not.
        self.parse_dict = None
        
        self.parse()

    ## This method closes the file that the parser is reading. It should always be called when you are done with a parser instance.
    # @param self
    def close(self):
       self.csv_file.close()

    ## Reads the csv file and organizes the information according to environment, activity, and used/unused. The info is placed into the
    # organized parse_dict dictionary described in the constructor.
    # @param self
    def parse(self):
        db = BLLDatabase()
        
        self.parse_dict = {}

        lines = list(self.reader)

        if lines:
            #Note: the "Elapsed_Time" column does not reset here because we are using 5 minute blocks
            start = float(lines[0]['Elapsed_Time'])
            
            acts_dict = {}
            for row in lines:
                env = row['environment'].strip()
                act = row['Activity'].strip()

                if not env in self.parse_dict:
                    self.parse_dict[env] = {}

                if not act in self.parse_dict[env]:
                    self.parse_dict[env][act] = {'used': [],
                                                 'unused': [],
                                                 }

                spreadsheet_timestamp = Reliability2Parser.get_row_timestamp(row, start)
                child_code = Reliability2Parser.get_child_code(row)
                #note: no need to check wav_file here, since that is derived from child_code
                result_set = db.select('tests2',
                          ['count(id)'],
                          'spreadsheet_timestamp=? AND child_code=?',
                          [spreadsheet_timestamp, child_code]
                          );
                if int(result_set[0][0]) > 0:
                    self.parse_dict[env][act]['used'].append(row)
                else:
                    self.parse_dict[env][act]['unused'].append(row)

                if not act in acts_dict:
                    acts_dict[act] = True

            self.acts = acts_dict.keys()
            self.envs = self.parse_dict.keys()

        db.close()

    ## Provides a list of all unique activities in the file.
    # @param self
    # @returns (list) list of strings, one for each unique activity
    def get_acts_list(self):
        return self.acts

    ## Provides a list of all unique environments in the file.
    # @param self
    # @returns (list) list of strings, one for each unique environment
    def get_envs_list(self):
        return self.envs

    ## Attempts to locate a particular wav file in a given folder hierarchy. Returns the path if it's found.
    # @param self
    # @param wav_filename (string) the name of the wav file to search for (this should not contain any path information - just the bare filename, eg. "C001a_20090708.wav")
    # @param root_dir (string) the full path to the root directory of the folder hierarchy to search for the wav file
    # @returns (string) the full path to the located wav file (including the wav filename itself), or None if the wav file could not be found in the hierarchy
    def locate_wavfile(self, wav_filename, root_dir):
        dirs = glob.glob(root_dir + '*' + os.path.sep)

        path = None

        if os.path.exists(root_dir + os.path.sep + wav_filename):
            path = root_dir + os.path.sep + wav_filename

        else:
            #if we have an appropriately named directory, search that first
            target_dir = root_dir + os.path.sep + wav_filename[:-4] + os.path.sep
            if os.path.exists(target_dir):
                path = self.locate_wavfile(wav_filename, target_dir)
                dirs.remove(target_dir)

            i = 0
            while not path and i < len(dirs):
                path = self.locate_wavfile(wav_filename, dirs[i])
                i += 1

        return path

    ## Picks a set of blocks from the csv file, for a given check2 object.
    # The check2 object has properties that tell the parser which environment-activitiy categories to pick from, and how
    # many blocks to pick for each. It is possible that there are not enough blocks of a particular category in the csv file.
    # You can check this before calling this method, by calling the have_enough_blocks() method. If there are not enough blocks of a given type, and
    # this method is still called anyway, it will return as many blocks as exist for each requested category.
    # @param self
    # @param check2 (Check2) the Check2 instance for which we are picking blocks.
    # @param alt_wav_locate_fcn (function) allows you to specify a custom search function that returns the path to the wav file, if the default locator method
    # in this class (locate_wavfile()) cannot find it. This param was added to allow calling code to pass in a function that opens a "browse file" dialog box, so that
    # the user can select the file manually if the code can't find it. The function is passed the name of the wav file we are looking for. If this custom search function
    # also fails to return a path, an exception is raised.
    # @param include_used (boolean) By default, this method only picks blocks from the parser's 'unused' category (see parse()). If this is set to True, then
    # the same block may be picked more than once.
    # @returns (list) returns a list of Test2 objects, one for each block. If there were not enough blocks of a requested environment-activity type,
    # this list will be too short. Please call the have_enough_blocks() method first to make sure you have enough blocks of each type.
    def pick_rows(self, check2, alt_wav_locate_fcn, include_used):
        sel_test2s = []
        #if self.have_enough_blocks(check2, include_used):
        check2_envs = check2.environments
        check2_envs.sort() #sort these so the UI always goes through them in the same order
        check2_acts = check2.activities
        check2_acts.sort()

        for env in check2_envs:
            for act in check2_acts:
                blocks = self.parse_dict[env][act]['unused']
                if include_used:
                    blocks = blocks + self.parse_dict[env][act]['used']

                indices = range(len(blocks))
                random.shuffle(indices)
                indices = indices[:check2.blocks_per_activity]
                for i in indices:
                    row = blocks[i]
                    short_wav_filename = Reliability2Parser.get_child_code(row) + '.wav'
                    full_wav_filename = self.locate_wavfile(short_wav_filename, check2.wav_foldername + os.path.sep)
                    if not full_wav_filename:
                        full_wav_filename = alt_wav_locate_fcn(short_wav_filename)
                        if not full_wav_filename:
                            raise Exception('Unable to locate wav file: "%s"' % (short_wav_filename))

                    test2 = Test2(
                        check2.db_id,
                        full_wav_filename,
                        Reliability2Parser.get_child_code(row),
                        Reliability2Parser.get_row_timestamp(row),#row['clock_time_tzadj'],
                        )
                    sel_test2s.append(test2)

        return sel_test2s

    ## Returns a timestamp string that uniquely identifies a row.
    # @param row (list) the row of the csv file for which to generate a timestamp string
    # @param row_offset_sec (float) the absolute start time of the row. You cannot use the "Elapsed_Time" column value for this - it may restart several times in the same file.
    # Instead, you should use an accumulator variable that calculates the absolute start time of each row as you loop through the csv file. See parse() for an example.
    # @returns (string) a timestamp string in the format "yyyy mm dd accum_sec"
    @staticmethod
    def get_row_timestamp(row, row_offset_sec):
        year = row['year']
        month = BackendUtils.pad_num_str(row['month'])
        day = BackendUtils.pad_num_str(row['day'])

        return '%s %s %s %f' % (day, month, year, row_offset_sec)

    ## Returns the child code for a give row.
    # @param row (list) the row of the csv file from which to extract the child code
    # @returns (string) a child code in the format "C_yyyymmdd" - for example, "C002_20091231"
    @staticmethod
    def get_child_code(row):
        year = row['year']
        month = BackendUtils.pad_num_str(row['month'])
        day = BackendUtils.pad_num_str(row['day'])
        child_code = row['child_id']
        
        return '%s_%s%s%s' % (child_code, year, month, day)

    ## Checks to see if we have enough blocks in a csv file to satisfy the requirements for a given Check2 object.
    #The check2 object has properties that tell the parser which environment-activitiy categories to pick from, and how
    # many blocks to pick for each.
    # @param self
    # @param check2 (Check2) the Check2 instance for which we are counting blocks.
    # @param include_used (boolean) By default, this method only counts blocks from the parser's 'unused' category (see parse()). If this is set to True, then
    # the method assumes that the same block may be picked more than once.
    # @returns (2-tuple) the first element is a boolean that is True if we have enough blocks to satisfy all requirements for the check2 object, False otherwise. The second
    # element is a string (with newlines such that it is formatted as a three column table) that indicates how many blocks for each type of environment-activity pair are available in the csv file.
    # This is suitable for printing to the UI in the event that there are not enough of one category (lets them know which category is short).
    def have_enough_blocks(self, check2, include_used):
        enough = True

        table_str = '{0:10} {1:25} {2}\n'.format('Env', 'Act', 'Count')
        i = 0
        while i < len(check2.environments): #don't short circuit where enough == True, since we want to build the whole table_str
            env = check2.environments[i]
            enough = enough and ( env in self.parse_dict )
            j = 0
            
            while j < len(check2.activities): #don't short circuit where enough == True, since we want to build the whole table_str
                act = check2.activities[j]
                if include_used:
                    enough = enough and ( act in self.parse_dict[env] and (len(self.parse_dict[env][act]['unused']) + len(self.parse_dict[env][act]['used'])) >= check2.blocks_per_activity )
                else:
                    enough = enough and ( act in self.parse_dict[env] and len(self.parse_dict[env][act]['unused']) >= check2.blocks_per_activity )

                table_str += '{0:10} {1:25} {2}\n'.format(
                    env,
                    act,
                    '%d total - %d used = %d unused' % (
                        len(self.parse_dict[env][act]['used']) + len(self.parse_dict[env][act]['unused']),
                        len(self.parse_dict[env][act]['used']),
                        len(self.parse_dict[env][act]['unused']),
                        ),
                    )
                
                j += 1
            i += 1

        return enough, table_str
