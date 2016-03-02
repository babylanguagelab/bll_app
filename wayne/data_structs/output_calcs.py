## @package data_structs.output_calcs

import logging
from db.bll_database import DBConstants
from data_structs.base_objects import BLLObject
from parsers.filter_manager import FilterManager
from utils.backend_utils import BackendUtils
from collections import OrderedDict

import re

## An OutputCalc encapsulates all of the calculations for a particular output.
#  There is a one-to-one relationship between Outputs and OutputCalcs.
#  This is an abstract base class - all subclasses should implement the methods defined here.
#  Idea: the add_seg() and add_chain() methods take in segs to be included in the calculation. Finally, write_segs() is called, which writes the results to a spreadsheet file.
#  Since output calcs can deal with either segments or chains, it is convenient to refer to them collectively as 'items' in this documentation.
class OutputCalc(BLLObject):
    ## Constructor
    #  @param self
    def __init__(self):
        pass

    ## Retreives an ordered list of args needed to instantiate this object these will be inserted into the DB. (this list will be passed directly to the constructor when the object is reinstantiated from the DB).
    #  @param self
    #  @returns (list) list of args to pass to the constructor when the object is recreated from the DB at a later date
    def get_db_args(self):
        pass

    ## Retreives a short description string that indicates what type of calculation this object is performing (eg. 'Count', 'Time Period', etc.)
    #  @param self
    #  @returns (string) short type description string to display in the UI
    def get_calc_type_str(self):
        pass

    ## Adds an unlinked segment to be considered in the calculations that this object is performing.
    #  @param self
    #  @param seg (Segment) A segment to consider in this object's calculations.
    def add_seg(self, seg):
        pass

    ## Adds a linked segment (i.e. an Utterance) to be considered in the calculations that this object is performing.
    #  @param self
    #  @param head (Utterance) the head of a chain of potentially linked Utterances. The whole chain will be considered in this object's calculations.
    def add_chain(self, head):
        pass

    ## Writes a short description of the calculation, along with the calculation results, to a csv file.
    #  @param self
    #  @param csv_writer (CSVWriter) this is a Python csv library writer objects, configured to write to the appropriate csv file.
    def write_csv_rows(self, csv_writer):
        pass

    ## This method clears any cached data from previous run (anything added by add_seg() or add_chain()), in preparation for new run
    #  @param self
    def reset(self):
        pass

