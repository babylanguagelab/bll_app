## @package parsers.reliability_exporter

import csv
import logging
import traceback

from utils.ui_utils import UIUtils
from db.bll_database import BLLDatabase, DBConstants

## The class writes details about a particular check run (from the Reliability App) to a CSV file.
class ReliabilityExporter(object):
    ## Constructor
    #  @param self
    #  @param check_run_id (int) the db_id of the run we're writing details for
    #  @param filename (string) full path to the destination CSV file
    def __init__(self, check, filename):
        #ensure file suffix is present
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        
        self.check = check
        self.filename = filename
        self.logger = logging.getLogger(__name__)

    ## Performs the write to the CSV file.
    #  @param self
    #  @returns (boolean) True if write was successful, False if an error occurred
    def export(self):
        success = True #whether write succeeded or not
        
        try:
            #write some basic info about the check
            csv_file = open(self.filename, 'wb')
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Check name: "%s"' % (self.check.name)])
            csv_writer.writerow(['Last run on %s' % (UIUtils.get_db_timestamp_str(str(self.check.last_run)))])
            csv_writer.writerow(['Created on %s' % (UIUtils.get_db_timestamp_str(str(self.check.created)))])
            csv_writer.writerow(['TRS / CSV file: %s' % (self.check.input_filename)])
            csv_writer.writerow(['WAV file: %s' % (self.check.wav_filename)])
            csv_writer.writerow(['Number of Segs: %s' % (self.check.num_segs)])
            csv_writer.writerow(['Default context padding (sec): %s' % (self.check.default_context_padding)])
            csv_writer.writerow(['Randomly Pick Segments: %s' % (str(self.check.pick_randomly)) ])

            #write filter descriptions
            if self.check.filters:
                csv_writer.writerow(['Filters:'])
                for cur_filter in self.check.filters:
                    csv_writer.writerow([cur_filter.get_filter_desc_str()])
            else:
                csv_writer.writerow(['Filters: None'])

            #write the actual data from the tests
            csv_writer.writerow([])
            headers = ['Test Number', 'LENA Start Time (w/o padding)', 'LENA End Time (w/o padding)', 'Context Padding', 'User-Adjusted Start Time', 'User-Adjusted End Time', 'Uncertain/Other', 'Syllables (with context)', 'Syllables (w/o context)', 'Actual Codes', 'Category Selection', 'Category Correct']
            csv_writer.writerow(headers) #write out the column headings

            #run through all of the tests, writing their data to the file and keeping track of how many times the user's selection was correct
            correct_count = 0
            db = BLLDatabase()
            for i in range(self.check.num_segs):
                cur_test = self.check.tests[i]
                row = []

                row.append(str(i + 1))
                row.append('%0.3f' % (cur_test.seg.start))
                row.append('%0.3f' % (cur_test.seg.end))
                row.append(str(cur_test.context_padding))
                row.append('%0.3f' % (cur_test.seg.user_adj_start))
                row.append('%0.3f' % (cur_test.seg.user_adj_end))
                row.append(str(bool(cur_test.is_uncertain)))
                row.append(str(cur_test.syllables_w_context))
                row.append(str(cur_test.syllables_wo_context) if cur_test.syllables_wo_context != None else '')

                actual_codes = self._get_actual_speaker_codes(cur_test, db)
                codes_str = ''
                for cur_codeinfo in actual_codes:
                    codes_str += cur_codeinfo.code + ' '
                if codes_str.endswith(' '):
                    codes_str = codes_str[:-1]
                row.append(codes_str)

                cat_sel = self._get_cat_sel(cur_test)
                row.append(cat_sel.disp_desc)

                cat_correct = self._get_cat_correct(cur_test, actual_codes, cat_sel)
                correct_count += int(cat_correct)
                row.append(str(bool(cat_correct)))

                csv_writer.writerow(row)

            db.close()
            csv_writer.writerow([])
            csv_writer.writerow(['Ratio correct: %0.2f' % ( float(correct_count) / float(self.check.num_segs) )])
            csv_file.close()
            success = True

        except Exception as err:
            self.logger.error('Error exporting check: %s' % (err))

        return success

    def _get_cat_sel(self, test):
        return DBConstants.COMBOS[DBConstants.COMBO_GROUPS.RELIABILITY_CATEGORIES][test.category_input]

    def _get_actual_speaker_codes(self, test, db):
        codes = []
        actual_code_rows = db.select('segs_to_speaker_codes rel join speaker_codes c on rel.speaker_code_id = c.id',
                                     ['c.code'],
                                     'rel.seg_id=?',
                                     [test.seg.db_id],
                                     )
        
        #lookup the corresponding CodeInfo object and append it to the list
        for cur_row in actual_code_rows:
            codes.append(DBConstants.SPEAKER_CODES.get_option(cur_row[0]))
            
        return codes

    ## Determines whether or not the users's selected option for a given test is correct.
    #  @param self
    #  @param cur_test (dictionary) a sub-dictionary from to get_tests_validation_data() - containing data about the test determine correctness for
    #  @param test_fcn (function) a function that tests whether an actual speaker code matches the user's combo selection. Function accepts a CodeInfo object representing an actual speaker code, and returns a boolean (False if user was incorrect, True if they were correct).
    #  @returns (boolean) True if one of the elements in cur_test's 'actual codes' list correctly corresponds to its 'category_input'
    def search_actual_codes(self, cur_test, test_fcn, actual_codes):
        result = False

        #run the function for each of the actual speaker codes
        i = 0
        while not result and i < len(actual_codes):
            result = test_fcn(actual_codes[i])
            i += 1

        return result

    ## This method updates the 'category_valid' key of a sub-dictionary obtained from get_tests_validation_data().
    # i.e. it determines whether or not the user-selected option matches a speaker.
    def _get_cat_correct(self, test, actual_codes, cat_sel):
        #map category options to functions that check if they are correct
        #each function accepts a codeinfo object and returns a boolean
        cats_enum = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.RELIABILITY_CATEGORIES]
        validate_fcns = {
            cats_enum.SILENCE: lambda speaker_code: speaker_code.is_speaker_type(DBConstants.SPEAKER_TYPES.SILENCE),
            
            cats_enum.OVERLAPPING_SPEECH: lambda speaker_code: speaker_code.has_property(DBConstants.SPEAKER_PROPS.OVERLAPPING),

            cats_enum.MEDIA: lambda speaker_code: speaker_code.has_property(DBConstants.SPEAKER_PROPS.MEDIA),

            cats_enum.TARGET_CHILD: lambda speaker_code: speaker_code.is_speaker_type(DBConstants.SPEAKER_TYPES.TARGET_CHILD),

            cats_enum.OTHER_CHILD: lambda speaker_code: speaker_code.is_speaker_type(DBConstants.SPEAKER_TYPES.OTHER_CHILD),

            cats_enum.FEMALE_ADULT: lambda speaker_code: speaker_code.is_speaker_type(DBConstants.SPEAKER_TYPES.FEMALE_ADULT),

            cats_enum.MALE_ADULT: lambda speaker_code: speaker_code.is_speaker_type(DBConstants.SPEAKER_TYPES.MALE_ADULT),

            cats_enum.DISTANT: lambda speaker_code: speaker_code.is_distance(DBConstants.SPEAKER_DISTANCES.FAR),

            cats_enum.NON_VERBAL_NOISE: lambda speaker_code: speaker_code.has_property(DBConstants.SPEAKER_PROPS.NON_VERBAL_NOISE),

            cats_enum.FUZ: lambda speaker_code: speaker_code.code == DBConstants.SPEAKER_CODES.get_option('FUZ').code,
            }

        #set the 'category valid' key based upon the result from search_actual_codes()
        cat_correct = self.search_actual_codes(test, #this is the sub-dictionary
                                               validate_fcns[cat_sel.db_id], #this is the function that validates the <em>user's selected option</em> (not the actual code). The actual code's codeinfo object is passed to this function to determine whether or not the user is correct
                                               actual_codes)

        return cat_correct
