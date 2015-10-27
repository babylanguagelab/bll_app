import re
from enum import Enum


class ParseUttersStateMachine():
    def __init__(self, trs_parser, segment):
        self.trs_parser = trs_parser
        self.seg = segment

        self.utter_list = []
        self.States = Enum(['INITIAL', 'INITIAL_SYNC_TAG', 'WHO_TAG'])
        self.cur_state = self.States.INITIAL

    def drive(self, next_obj):
        # In the initial state
        if self.cur_state == self.States.INITIAL:
            if next_obj.tag == 'Sync':
                # grab the speech data from the element.
                utters = self.trs_parser.parse_speech_data(self.seg, next_obj)

                # set the start time
                start_time = float(next_obj.attrib['time'])
                map(lambda u: setattr(u, 'start', start_time), utters)
                self.utter_list.extend(utters)

                # move to next state
                self.cur_state = self.States.INITIAL_SYNC_TAG
        elif self.cur_state == self.States.INITIAL_SYNC_TAG:
            if next_obj.tag == 'Sync':
                end_time = float(next_obj.attrib['time'])
                # work backward through the list until we reach the point at
                # which utters already have an end time
                # (or we reach the beginning of the list)
                i = len(self.utter_list) - 1
                while (i >= 0 and self.utter_list[i].end is None):
                    self.utter_list[i].end = end_time
                    i -= 1

                new_utters = self.trs_parser.parse_speech_data(self.seg,
                                                               next_obj)
                start_time = float(next_obj.attrib['time'])
                map(lambda u: setattr(u, 'start', start_time), new_utters)
                self.utter_list.extend(new_utters)
            elif next_obj.tag == 'Who':
                # pop utterance created from previous empty sync tag
                old_utter = self.utter_list.pop()
                self.trs_parser.total_utters -= 1

                new_utters = self.trs_parser.parse_speech_data(self.seg,
                                                               next_obj)
                map(lambda u: setattr(u, 'start', old_utter.start), new_utters)
                self.utter_list.extend(new_utters)

                self.cur_state = self.States.WHO_TAG
        elif self.cur_state == self.States.WHO_TAG:
            if next_obj.tag == 'Sync':
                sync_time = float(next_obj.attrib['time'])
                i = len(self.utter_list) - 1
                while i >= 0 and self.utter_list[i].end is None:
                    self.utter_list[i].end = sync_time
                    i -= 1

                new_utters = self.trs_parser.parse_speech_data(self.seg,
                                                               next_obj)
                map(lambda u: setattr(u, 'start', sync_time), new_utters)
                self.utter_list.extend(new_utters)

                self.cur_state = self.States.INITIAL_SYNC_TAG

            elif next_obj.tag == 'Who':
                new_utters = self.trs_parser.parse_speech_data(self.seg,
                                                               next_obj)
                map(lambda u: setattr(u, 'start', self.utter_list[-1].start),
                    new_utters)
                self.utter_list.extend(new_utters)

    def finish(self, final_obj):
        final_end_time = float(final_obj.attrib['endTime'])

        # Append the end time to any outstanding Utterances in self.utter_list
        if self.cur_state == self.States.INITIAL_SYNC_TAG or \
           self.cur_state == self.States.WHO_TAG:
            i = len(self.utter_list) - 1
            while i >= 0 and self.utter_list[i].end is None:
                self.utter_list[i].end = final_end_time
                i -= 1

    ## Retreieves the list of Utterances that this state machine has constructed.
    #  This method should only be called after finish() has been called (Otherwise there may be incomplete Utterances in the returned list)
    #  @param self
    #  @returns (list) list of Utterance objects
    def get_result(self):
        return self.utter_list