## This OutputCalc searches for a regex match in a segment/chain phrase and counts the number of matches.
#  The counting can be done on a per-item basis, as an average across items, or as a sum across items.
class CountOutputCalc(OutputCalc):
    #this is an enum containing combo_options from the combo group COUNT_OUTPUT_CALC_TYPE
    COUNT_TYPES = None

    ## Constructor
    #  @param self
    #  @param search_term (string) a Python regular expression to search for in the phrase
    #  @param count_type (int) one of the values from the CountOutputCalc.COUNT_TYPES enum - specifies how it count (per item, avg across items, or sum across items)
    #  @param max_count (int=-1) a maximum threshold for the matches (-1 means no threshold) that an <em>individual item</em> can have.
    def __init__(self, search_term, count_type, max_count=-1):
        self.logger = logging.getLogger(__name__)
        self.search_term = search_term
        self.count_type = count_type
        self.max_count = max_count
        self._init_data_structs()
        self.count = 0 # count how many utterances in all
        self.sum = 0 # get sum of words in all utterances
        self.average = 0.0 # average number of words in each utterance, equal to sum / count

    ## Initializes internal data structures used to record items added to this OutputCalc.
    #  @param self
    def _init_data_structs(self):
        self.utter_dict = OrderedDict()
        self.chain_dict = OrderedDict()

    ## See superclass description.
    def reset(self):
        #clear any saved items from this instance
        self._init_data_structs()

    ## See superclass description.
    def get_db_args(self):
        return [self.search_term, self.count_type, self.max_count]

    ## See superclass description.
    def get_calc_type_str(self):
        return 'Count'

    ## See superclass description.
    def add_seg(self, seg):
        i = 0
        while seg.utters and i < len(seg.utters):
            #search the phrase for regex matches
            # if seg.utters[i].trans_phrase:
            if seg.utters[i].trans_phrase and seg.utters[i].trans_phras.lower() != 'xxx' and seg.utters[i].trans_phras.lower() != 'bbl':
                count = len(re.findall(self.search_term, seg.utters[i].trans_phrase))
                if count > self.max_count and self.max_count != -1:
                    count = self.max_count

                #track the counts for each utterance in a dictionary
                if seg.utters[i] in self.utter_dict:
                    #handle case where same utterance is added twice
                    self.utter_dict[seg.utters[i]] += count
                else:
                    self.utter_dict[seg.utters[i]] = count

            i += 1
            
    ## See superclass description.
    def add_chain(self, head):
        # if head.trans_phrase: #filter out untranscribed utterances
        if head.trans_phrase and head.trans_phrase.lower() != 'xxx' and head.trans_phrase.lower() != 'bbl':
            full_phrase = ''
            cur = head
            while cur:
                if cur.trans_phrase:
                    full_phrase += cur.trans_phrase
                    if cur.next:
                        full_phrase += ' ' #separate with a space (for search, below)
                cur = cur.next

            count = len(re.findall(self.search_term, full_phrase))
            if self.max_count != -1 and count > self.max_count:
                count = self.max_count

            #track chain counts in a dictionary, keyed by their head utterance
            if not head in self.chain_dict:
                self.chain_dict[head] = count
            else:
                #handle case where same chain is added twice
                self.chain_dict[head] += count

    ## Writes out the count results for a 'per item' count.
    #  This consists of a single line for each item, followed by its count. The total count is displayed in a row at the bottom of the section.
    #  @param self
    #  @param chained (boolean) True if we are considering linked segments, False if unlinked.
    #  @param csv_writer (CSVWriter) Python csv library writer object, set to write to the appropriate csv file.
    def _write_per_seg(self, chained, csv_writer):
        #write table headers
        csv_writer.writerow(['Start Time', 'End Time', 'Phrase', 'Count'])

        utter_list = self.chain_dict if chained else self.utter_dict
        total = 0
        #go through items, writing out each one, with its count
        for utter in utter_list:
            #linked segments
            if chained:
                phrase, tail = FilterManager.get_chain_phrase(utter)
                start = BackendUtils.get_time_str(utter.start)
                end = BackendUtils.get_time_str(tail.end)
                count = self.chain_dict[utter]

                if count > 0:
                    total += count
                    csv_writer.writerow([start,
                                         end,
                                         phrase.replace('\n', '').replace('\r', ''),
                                         count,
                                         ])

            #unlinked segments
            else:
                start = BackendUtils.get_time_str(utter.start)
                end = BackendUtils.get_time_str(utter.end)
                count = self.utter_dict[utter]

                if count > 0:
                    total += count
                    csv_writer.writerow([
                            start,
                            end,
                            utter.trans_phrase,
                            count
                            ])

        #append the total count in a row at the bottom
        csv_writer.writerow([''])
        csv_writer.writerow(['Total:', '', '', total])
        self.count = len(utter_list)

    ## Writes out the count results for an 'average across items' count.
    #  This consists of a single row with the average count.
    #  The average calculation is computed as (sum of counts from all items) / number of items <em>containing a match<\em>)
    #  @param self
    #  @param chained (boolean) True if we are considering linked segments, False if unlinked.
    #  @param csv_writer (CSVWriter) Python csv library writer object, set to write to the appropriate csv file.
    def _write_avg_across_segs(self, chained, csv_writer):
        counts = self.chain_dict.values() if chained else self.utter_dict.values()
        if counts:
            total = reduce(lambda accum, x: accum + x, counts, 0)
            avg = float(total) / float(len(counts))
            self.average = avg

            csv_writer.writerow(['Avg:', '%0.3f' % (avg)])
        else:
            csv_writer.writerow(['No matches found in TRS file.'])

    ## Writes out the count results for a 'sum across items' count.
    #  This consists of single row with the total sum.
    #  @param self
    #  @param chained (boolean) True if we are considering linked segments, False if unlinked.
    #  @param csv_writer (CSVWriter) Python csv library writer object, set to write to the appropriate csv file.
    def _write_sum_across_segs(self, chained, csv_writer):
        counts = self.chain_dict.values() if chained else self.utter_dict.values()
        total = reduce(lambda accum, x: accum + x, counts, 0)
        self.sum = total

        csv_writer.writerow(['Sum:', total])

    ## See superclass description.
    def write_csv_rows(self, chained, csv_writer):
        combo_option = DBConstants.COMBOS[DBConstants.COMBO_GROUPS.COUNT_OUTPUT_CALC_TYPES][self.count_type]
        csv_writer.writerow(['Count:', combo_option.disp_desc])
        csv_writer.writerow(['Search Term:', self.search_term])

        #call the appropriate method based on the type setting
        {CountOutputCalc.COUNT_TYPES.PER_SEG: self._write_per_seg,
         CountOutputCalc.COUNT_TYPES.AVG_ACROSS_SEGS: self._write_avg_across_segs,
         CountOutputCalc.COUNT_TYPES.SUM_ACROSS_SEGS: self._write_sum_across_segs,
         }[self.count_type](chained, csv_writer)

