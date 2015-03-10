## @package parsers.freq_exporter

import logging
import csv
from utils.ui_utils import UIUtils

## This class provides the ability to export data for the WH-Frequency App.
# Note: 'Count Columns' are columns that the user has added to the main window. These columns count user-specified (regex) patterns.
class FreqExporter(object):
    ## Constructor
    #  @param self
    #  @param filename (string) full path to the CSV spreadsheet file to write to
    #  @param trs_filename (string) full path to the trs file being used by the WH-Frequency App
    def __init__(self, filename, trs_filename):
        #log errors to log/
        self.logger = logging.getLogger(__name__)

        #make sure file suffix is present
        if not filename.lower().endswith('.csv'):
            filename += '.csv'

        self.filename = filename
        self.trs_filename = trs_filename

        #create a basic csv-writing object using the python csv library
        self.csv_file = open(self.filename, 'wb')
        self.csv_writer = csv.writer(self.csv_file, quoting=csv.QUOTE_ALL)

    ## Writes the column headings to the spreadsheet file.
    #  @param self
    #  @param count_col_headers (list) list of strings, each representing the headers for any 'count columns' the user has added
    def write_header_row(self, count_col_headers):
        self.csv_writer.writerow(['Date: %s' % UIUtils.get_cur_timestamp_str()])
        self.csv_writer.writerow(['File: %s' % self.trs_filename])
        self.csv_writer.writerow([''])
        headers = ['Time', 'Phrase', 'Speakers', 'Target Listeners', 'WHQ Count']
        headers.extend(count_col_headers)
        self.csv_writer.writerow(headers)

    ## Writes a row of data to the spreadsheet file.
    #  This includes the values for the user-specified 'count columns'.
    #  @param self
    #  @param time_str (string) a string containing the start and end times of the utterance this row corresponds to (eg. '00:01:00 - 00:02:00')
    #  @param phrase (string) the transcription phrase for the utterance this row corresponds to
    #  @param speakers_str (string) a string containing a description of the speakers for the utterance this row corresponds to
    #  @param targets_str (string) a string containing a description of the target listenders for the utterance this row corresponds to
    #  @param num_whq (int) an integer representing the number of WH Questions conatined in the utterance this row corresponds to
    #  @param count_col_vals (list) list of the values for the user-defined 'count columns'
    def write_count_row(self, time_str, phrase, speakers_str, targets_str, num_whq, count_col_vals):
        row = [time_str, phrase, speakers_str, targets_str, num_whq]
        row.extend(count_col_vals)
        self.csv_writer.writerow(row)

    ## Writes a final 'Totals' row to the spreadsheet file.
    #  This row contains the sum of the 'WH count" column, in addition to the sums of the user-defined 'count columns'.
    #  @param self
    #  @param total_whq (int) the sum of the 'WH Counts' across all rows that have been written to the spreadsheet.
    #  @param count_col_totals (list) list of integers - each representing the sum of a particular 'count-column'.
    def finish(self, total_whq, count_col_totals):
        self.csv_writer.writerow([''])
        row = ['', '', '', 'Totals:', total_whq]
        row.extend(count_col_totals)
        self.csv_writer.writerow(row)
        self.csv_file.close()
