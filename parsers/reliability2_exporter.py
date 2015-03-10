## @package parsers.reliability2_exporter

import csv

from parsers.reliability2_parser import Reliability2Parser
from utils.backend_utils import BackendUtils

## This calss writes details about a check2 object (a unit of data from the Reliability2 App) to a CSV file.
class Reliability2Exporter(object):
    ## Constructor
    # @param self
    # @param write_filename (string) path to the csv file we will write the data to
    # @param check2 (Check2) a Check2 object containing the data to write - see data_structs.Check2
    def __init__(self, write_filename, check2):
        self.out_file = open(write_filename, 'wb')
        self.in_file = open(check2.csv_filename, 'rb')

        self.check2 = check2

    ## This method extracts data from the Check2 object and writes it to the csv file in a nicely formatted manner.
    # @param self
    # @param include_trans (boolean) If True, the method will append an extra CSV column containing the actual transcription
    # text that was entered by the user for each clip.
    #  @param progress_update_fcn (function=None) function accepting a value in [0,1] to display as a progress bar - see utils.ProgressDialog. This value is used to indicate the level of completeness <em>of the current phase</em>
    #  @param progress_next_phase_fcn(function=None) - moves the progress bar to the next phase, which causes new text to be displayed in the bar - see utils.ProgressDialog
    def export(self, include_trans, progress_update_fcn=None, progress_next_fcn=None):
        reader = csv.DictReader(self.in_file)
        extra_headers = ['Child Voc', 'Word Count']
        if include_trans:
            extra_headers.append('Transcription')
        out_headers = reader.fieldnames + extra_headers
        writer = csv.DictWriter(self.out_file, out_headers)

        writer.writeheader()

        #The composite key (child_code, timestamp) uniquely identifies a row (assuming a child can't be in two
        # places at the same time :) We are going to build a lookup table that is keyed based on this combination of values.
        
        #Match the rows: we can generate a dict of self.check2.test2s
        #and go through the input file one row at a time, storing matches in the out_rows array below.
        #We must store to this array in the order the tests were run, not the order they appear in the input file.
        test2_dict = {}
        for i in range(len(self.check2.test2s)):
            test2 = self.check2.test2s[i]
            key = test2.child_code + test2.spreadsheet_timestamp
            test2_dict[key] = (test2, i)
        
        out_rows = [None] * len(self.check2.test2s)
        all_rows = list(reader)
        match_count = 0
        
        i = 0
        while i < len(all_rows) and match_count < len(self.check2.test2s):
            row = all_rows[i]
            year = row['year']
            month = BackendUtils.pad_num_str(row['month'])
            day = BackendUtils.pad_num_str(row['day'])
            elapsed_sec = row['Elapsed_Time']
            key = Reliability2Parser.get_child_code(row) + '%s %s %s %s' % (day, month, year, elapsed_sec) #row['clock_time_tzadj']
            if key in test2_dict:
                row[extra_headers[0]] = test2_dict[key][0].child_vocs
                row[extra_headers[1]] = BackendUtils.get_word_count(test2_dict[key][0].transcription)
                if include_trans:
                    row[extra_headers[2]] = test2_dict[key][0].transcription
                    match_count += 1

                out_rows[test2_dict[key][1]] = row

            if progress_update_fcn:
                progress_update_fcn(float(i + 1) / float(len(all_rows)))

            i += 1

        if progress_next_fcn:
            progress_next_fcn()
        for i in range(len(out_rows)):
            row = out_rows[i]
            if row == None:
                raise Exception('Unable to match Test2 object with input spreadsheet row. Has spreadsheet changed?')
            else:
                writer.writerow(row)

            if progress_update_fcn:
                progress_update_fcn(float(i + 1) / float(len(out_rows)))

    ## Closes this parser. This just closes all the open files that it is using.
    # Calling this method is necessary to ensure that all of the data that was written to the csv file is actually flushed to disk.
    # @param self
    def close(self):
        self.out_file.close()
        self.in_file.close()        