## This OutputCalc searches for a regex match in a segment/chain phrase and counts the number of matches, then divides the count by the length of the segment in seconds.
#  The output is a measure of count/sec. This can be computed for each item individually ('per item'), or as an average across items.
class RateOutputCalc(OutputCalc):
    #this is an enum containing options from combo group RATE_OUTPUT_CALC_TYPE
    RATE_TYPES = None

    ## Constructor
    #  @param self
    #  @param search term (string) a Python regular expression to search for in the the item phrases.
    #  @param rate_type (int) one of the options from the enum RateOutputCalc.RATE_TYPES - indicating how the rate is to be calculated (per item, or average across items)
    def __init__(self, search_term, rate_type):
        self.logger = logging.getLogger(__name__)
        self.search_term = search_term
        self.rate_type = rate_type
        self._init_data_structs()

    ## Initializes internal data structures used to record items added to this OutputCalc.
    #  @param self
    def _init_data_structs(self):
        self.chain_dict = OrderedDict()
        self.utter_dict = OrderedDict()

    ## See superclass description.
    def reset(self):
        self._init_data_structs()

    ## See superclass description.
    def get_db_args(self):
        return [self.search_term, self.rate_type]

    ## See superclass description.
    def get_calc_type_str(self):
        return 'Rate'

    ## See superclass description.
    def add_seg(self, seg):
        i = 0
        while seg.utters and i < len(seg.utters):
            #search the phrase for regex matches
            if seg.utters[i].trans_phrase:
                count = len(re.findall(self.search_term, seg.utters[i].trans_phrase))

                #skip utters with no end/start time recorded
                if seg.utters[i].end != None and seg.utters[i].start != None:
                    time = seg.utters[i].end - seg.utters[i].start

                    #record the result in a dictionary, keyed by utterance. Each entry is a tuple of the form (number of matches, length of segment in seconds)
                    if seg.utters[i] in self.utter_dict:
                        self.utter_dict[seg.utters[i]][0] += count
                        self.utter_dict[seg.utters[i]][1] += time
                    else:
                        self.utter_dict[seg.utters[i]] = (count, time)
            i += 1

    ## See superclass description.
    def add_chain(self, head):
        if head.trans_phrase: #filter out untranscribed utterances
            count = 0
            i = 0
            cur = head
            tail = head
            #count the number of matches in the whole chain
            while cur:
                if cur.trans_phrase:
                    count += len(re.findall(self.search_term, cur.trans_phrase))
                tail = cur
                cur = cur.next

            #skip chains with no end/start time recorded
            if tail.end != None and head.start != None:
                time = tail.end - head.start
                #record the result in a dictionary, keyed by the head utterance. Each entry is a tuple of the form (number of matches, length of segment in seconds)
                if not head in self.utter_dict:
                    self.chain_dict[head] = (count, time)
                else:
                    self.chain_dict[head][0] += count
                    self.chain_dict[head][1] += time

    ## Writes the results for a 'per item' rate calculation to a spreadsheet file.
    #  This consists of a single row for each item, with it's corresponding rate.
    #  @param self
    #  @param chained (boolean) True if we are considering linked segments, False if unlinked.
    #  @param csv_writer (CSVWriter) Python csv library writer object, set to write to the appropriate csv file.
    def _write_per_seg(self, chained, csv_writer):
        #write headers row
        csv_writer.writerow(['Start Time', 'End Time', 'Phrase', 'Occurances', 'Time Elapsed(sec)', 'Rate (occurrances/sec)'])

        #go through all items, performing the rate calculation and writing it to the spreadsheet file
        utter_list = self.chain_dict if chained else self.utter_dict
        for utter in utter_list:
            start = None
            end = None
            phrase = None
            rate = None
            count = None
            time = None
            
            if chained:
                #count number of matches in entire chain
                phrase, tail = FilterManager.get_chain_phrase(utter)
                start = utter.start
                end = tail.end
                count, time = self.chain_dict[utter]
                rate = float(count) / float(time)
                
            else:
                start = utter.start
                end = utter.end
                phrase = utter.trans_phrase
                count, time = self.utter_dict[utter]
                rate = float(count) / float(time)

            csv_writer.writerow([BackendUtils.get_time_str(start),
                                 BackendUtils.get_time_str(end),
                                 phrase.replace('\n', '').replace('\r', ''),
                                 count,
                                 time,
                                 rate,
                                 ])

    ## Writes the results for a 'average across items' rate calculation to a spreadsheet file.
    #  This consists of a single row containing the average.
    #  The average is calculated as (sum of number of matches across all items) / (sum of lengths of <em>all</em> items, in seconds)
    def _write_avg_across_segs(self, chained, csv_writer):
        pairs = self.chain_dict.values() if chained else self.utter_dict.values()
        total_time = 0.0
        total_count = 0

        for cur_pair in pairs:
            count, time = cur_pair
            total_count += count
            total_time += time
            
        avg = float(total_count) / total_time

        csv_writer.writerow(['Avg:', avg])

    ## See superclass description.
    def write_csv_rows(self, chained, csv_writer):
        combo_option = DBConstants.COMBOS[DBConstants.COMBO_GROUPS.RATE_OUTPUT_CALC_TYPES][self.rate_type]
        csv_writer.writerow(['Rate:', combo_option.disp_desc])
        csv_writer.writerow(['Search Term:', self.search_term])

        #call the appropriate method based on the type setting
        {RateOutputCalc.RATE_TYPES.PER_SEG: self._write_per_seg,
         RateOutputCalc.RATE_TYPES.AVG_ACROSS_SEGS: self._write_avg_across_segs,
         }[self.rate_type](chained, csv_writer)