## This class handles the job of linking together Utterances (via their next/prev pointers) that are marked with I/C codes (transcriber code 3) by the transcribers.
#  Utterances are 'linkable' if an I/C code can be used to tie them to another utterance. They are 'unlinkable' if they cannot be. Unlinkable Utterances usually consist of silence (speaker is SIL),
#  or non-verbal noise (and have no transcription phrase). The ''is_linkable column of the 'speaker_codes' database table defines the particular speakers that make an utterance linkable/unlinkable.
#  In addition to linking Utterances, this class also provides error detection for problems like 'I without C', 'C without I', 'ambiguous I/C codes', etc. These errors are appended to the TRSParser's ErrorCollector.
#  Utterances are only linked across segments (not within segments).
#  The transcriber manual dictates that when ambiguous I/C codes are used, they must be numbered
#  (eg. I, I1, and I2, link to C, C1, and C2, respectively). These numbers are referred to as 'link numbers' (not to be confused with 'segment numbers', which refer to Segment objects' 'num' attributes).
#  In order to simplify the linking process, the state machine considers the initial I or C codes to have the number 0 (eg. I links to C becomes I0 links to C0).
#  Usage: after instantiating the class, call drive() with every Utterance. Then call finish().
class LinkUttersStateMachine(object):
    ## Constructor
    #  @param self
    #  @param trs_parser (TRSParser) This class must be driven from an instance of a TRSParser
    def __init__(self, trs_parser):
        self.trs_parser = trs_parser
        
        #holds the link numbers of utterances with I/C codes that have been encountered in the current and previous segments, respectively
        self.link_dict = {'cur_links': {},
                          'prev_links': {}
                          }
        
        # holds the segment whose utterances we are currently working with
        self.cur_linkable_seg = None
        # holds the segment whose utterances we were working with before we encountered cur_linkable_seg
        self.last_linkable_seg = None
        
        #set up logging
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    ##Constructs a string that is formatted as indented list of information about all utterances in a given segment. This is useful to tack on to error messages.
    #  @param self
    #  @param seg (Segment) segment object for which to generate a list of utterance info
    #  @returns (string) an indented string containing speaker, start/end times, lena notes, transcription phrase, transcriber codes, etc. for each utterance in the segment.
    def _get_seg_contents(self, seg):
        contents = ''
        for utter in seg.utters:
            codes_str = ''
            if utter.lena_codes:
                codes_str += '|%s|' % ('|'.join(utter.lena_codes))
            if utter.trans_codes:
                codes_str = '|%s|' % ('|'.join(utter.trans_codes))
                                      
            contents += '\t%s [%s - %s] %s%s%s\n' % (utter.speaker.speaker_codeinfo.code if utter.speaker else '-',
                                                     BackendUtils.get_time_str(utter.start),
                                                     BackendUtils.get_time_str(utter.end),
                                                     (utter.lena_notes or '') + ' ',
                                                     (utter.trans_phrase or '') + ' ',
                                                     codes_str,
                                                     )
            
        return contents

    ## Drives the state machine ahead on step.
    #  @param self
    #  @param next_obj (Utterance) the next Utterance to consider in the linking process
    def drive(self, next_obj):
        #we only drive the state machine for utterances that are linkable, and have been transcribed
        #if next_obj.is_linkable() and next_obj.trans_phrase:
        if next_obj.trans_phrase:

            #if we've moved beyond a segment boundary (i.e. next_obj is the first utterance of a new segment), some maintanence work needs to be done on the data structures
            if self.cur_linkable_seg == None or self.cur_linkable_seg.num != next_obj.seg.num:

                #Any utterances whose link numbers are left in the 'prev_links' sub-dictionary are now too far away from their originating segment to be linked. (eg. they are from segment 2, and we are now starting segment 4 - therefore matching C/IC codes were not found in segment 3). Therefore, we generate errors for each of them.
                for link_num in self.link_dict['prev_links']:
                    err_msg = 'Encountered I%s with no C%s in next linkable segment.\n' % tuple([str(link_num or '')] * 2)
                    err_msg += 'Expected a \'C\' in either the current segment, or one of the these (following) segments:\n'
                    err_msg += self._get_seg_contents(self.cur_linkable_seg)
                        
                    self.trs_parser.error_collector.add(ParserError(err_msg, self.link_dict['prev_links'][link_num]))

                #update the last/cur linkable segments
                self.last_linkable_seg = self.cur_linkable_seg
                self.cur_linkable_seg = next_obj.seg

                #replace the 'prev_links' sub-dictionary (has outdated entries from 2 segments ago) with the 'cur_links' sub-dictionary (now has entries from 1 segment ago)
                self.link_dict['prev_links'] = self.link_dict['cur_links']
                #reset the 'cur_links' sub-dictionary so we can enter link numbers for utterances from the new segment
                self.link_dict['cur_links'] = {}

            
            continued_match = None #this will be set to a regex match object if next_obj contains an I transcriber code (note: could be IC)
            continuation_match = None #this will be set to a regex match object if next_obj contains a C transcriber code (note: could be IC)
            continued_num = '' #if continued_match is non-None, this will be set to the link number
            continuation_num = '' #if continuation_match is non-None, this will be set to the link number

            #make sure the Utterance has transcriber codes, then set the 'match' variables
            if len(next_obj.trans_codes) == len(DBConstants.TRANS_CODES):
                continued_match = re.search('(?:I(\d+)?)', next_obj.trans_codes[2])
                continuation_match = re.search('(?:C(\d+)?)', next_obj.trans_codes[2])

            #determine the link numbers for any matches
            continued = hasattr(continued_match, 'group') #this is a boolean - True if continued_match is non-None
            if continued:
                #if no number is present, use a 0 (i.e. match is just 'I' or 'IC')
                continued_num = continued_match.groups()[0] or 0

            continuation = hasattr(continuation_match, 'group') #this is a boolean - True if continuation_match is non-None
            if continuation:
                #if no number is present, use a 0 (i.e. match is just 'C' or 'IC')
                continuation_num = continuation_match.groups()[0] or 0

            #Note: if the utterance has an 'IC' code, it is possible that both continued and continuation are True at this point

            #if there was a C code (or an IC code), search for a matching 'I' code
            if continuation:
                #the 'prev_links' sub-dict holds the continued utterances from last linkable segment - looking for a matching 'I' code there
                if continuation_num in self.link_dict['prev_links']:
                    #remove (pop) the matching I/IC code from the 'prev_links' sub-dict
                    prev_obj = self.link_dict['prev_links'].pop(continuation_num)
                    
                    #set the utterance pointers on both objects
                    prev_obj.next = next_obj
                    next_obj.prev = prev_obj

                #if it's not in prev_links, check cur_links (allow links to occur within the same turn)
                elif continuation_num in self.link_dict['cur_links']:
                    #remove (pop) the matching I/IC code from the 'cur_links' sub-dict
                    prev_obj = self.link_dict['cur_links'].pop(continuation_num)
                    
                    #set the utterance pointers on both objects
                    prev_obj.next = next_obj
                    next_obj.prev = prev_obj
                    
                #if we didn't find a matching I code, generate an error
                else:
                    err_msg = 'Encountered C%s code with no I%s code in previous linkable segment.\n' % tuple([str(continuation_num or '')] * 2)
                    if self.last_linkable_seg:
                        err_msg += 'Expected an \'I\' either previously in the current segment, or in one of these (previous) segments:\n'
                        err_msg += self._get_seg_contents(self.last_linkable_seg)
                    
                    self.trs_parser.error_collector.add(ParserError(err_msg, next_obj))
                    

            #if there was an I code (or an IC code), insert the link number into the 'cur_links' sub-dictionary
            if continued:
                #first check if it's aready in the sub-dictionary. If so, we've encountered it before in this segment - therefore generate an 'ambiguous Is' error.
                if continued_num in self.link_dict['cur_links']:
                    self.trs_parser.error_collector.add(ParserError('Ambiguous I%s in segment.' % (str(continued_num or '')), next_obj))
                #otherwise, we're good to insert it
                else:
                    self.link_dict['cur_links'][continued_num] = next_obj

    ## This method ensures that errors are generated for any utterances that are still waiting around for a link.
    #  This routine must be called after drive() - otherwise, you'll (potentially) be missing some errors.
    #  @param self
    def finish(self):
        #Any link numbers left in the 'cur_links' sub-dict are waiting for future utterances with corresponding C codes. They won't get any, since there are no more Utterances to process.
        #Therefore they are all 'I without C' errors.
        for link_num in self.link_dict['cur_links']:
            self.trs_parser.error_collector.add(ParserError('Encountered I%s with no C%s in next segment.' % tuple([str(link_num or '')] * 2), self.link_dict['cur_links'][link_num]))

        #Any link numbers left in the 'prev_links' sub-dict are for 'IC' codes that were not popped because no match could be found.
        for link_num in self.link_dict['prev_links']:
            #self.trs_parser.error_collector.add(ParserError('Encountered C%s with no previous I%s code.'  % tuple([str(link_num or '')] * 2), self.link_dict['prev_links'][link_num]))
            self.trs_parser.error_collector.add(ParserError('Encountered I%s with no following C%s code.'  % tuple([str(link_num or '')] * 2), self.link_dict['prev_links'][link_num]))
