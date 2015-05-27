## @package parsers.trs_parser

import xml.etree.ElementTree
import logging
import re
import traceback
import random

from data_structs.segment import Segment
from data_structs.utterance import Utterance
from data_structs.speaker import Speaker
from db.bll_database import DBConstants
from parsers.state_machines import *
from parsers.errors import *
from data_structs.error_collector import ErrorCollector
from parsers.parser_tools import *

## This class parses transcribed (or untranscribed) TRS files, producing output in the form of Segment objects (which contain Utterance objects).
#  The tasks of assigning Utterance start/end times and linking segments into chains are passed off to the parsers.state_machines.StateMachines class.
class TRSParser(object):
    #every correctly transcribed line should match this regex
    #General format: "<transcription phrase> <lena notes> <pipe-delimited LENA codes><pipe-delimited transcriber codes>"
    TRANS_LINE_REGEX = '^\s*([^\|]*?)\s*(' + '|'.join(DBConstants.LENA_NOTES_CODES.get_all_options_codes()) + ')?\s*(?:\|(.*)\|)?\s*$'
    
    #this regex is used to check for angle brackets to see if a particular transcription should be marked as 'overlapping'
    TRANS_OVERLAP_REGEX = '\s*<.*>\s*'

    ## Constructor
    #  @param self
    #  @param filename (string) full path to TRS file to parse
    def __init__(self, filename):
        self.logger = logging.getLogger(__name__)
        self.filename = filename

        #perform setup of data structures used in the parsing process
        self._init_data_structures()

    ## Sets up data structures used to iterate through the XML and track segments, utterances, errors, etc.
    #  @param self
    def _init_data_structures(self):
        self.error_collector = ErrorCollector()
        self.segments = []
        self.speakers = {}
        self.utter_index = {} #for lookup by utter_id, only build on demand
        self.parsed = False
        self.link_sm = LinkUttersStateMachine(self)
        self.total_utters = 0
        self.tree = None

        #Use Python ElementTree library to parse the XML in the TRS file.
        try:
            self.tree = xml.etree.ElementTree.parse(self.filename)
            
        except Exception as e:
            self.logger.error("Unable to open TRS file. Exception: %s" % e)
            self.logger.error("Stack trace: %s" % (traceback.format_exc()))

    ## Retreives the errors and warnings found by this parser in the form of an ErrorCollector object
    #  It provides methods to look up various errors/warnings by type.
    #  @param self
    #  @returns (ErrorCollector) - this object can be used to lookup errors/warnings by type (see errors.ErrorCollector class)
    def get_errors(self):
        return self.error_collector

    ## Resets internal data structures and parses the TRS file a second time. Useful if the file has changed since the last parse.
    #  All cached segments/utterances from the last parse are cleared.
    #  @param self
    #  @param progress_update_fcn (function=None) function accepting a value in [0,1] to display as a progress bar - see utils.ProgressDialog. This value is used to indicate the level of completeness <em>of the current phase</em>
    #  @param progress_next_phase_fcn(function=None) - moves the progress bar to the next phase, which causes new text to be displayed in the bar - see utils.ProgressDialog
    #  @param validate (boolean=True) set to True if you want the parser to check for errors (can be retreived with get_errors()), False otherwise
    #  @param seg_filters (list=[]) list of SegFilter objects. These filters are applied to the segments list in a permanent manner (i.e. anything they filter out will not be returned by this parser)
    #  @returns (list) list of Segment objects
    def re_parse(self, progress_update_fcn=None, progress_next_phase_fcn=None, validate=True, seg_filters=[], remove_bad_trans_codes=True):
        self._init_data_structures()
        
        return self.parse(progress_update_fcn=progress_update_fcn,
                          progress_next_phase_fcn=progress_next_phase_fcn,
                          validate=validate,
                          seg_filters=seg_filters,
                          remove_bad_trans_codes=remove_bad_trans_codes)

    ## Parses the TRS file, returning a list of Segments.
    #  @param self
    #  @param progress_update_fcn (function=None) function accepting a value in [0,1] to display as a progress bar - see utils.ProgressDialog. This value is used to indicate the level of completeness <em>of the current phase</em>
    #  @param progress_next_phase_fcn(function=None) - moves the progress bar to the next phase, which causes new text to be displayed in the bar - see utils.ProgressDialog
    #  @param validate (boolean=True) set to True if you want the parser to check for errors (can be retreived with get_errors()), False otherwise
    #  @param seg_filters (list=[]) list of SegFilter objects. These filters are applied to the internal segments list in a permanent manner (i.e. anything they filter out will not be returned by this parser)
    #  @returns (list) list of Segment objects
    def parse(self, progress_update_fcn=None, progress_next_phase_fcn=None, validate=True, seg_filters=[], remove_bad_trans_codes=True):
        #make sure the xml was readable, and results have not yet been cached
        if self.tree and not self.parsed:
            #parse the file, driving the linking state machine as we go
            self._parse(progress_update_fcn, seg_filters, remove_bad_trans_codes)
            self.link_sm.finish()

            #validate the utterances, if requested
            if validate:
                if progress_next_phase_fcn:
                    progress_next_phase_fcn()

                cur_utter = 0
                for seg in self.segments:
                    for utter in seg.utters:
                        #log errors to the collector object
                        utter.validate(self.error_collector)
                        cur_utter += 1

                        if progress_update_fcn:
                            progress_update_fcn(float(cur_utter) / float(self.total_utters))
            
            self.parsed = True
            self.tree = None #no need to keep this huge object in memory anymore...

        return self.segments

    ## Retreives an Utterance object (residing in one of this trs parser's segments) by its utterance id attribute.
    #  @param self
    #  @param utter_id (int) utterance id to search for
    #  @returns (Utterance) the requested Utterance object, or None if not found
    def get_utter_by_id(self, utter_id):
        result = None

        #build an index (keyed by utterance id) so that these acceses will be faster in the future
        #note: this only involves copying pointers, not actual data...
        if not self.utter_index:
            self.parse()
            self.utter_index = {}
            for seg in self.segments:
                for utter in seg.utters:
                    self.utter_index[utter.id] = utter

        if utter_id in self.utter_index:
            result = self.utter_index[utter_id]

        return result
    
    ## This method performs the actual parsing work that produces a list of Segment objects from the XML.
    #  @param self
    #  @param progress_update_fcn (function) see identical parameter description in parse()
    #  @param seg_filters (list) list of SegFilter objects to apply to the segments as they are created. Anything that these filters exclude will not be in the returned list (their changes are made permanent).
    #  @returns (list) list of Segment objects
    def _parse(self, progress_update_fcn, seg_filters, remove_bad_trans_codes):
        #make sure xml was readable
        if self.tree:
            #retrieve a dictionary of speakers from the xml file and store it in self.speakers
            self._parse_speakers()

            #grab all turns in the current section element
            turn_list = list(self.tree.iter('Turn'))
            total_turns = len(turn_list)

            #iterate through turns, pulling out utterances
            for turn_num in range(total_turns):
                #build a list of Speaker objects representing all of the speakers in this segment
                if not 'speaker' in turn_list[turn_num].attrib: #some turns have no speakers
                    seg_speakers = []
                else:
                    seg_speakers = map(lambda spkr_id: self.speakers[spkr_id], turn_list[turn_num].attrib['speaker'].split(' '))

                #construct the segment object
                seg = Segment(turn_num,
                              float(turn_list[turn_num].attrib['startTime']),
                              float(turn_list[turn_num].attrib['endTime']),
                              seg_speakers)

                #parse the utterances out of this turn element and store them in the segment
                seg.utters = self._parse_utters(seg, turn_list[turn_num], remove_bad_trans_codes)

                #make sure this isn't a segment that the user has requested be filtered out
                if ParserTools.include_seg(seg, seg_filters):
                    #append the newly created segment object to the internal list of segments
                    self.segments.append(seg)

                #update any progress bars, if present
                if progress_update_fcn:
                    progress_update_fcn(float(turn_num + 1) / float(total_turns))

    ## Creates Utterance objects for a given XML turn element.
    #  @param self
    #  @param seg (Segment) the parent Segment object
    #  @param turn (Element) an etree.Element object representing the XML node
    #  @returns (list) list of Utterance objects
    def _parse_utters(self, seg, turn, remove_bad_trans_codes):
        #this state machine handles Utterance creation and assigns their start/end times as we go through the sub-elements in the turn node
        sm = ParseUttersStateMachine(self, seg, remove_bad_trans_codes)
        
        #advance the state machine for each sub-element in the turn node
        for el in turn.iter():
            sm.drive(el)
            
        #perform any final end time assignments
        sm.finish(turn)

        #grab a list of Utterances from the state machine and return it
        return sm.get_result()

    ## Extracts Utterance attributes (eg. transcriber codes, transcription phrase, etc.) from the text following a <sync> element.
    #  @param self
    #  @param seg (Segment) A Segment object that Utterances created from this text should appear within.
    #  @param el (etree Element) An XML "text element" from the etree library, containing the data immediately following a <sync> tag. This may span multiple lines.
    #  @returns (list) List of Utterance objects with their attributes set. Multiple Utterance objects are created from the text if it spans multiple lines (different speakers) or uses the '.' operator (see the transcriber manual).
    def _parse_speech_data(self, seg, el, remove_bad_trans_codes):
        utter_list = []
        text = el.tail.strip()
        if text:
            #split up separate lines
            speaker_utters = re.split('\s*\n\s*', text)

            #each line is treated as a separate utterance, since (according to the transcriber manual) new lines are used for different speakers
            for i in range(len(speaker_utters)):
                #split at the '.' operator, if present. Transcribers use this to "split apart" segments that LENA has mistakenly put together.
                have_multi_utters = re.search(r'\s*\.\s*', speaker_utters[i]) != None
                multi_utters = re.split(r'\s*\.\s*', speaker_utters[i])
                for j in range(len(multi_utters)):
                    utter = Utterance()
                    utter.seg = seg
                    utter.is_dot_split = have_multi_utters
                    self.total_utters += 1
                    
                    #First line has the speaker indicated by LENA. Subsequent lines are considered to be other speakers.
                    if i == 0:
                        self._assign_speaker(el, utter)

                    self._assign_utter_attribs(utter, multi_utters[j], remove_bad_trans_codes)

                    utter_list.append(utter)
        #If the <sync> tag was not transcribed, just create an empty Utterance for it
        else:
            utter = Utterance()
            utter.seg = seg
            if seg.speakers:
                #assume first speaker for now...
                utter.speaker = seg.speakers[0]
            self.total_utters += 1
            utter_list.append(utter)

        return utter_list

    ## Determines the speaker for an Utterance, and sets the Utterance speaker attribute to an appropriate Speaker object.
    #  @param self
    #  @param el (etree Element object) The XML element (with either a "sync" or a "who" tag) that corresponds to utter
    #  @param utter (Utterance) The Utterance object to assign a speaker to
    def _assign_speaker(self, el, utter):
        #"sync" tags receive the enclosing segment's speaker, if any
        if el.tag == 'Sync':
            utter.speaker = utter.seg.speakers[0] if len(utter.seg.speakers) > 0 else None
        #For "who" tags, we need to examine the 'nb' attribute. This gives the index (starts at 1) of the speaker in the enclosing segment's speaker list.
        elif el.tag == 'Who':
            speaker_index = int(el.attrib['nb']) - 1
            #sometimes there's human error and we do not have enough speakers in the enclosing segment
            if speaker_index < len(utter.seg.speakers):
                utter.speaker = utter.seg.speakers[speaker_index]

    ## Performs the actual assignment of utterance attributes (like transcription phrase, codes, etc.), based upon a line from the TRS file.
    #  @param self
    #  @param utter (Utterance) the object we are assigning attributes to
    #  @param line (string) the text following a "sync" or "who" element. This contains LENA codes, plus transcriber added data (and more)
    def _assign_utter_attribs(self, utter, line, remove_bad_trans_codes):
        #sometimes there is no data...
        if (line):
            #grab the data using regex capturing groups
            match = re.search(TRSParser.TRANS_LINE_REGEX, line)
            #the above match "should" never fail (the regex will match anything), but it may not capture groups if the corresponding text isn't present. Therefore we assign them carefully.
            utter.trans_phrase = ''
            utter.lena_notes = ''
            codes = ''
            try:
                utter.trans_phrase = match.groups()[0] or '' #change None into empty string
                utter.is_trans_overlap = re.search(TRSParser.TRANS_OVERLAP_REGEX, utter.trans_phrase) != None
                utter.lena_notes = match.groups()[1] or ''
                codes = match.groups()[2] or ''
            except Exception as err:
                self.logger.error('Found invalid transcription line in TRS file: %s' % line)

            #assign any codes using another regex
            if codes:
                codes_list = re.findall('[^\|]+', codes)

                #These have been verified through TRANS_LINE_REGEX.
                lena_codes = codes_list[0: len(codes_list) - 4]
                #These have not.
                #We assume last 4 codes are transcriber codes, setting invalid ones to empty
                #string if the remove_bad_trans_codes flag is set.
                trans_codes = codes_list[len(codes_list) - 4:]

                if remove_bad_trans_codes:
                    for i in range(len(trans_codes)):
                        code = trans_codes[i]
                        pattern = '^[%s]$' % (''.join(DBConstants.TRANS_CODES[i].get_all_options_codes()))

                        #code 2 can have multiple chars, with numbers (I1, C1, etc.)
                        if i == 2:
                            pattern = '^([%s][1-9]?)+$' % (''.join(DBConstants.TRANS_CODES[i].get_all_options_codes()))
                            
                        if not re.match(pattern, code):
                            trans_codes[i] = ''

                utter.lena_codes = lena_codes
                utter.trans_codes = trans_codes

                #let the state machine know that we've got this data (this method should really be refactored so that this line can be moved to state_machines.py, where it belongs...)
                self.link_sm.drive(utter)

    ## Grabs a list of all of the speakers in the TRS file, from the <Speakers> tag (which appears near the top). Creates Speaker objects for them and stores them in the self.speakers list.
    #  @param self
    def _parse_speakers(self):
        if not self.speakers:
            for person in self.tree.getroot().find('Speakers').findall('Speaker'):
                speaker_id = person.attrib['id'].strip()
                speaker_code = person.attrib['name'].strip()
                self.speakers[speaker_id] = Speaker(speaker_id, DBConstants.SPEAKER_CODES.get_option(speaker_code))
                if self.speakers[speaker_id].speaker_codeinfo == None: #indicates speaker code is not in the DB table
                    self.logger.error('Unrecognized speaker code: %s' % (speaker_code))