## This OutputCalc searches for a regex match in the items' phrases, and calculates the total length of the items (in seconds) that contain a match.
class TimePeriodOutputCalc(OutputCalc):
    ## Constructor
    #  @param self
    #  @param search term (string) a Python regular expression to search for in the the item phrases.
    def __init__(self, search_term):
        self.logger = logging.getLogger(__name__)
        self.search_term = search_term
        self._init_data_structs()

    ## Initializes the data structures used to record the items added to this OutputCalc.
    def _init_data_structs(self):
        self.utters_dict = {}
        self.chains_dict = {}
        
        self.utters_filtered_time = 0.0
        self.chains_filtered_time = 0.0

    ## See superclass description.
    def reset(self):
        self._init_data_structs()

    ## See superclass description.
    def get_db_args(self):
        return [self.search_term]

    ## See superclass description.
    def get_calc_type_str(self):
        return 'Time Period'

    ## Searches through the internal dictionary for a key that intersects with the specified start and end times.
    #  The dictionary is keyed by tuples of the form (start_time, end_time).
    #  This routine checks to see if the specified start and end range intersects with any key tuple already in the dictionary.
    #  @param self
    #  @param start (float) an Utterance start time
    #  @param end (float) an Utterance end time
    #  @returns (tuple) if an intersecting tuple is found, that tuple is returned. Else None is returned.
    def _get_chain_intersection(self, start, end):
        found_key = None
        keys = self.chains_dict.keys()

        i = 0
        while not found_key and i < len(keys):
            if ( (start >= keys[i][0] and start <= keys[i][1]) or
                 (end <= keys[i][1] and end >= keys[i][0]) ):
                found_key = keys[i]
            i += 1

        return found_key

    ## Searched through the phrases of Utterances in a chain, for a match against the regex.
    #  @param self
    #  @param head (Utterance) head of the chain to search
    #  @returns (boolean) True if a match was found anywhere in the chain phrase, False otherwise.
    def _search_chain_phrase(self, head):
        cur = head
        found = False
        
        while not found and cur:
            if cur.trans_phrase:
                found = re.search(self.search_term, cur.trans_phrase) != None
            cur = cur.next

        return found

    ## See superclass description.
    #  We may have segments that start and end at exactly the same time.
    #  We are guarenteed never to have segments that intersect in other ways.
    def add_seg(self, seg):
        for utter in seg.utters:
            #make sure the Utterance has a start and end time so we can calculate it's length. Also make sure it's been transcribed.
            if utter.end != None and utter.start != None and utter.trans_phrase:
                #only store an entry in the dictionary if an Utterance with equivalent start/end times is not already present
                if not (utter.start, utter.end) in self.utters_dict:
                    self.utters_dict[(utter.start, utter.end)] = True #it doesn't matter what we store here - the key is the important part. We're just using a dictionary for it's fast lookup abilities.

                    #maintain a sum of the lengths of the segments that have been inserted (and contain a match)
                    if utter.trans_phrase and re.search(self.search_term, utter.trans_phrase):
                        self.utters_filtered_time += (utter.end - utter.start)

    ## See superclass description.
    #  Here things are more complicated than in add_seg() because chains can intersect in time (in any way).
    def add_chain(self, head):
        #only proceed if the first Utterance is transcribed
        if head.trans_phrase:
            tail = FilterManager.get_endpoint(FilterManager.ENDPOINT_TYPES.TAIL, head)
            #make sure both start and end times on the the ends of the chain are present
            if tail.end != None and head.start != None:
                #if we find a match, check for intersection in the internal dictionary
                if self._search_chain_phrase(head):
                    key_tuple = self._get_chain_intersection(head.start, tail.end)
                    new_key_tuple = None

                    #if an intersection occurred we need to figure out how to adjust things...
                    if key_tuple:
                        #remove the intersecting key and subtract it's length from the sum (this sum was previously added)
                        self.chains_dict.pop(key_tuple)
                        self.chains_filtered_time -= (key_tuple[1] - key_tuple[0])

                        #Obtain the widest (start, end) range by comparing the intersecting key with the start and end times of the Utterance we're trying to insert.
                        #This new key will be inserted into the dictionary below.
                        #This ensures that we will always detect future intersections.
                        new_key_tuple = (min(key_tuple[0], head.start), max(key_tuple[1], tail.end))
                        
                    #if no intersection occurred, we can just add the (start, end) tuple of the head Utterance to the dictionary
                    else:
                        new_key_tuple = (head.start, tail.end)

                    #factor the length of the new key into the sum, and add the key to the internal dictionary
                    self.chains_filtered_time += (new_key_tuple[1] - new_key_tuple[0])
                    self.chains_dict[new_key_tuple] = True

    ## See superclass description.
    def write_csv_rows(self, chained, csv_writer):
        csv_writer.writerow(['Time Period'])

        total_time = self.chains_filtered_time if chained else self.utters_filtered_time

        csv_writer.writerow(['Search Term:', self.search_term])
        csv_writer.writerow(['Time Containg Matches:', BackendUtils.get_time_str(total_time)])

