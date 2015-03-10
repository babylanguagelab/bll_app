## @package parsers.csv_parser

import csv
import logging

from data_structs.segment import Segment
from data_structs.utterance import Utterance
from data_structs.speaker import Speaker
from db.bll_database import DBConstants
from parsers.parser_tools import *

## Parses Segment objects out a CSV file (one segment per row). Each row must contain the columns "Elapsed_Time, Segment_Duration, Speaker_ID".
class CSVParser(object):
    ## Constructor
    #  @param self
    #  @param filename (string) full path to csv file to parse
    def __init__(self, filename):
        self.logger = logging.getLogger(__name__)
        self.filename = filename
        self.segments = []
        self.parsed = False

    ## Parses the CSV file row by row, generating Segment objects.
    #  @param self
    #  @param progress_update_fcn (function=None) function that updates the progress bar, accepting a single parameter, a real number in [0.0, 1.0]
    #  @param seg_filters (list=[]) list of SegFilter objects. These filters are applied to the internal segments list in a permanent manner (i.e. anything they filter out will not be returned by this parser)
    #  @returns (list) List of the segments parsed out of the file - this list is also saved internally as self.segments
    def parse(self, progress_update_fcn=None, seg_filters=[]):
        #check if cached - if not, parse and store the results in self.segments. Otherwise, just return the cached list
        if not self.parsed:
            self._parse(progress_update_fcn, seg_filters)
            self.parsed = True

        return self.segments

    ## Goes through the file row by row.
    #  @param self
    #  @param progress_update_function (see parse())
    #  @param seg_filters (see parse())
    def _parse(self, progress_update_fcn=None, seg_filters=[]):
        #try to open the csv file
        csv_file = None
        try:
            csv_file = open(self.filename, 'rb')
        except Exception as e:
            self.logger.error('Error opening file: %s' % e)
            return []

        #determine delimiter (comma or tab)
        line = csv_file.next()
        delim = '\t' if line.find('\t') >= 0 else ','
        csv_file.seek(0)
        #print 'delim: %s' % delim

        #grab the header row
        headers = None
        reader = csv.reader(csv_file, delimiter=delim)
        rows = []
        for cur_row in reader:
            if reader.line_num == 1:
                headers = cur_row
            else:
                rows.append(cur_row)

        #iterate through the remaining rows, creating Segment objects for them
        row_dict = dict( zip(headers, rows[0]) )
        start = float(row_dict['Elapsed_Time'])
        for i in range(len(rows)):
            row_dict = dict( zip(headers, rows[i]) )
            end = start + float(row_dict['Segment_Duration'])

            #build the Utterance and put it inside the Segment
            utter = Utterance()
            utter.speaker = Speaker( '', DBConstants.SPEAKER_CODES.get_option(row_dict['Speaker_ID']) )
            utter.start = start
            utter.end = end
            utter.lena_codes.append(row_dict['Speaker_ID'])

            seg = Segment(i, utter.start, utter.end, [utter.speaker], [utter])
            utter.seg = seg

            #seg = self._parse_row(headers, rows[i], i, start, end)
            #check if the segment should be filtered out
            if ParserTools.include_seg(seg, seg_filters):
                self.segments.append(seg)
            
            if progress_update_fcn:
                progress_update_fcn( float(i + 1) / float(len(rows)) )

            start = end

        csv_file.close()

    ## Constructs a Segment object from a single row of the csv file. Each row must contain the columns "Elapsed_Time, Segment_Duration, Speaker_ID".
    #  @param self
    #  @param headers (list) List of strings, corresponding to the column titles given in the first line of the csv file. Currently, these should be unique - if things change in the future, this method will need a touchup.
    #  @param row (list) List of string - the column data from the current row we are processing
    #  @param line_num (int) Zero-based index of row, excluding the header (i.e. the first row after the header is row 0)
    #  @returns (Segment) A Segment object constructed from the data in row
    # def _parse_row(self, headers, row, line_num, accum_start, accum_end):
    #     row_dict = dict( zip(headers, row) ) #works as long as all header col names are unique
    #     utter = Utterance()
    #     utter.speaker = Speaker( '', DBConstants.SPEAKER_CODES.get_option(row_dict['Speaker_ID']) )
    #     utter.start = accum_start
    #     utter.end = accum_end
    #     utter.lena_codes.append(row_dict['Speaker_ID'])

    #     seg = Segment(line_num, utter.start, utter.end, [utter.speaker], [utter])
    #     utter.seg = seg

    #     return seg
            