## This type of OutputCalc constructs a table of counts.
#  The user can select two transcriber codes. The first is the row criteria. All elements of the code are enumerated along the left (vertical axis) side of the table.
#  The second is the column criteria. All elements of this code are enumerated along the top (horizontal axis) of the table.
#  Each internal table cell will contain a count of the number of items found that have both the horizontal and vertical codes.
class BreakdownOutputCalc(OutputCalc):
    #This is an enum of options from BREAKDOWN_OUTPUT_CALC_CRITERIA
    BREAKDOWN_CRITERIA = None

    ## Constructor
    #  @param self
    #  @param row_criteria (int) one of the values from the enum BreakdownOutputCalc.BREAKDOWN_CRITERIA. Indicates the row code.
    #  @param col_criteria (int) one of the values from the enum BreakdownOutputCalc.BREAKDOWN_CRITERIA. Indicates the column code.
    def __init__(self, row_criteria, col_criteria):
        self.logger = logging.getLogger('stats_app')
        self.row_criteria = row_criteria
        self.col_criteria = col_criteria
        self._init_data_structs()

    ## Initializes data structs used to keep track of items added to this OutputCalc.
    #  @param self
    def _init_data_structs(self):
        self.seg_list = []
        self.chain_list = []

    ## See superclass description.
    def reset(self):
        self._init_data_structs()

    ## See superclass description.
    def get_db_args(self):
        return [self.row_criteria, self.col_criteria]

    ## See superclass description.
    def get_calc_type_str(self):
        return 'Breakdown'

    ## See superclass description.
    def add_seg(self, seg):
        self.seg_list.append(seg)

    ## See superclass description.
    def add_chain(self, head):
        self.chain_list.append(head)

    ## Given a row or column criteria selected by the user, provides the corresponding transcriber code index.
    #  @param self
    #  @param criteria (int) an option from BreakdownOutputCalc.BREAKDOWN_CRITERIA
    #  @returns (int) the index (zero-based) of the transcriber code corresponding the specified criteria that the user has selected
    def _get_trans_code_index(self, criteria):
        return {
            BreakdownOutputCalc.BREAKDOWN_CRITERIA.SPEAKER_TYPE: 0,
            BreakdownOutputCalc.BREAKDOWN_CRITERIA.TARGET_LISTENER: 1,
            BreakdownOutputCalc.BREAKDOWN_CRITERIA.COMPLETENESS: 2,
            BreakdownOutputCalc.BREAKDOWN_CRITERIA.UTTERANCE_TYPE: 3,
            }[criteria]

    ## Determines the transcriber code index that the specified criteria corresponds to, then returns the code in that index from the specified Utterance.
    #  @self
    #  @utter (Utterance) the utterance who's code you want to grab
    #  @criteria (int) an option from BreakdownOutputCalc.BREAKDOWN_CRITERIA
    #  @returns (string) a transcriber code, or None if the Utterance has no transcriber codes
    def _get_utter_criteria_code(self, utter, criteria):
        code = None
        trans_code_index = self._get_trans_code_index(criteria)
        if len(utter.trans_codes) > trans_code_index:
            code = utter.trans_codes[trans_code_index]

        return code

    ## See superclass description.
    #  This method writes out the table of counts to a spreadsheet file.
    #  The user can select two codes. The first is the row criteria. All elements of the code are enumerated along the left (vertical axis) side of the table.
    #  The second is the column criteria. All elements of this code are enumerated along the top (horizontal axis) of the table.
    #  Each internal table cell will contain a count of the number of items found that have both the horizontal and vertical codes.
    #  In cases where codes can have multiple characters (eg. transcriber code 3), only the single codes will be enumerated in the table headers.
    #  If items are found containing multiple character codes, then each character in the code increments one cell (the item will be 'counted once for each character'').
    def write_csv_rows(self, chained, csv_writer):
        row_combo = DBConstants.COMBOS[DBConstants.COMBO_GROUPS.BREAKDOWN_OUTPUT_CALC_CRITERIA][self.row_criteria]
        col_combo = DBConstants.COMBOS[DBConstants.COMBO_GROUPS.BREAKDOWN_OUTPUT_CALC_CRITERIA][self.col_criteria]

        csv_writer.writerow(['Row Criteria:', row_combo.disp_desc])
        csv_writer.writerow(['Column Criteria:', col_combo.disp_desc])

        #build an array of all possible options for the code corresponding to the row criteria
        row_code_index = self._get_trans_code_index(self.row_criteria)
        row_code = DBConstants.TRANS_CODES[row_code_index]
        row_code_strs = row_code.get_all_options_codes()

        #do the same for the column criteria
        col_code_index = self._get_trans_code_index(self.col_criteria)
        col_code = DBConstants.TRANS_CODES[col_code_index]
        col_code_strs = col_code.get_all_options_codes()

        csv_writer.writerow([''] + col_code_strs) # headers (note: top left cell is blank)

        #this has records the values of the internal table cells
        count_hash = OrderedDict()

        #locate our data source
        data_list = self.chain_list if chained else self.seg_list

        #initialize all table cell values to 0
        for row in row_code_strs:
            count_hash[row] = OrderedDict()
            for col in col_code_strs:
                count_hash[row][col] = 0

        #go through the data, incrementing the appropriate table cells in the count_hash
        for datum in data_list:
            if chained:
                if datum.trans_phrase: #filter out untranscribed utters
                    #Each chain contributes one to the count (with the exception of those containing multi-char codes).
                    #It is assumed that the head has the same trans codes as the rest (with exception of C code in tail).
                    row_code = self._get_utter_criteria_code(datum, self.row_criteria)
                    col_code = self._get_utter_criteria_code(datum, self.col_criteria)
                    if row_code != None and col_code != None:
                        for row_char in row_code: #for multi-char codes, increment count_hash individually for each char
                            for col_char in col_code:
                                try:
                                    count_hash[row_char][col_char] += 1
                                    
                                except KeyError as err:
                                    self.logger.info('Output Calc encountered unrecognized key: %s' % (err))
                                    self.logger.info('row_code: %s, col_code: %s' % (row_code, col_code))
                                    self.logger.info('Utterance: %s' % (datum))
                                    
                                    #also dump to stdout for now to make it obvious
                                    print 'Output Calc encountered unrecognized key: %s' % (err)
                                    print 'row_code: %s, col_code: %s' % (row_code, col_code)
                                
            else:
                utter_index = 0
                while datum.utters and utter_index < len(datum.utters):
                    if datum.utters[utter_index].trans_phrase: #filter out untranscribed utters
                        row_code = self._get_utter_criteria_code(datum.utters[utter_index], self.row_criteria)
                        col_code = self._get_utter_criteria_code(datum.utters[utter_index], self.col_criteria)
                        if row_code != None and col_code != None:
                            for row_char in row_code: #for multi-char codes, increment count_hash individually for each char
                                for col_char in col_code:
                                    try:
                                        count_hash[row_char][col_char] += 1
                                        
                                    except KeyError as err:
                                        self.logger.info('Output Calc encountered unrecognized key: %s' % (err))
                                        self.logger.info('row_code: %s, col_code: %s' % (row_code, col_code))
                                        self.logger.info('Utterance: %s' % (datum))

                                        #also dump to stdout for now to make it obvious
                                        print 'Output Calc encountered unrecognized key: %s' % (err)
                                        print 'row_code: %s, col_code: %s' % (row_code, col_code)

                    utter_index += 1

        #add column (vertical) headers and count_matrix rows to spreadsheet
        for row_key in count_hash:
            csv_writer.writerow( [row_key] + map(lambda col_key: count_hash[row_key][col_key], count_hash[row_key]) )

## This type of OutputCalc searches for a regex match in the phrase of items. Items containing one or more matches are shown in a list. The list is grouped by a particular (user-selected) transcriber code.
class ListOutputCalc(OutputCalc):
    #this is an enum of combo options from the LIST_OUTPUT_CALC_CATS combo group
    LIST_CATS = None

    ## Constructor
    #  @param self
    #  @param search_term (string) a Python regular expression
    #  @cat (int) one of the options from ListOutpuCalc.LIST_CATS. Indicates which transcriber code to group by.
    def __init__(self, search_term, cat):
        self.logger = logging.getLogger(__name__)
        self.search_term = search_term
        self.cat = cat
        self._init_data_structs()

    ## Initializes the data structs used to keep track of the items that have been added to this OutputCalc.
    def _init_data_structs(self):
        self.utter_list = []
        self.chain_list = []

    ## See superclass description.
    def reset(self):
        self._init_data_structs()

    ## See superclass description.
    def get_db_args(self):
        return [self.search_term, self.cat]

    ## See superclass description.
    def get_calc_type_str(self):
        return 'List'

    ## See superclass description.
    def add_seg(self, seg):
        i = 0
        #filter the utterances using the regex - only include utterances that contain a match
        while seg.utters and i < len(seg.utters):
            if seg.utters[i].trans_phrase and re.search(self.search_term, seg.utters[i].trans_phrase):
                self.utter_list.append(seg.utters[i])
            i += 1

    ## See superclass description.
    def add_chain(self, head):
        cur = head
        found = False
        #only include chains that yield at least one regex match
        while not found and cur:
            if cur.trans_phrase:
                found = re.search(self.search_term, cur.trans_phrase)
            cur = cur.next

        if found:
            self.chain_list.append(head)

    ## Retreives the transcriber code index, given a user-selected category option.
    #  @param self
    #  @param cat (int) one of the options from  ListOutpuCalc.LIST_CATS
    #  @returns (int) the index (zero-based) or the corresponding transcriber code
    def _get_trans_code_index(self, cat):
        return {
            ListOutputCalc.LIST_CATS.SPEAKER_TYPE: 0,
            ListOutputCalc.LIST_CATS.TARGET_LISTENER: 1,
            ListOutputCalc.LIST_CATS.COMPLETENESS: 2,
            ListOutputCalc.LIST_CATS.UTTERANCE_TYPE: 3,
            }[cat]

    ## See superclass description.
    def write_csv_rows(self, chained, csv_writer):
        combo = DBConstants.COMBOS[DBConstants.COMBO_GROUPS.LIST_OUTPUT_CALC_CATS][self.cat]
        csv_writer.writerow(['List:', combo.disp_desc])
        csv_writer.writerow(['Search Term:', self.search_term])

        #use the selected category option to grab a list of all possible values for the corresponding code
        trans_code_index = self._get_trans_code_index(self.cat)
        group_code = DBConstants.TRANS_CODES[trans_code_index]
        group_code_strs = group_code.get_all_options_codes()

        #This dictionary holds the list items, separating the groups - it's keyed by transcriber code.
        #Each value is another dictionary, keyed by utterance.
        #Note that we can add the same utterance to different groups if we're working with a multi-character transcriber code.
        group_dict = OrderedDict()
        data_list = self.chain_list if chained else self.utter_list

        #organize the data into groups based on transcriber code value
        for utter in data_list:
            code_str = None
            if chained:
                cur = utter
                while cur:
                    if len(cur.trans_codes) > trans_code_index:
                        code_str = cur.trans_codes[trans_code_index]

                        if not code_str in group_dict:
                            group_dict[code_str] = OrderedDict()
                            
                        if not utter in group_dict[code_str]:
                            group_dict[code_str][utter] = True
                            
                    cur = cur.next
                
            else:
                if len(utter.trans_codes) > trans_code_index:
                    code_str = utter.trans_codes[trans_code_index]
                    
                    if not code_str in group_dict:
                        group_dict[code_str] = OrderedDict()
                        
                    if not utter in group_dict[code_str]:
                        group_dict[code_str][utter] = True

        #write out the csv file
        for code in group_dict:
            csv_writer.writerow([''])
            csv_writer.writerow(['', 'Code:', code])
            csv_writer.writerow(['', 'Start Time', 'End Time', 'LENA Speakers', 'Phrase', 'Transcriber Codes'])
            for utter in group_dict[code]:
                if chained:
                    trans_codes, tail = FilterManager.get_chain_trans_codes(utter)
                    trans_codes = trans_codes.replace('\n', '').replace('\r', '')
                    speakers, tail = FilterManager.get_chain_lena_speakers(utter)
                    speakers = speakers.replace('\n', '').replace('\r', '')
                    phrase, tail = FilterManager.get_chain_phrase(utter)
                    phrase = phrase.replace('\n', '').replace('\r', '')
                    start_str = BackendUtils.get_time_str(utter.start)
                    end_str = BackendUtils.get_time_str(tail.end)
                    csv_writer.writerow(['', start_str, end_str, speakers, phrase, trans_codes])
                    
                else:
                    csv_writer.writerow(['',
                                         BackendUtils.get_time_str(utter.start),
                                         BackendUtils.get_time_str(utter.end),
                                         utter.speaker.speaker_codeinfo.code if utter.speaker and utter.speaker.speaker_codeinfo else '?',
                                         utter.trans_phrase,
                                         '|%s|' % ('|'.join(utter.trans_codes)) if utter.trans_codes else 'None',
                                     ])

## This function fills in the combo_option constants in the above classes.
#  These constants exist only for convenience (so you don't have to access them via DBConstants using the combo group, which invloves a lot of typing).
def fetch_db_constants():
    #should really remove the 'EMPTY' option here somehow...
    CountOutputCalc.COUNT_TYPES = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.COUNT_OUTPUT_CALC_TYPES]
    RateOutputCalc.RATE_TYPES = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.RATE_OUTPUT_CALC_TYPES]
    BreakdownOutputCalc.BREAKDOWN_CRITERIA = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.BREAKDOWN_OUTPUT_CALC_CRITERIA]
    ListOutputCalc.LIST_CATS = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.LIST_OUTPUT_CALC_CATS]
    
fetch_db_constants()
