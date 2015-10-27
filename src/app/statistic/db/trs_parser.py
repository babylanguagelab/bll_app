import xml.etree.ElementTree
import re

from bll_database import BLLConstants
from speaker import Speaker
from segments import Segment
from utterance import Utterance
from state_machines import ParseUttersStateMachine
from debug import myDebug as de

# from parsers.errors import *
# from data_structs.error_collector import ErrorCollector
# from parsers.parser_tools import *


class TRSParser():
    def __init__(self, filename):
        self.filename = filename
        self.segments = []
        self.speakers = {}
        self.utter_index = {}
        # self.link_sm = LinkUttersStateMachine(self)
        self.totautters = 0
        self.tree = xml.etree.ElementTree.parse(self.filename)

    def parse(self):
        if self.tree:
            self.parse_speakers()

            # grab all turns in the current section element
            turn_list = list(self.tree.iter('Turn'))
            total_turns = len(turn_list)

            # iterate through turns, pulling out utterances
            for turn_num in range(total_turns):
                # all of the speakers in this segment
                # some turns have no speakers
                if 'speaker' not in turn_list[turn_num].attrib:
                    seg_speakers = []
                else:
                    seg_speakers = map(lambda spkr_id: self.speakers[spkr_id],
                                       turn_list[turn_num].attrib['speaker'].split(' '))

                # construct the segment object
                seg = Segment(turn_num,
                              float(turn_list[turn_num].attrib['startTime']),
                              float(turn_list[turn_num].attrib['endTime']),
                              seg_speakers)

                seg.utters = self.parse_utters(seg, turn_list[turn_num])

                # make sure this isn't a segment that the user has requested be filtered out
                if ParserTools.include_seg(seg, seg_filters):
                    # append the newly created segment object to the internal list of segments
                    self.segments.append(seg)

            self.link_sm.finish()

            self.parsed = True
            # free memory
            self.tree = None

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

    def parse_utters(self, seg, turn):
        # this state machine handles Utterance creation and assigns
        # their start/end times as we go through the sub-elements in the turn
        sm = ParseUttersStateMachine(self, seg)

        for el in turn.iter():
            sm.drive(el)

        sm.finish(turn)

        return sm.get_result()

    def parse_speech_data(self, seg, el):
        utter_list = []
        text = el.tail.strip()
        if text:
            # split up separate lines
            speaker_utters = re.split('\s*\n\s*', text)

            # each line is treated as a separate utterance
            for i in range(len(speaker_utters)):
                # split at the '.' operator, if present.
                # Transcribers use this to "split apart" segments that
                # LENA has mistakenly put together.
                if (re.search(r'\s*\.\s*', speaker_utters[i]) is not None):
                    have_multi_utters = True
                multi_utters = re.split(r'\s*\.\s*', speaker_utters[i])
                for j in range(len(multi_utters)):
                    utter = Utterance()
                    utter.seg = seg
                    utter.is_dot_split = have_multi_utters
                    self.total_utters += 1

                    # First line has the speaker indicated by LENA.
                    # Subsequent lines are considered to be other speakers.
                    if i == 0:
                        self.assign_speaker(el, utter)

                    self._assign_utter_attribs(utter, multi_utters[j], remove_bad_trans_codes)

                    utter_list.append(utter)
        # If the <sync> tag was not transcribed, just create an empty Utterance for it
        else:
            utter = Utterance()
            utter.seg = seg
            if seg.speakers:
                #assume first speaker for now...
                utter.speaker = seg.speakers[0]
            self.total_utters += 1
            utter_list.append(utter)

        return utter_list

    def assign_speaker(self, el, utter):
        if el.tag == 'Sync':
            utter.speaker = utter.seg.speakers[0]
            # For "who" tags, we need to examine the 'nb' attribute.
            # This gives the index (starts at 1) of in this segment.
        elif el.tag == 'Who':
            speaker_index = int(el.attrib['nb']) - 1
            # sometimes there's human error
            # and we do not have enough speakers in the enclosing segment
            if speaker_index < len(utter.seg.speakers):
                utter.speaker = utter.seg.speakers[speaker_index]

    def assign_utter_attribs(self, utter, line):
        RE_PHRASE = '^\s*([^\|]*?)\s*('
        RE_LENA_CODES = '|'.join(BLLConstants.LENA_NOTES_CODES.get_all_options_codes())
        RE_TRANS_CODES = ')?\s*(?:\|(.*)\|)?\s*$'
        # General format: "<transcription phrase>
        #                  <lena notes>
        #                  <pipe-delimited LENA codes>
        #                  <pipe-delimited transcriber codes>"
        TRANS_LINE_REGEX = RE_PHRASE + RE_LENA_CODES + RE_TRANS_CODES
        # this regex is used to check for angle brackets to see
        # if a particular transcription should be marked as 'overlapping'
        TRANS_OVERLAP_REGEX = '\s*<.*>\s*'

        if (line):
            match = re.search(TRANS_LINE_REGEX, line)
            utter.trans_phrase = ''
            utter.lena_notes = ''
            codes = ''
            try:
                utter.trans_phrase = match.groups()[0] or ''
                if (utter.trans_phrase):
                    utter.is_trans_overlap = re.search(TRANS_OVERLAP_REGEX,
                                                       utter.trans_phrase)
                utter.lena_notes = match.groups()[1] or ''
                codes = match.groups()[2] or ''
            except Exception:
                de('Found invalid transcription line in TRS file:', line)

            if codes:
                codes_list = codes.split('|')

                utter.lena_codes = codes_list[0: len(codes_list) - 4]
                utter.trans_codes = codes_list[len(codes_list) - 4:]

                self.link_sm.drive(utter)

    def parse_speakers(self):
        for person in self.tree.getroot().find('Speakers').findall('Speaker'):
            speaker_id = person.attrib['id'].strip()
            speaker_name = person.attrib['name'].strip()
            speaker_code = BLLConstants.SPEAKER_CODES.get_option(speaker_name)
            self.speakers[speaker_id] = Speaker(speaker_id, speaker_code)

            if self.speakers[speaker_id].codeinfo is None:
                de('Unrecognized speaker code: ', speaker_name)
            else:
                self.speakers[speaker_id] = Speaker(speaker_id, speaker_code)

mParser = TRSParser('C002_20090619_FINAL.trs')
mParser.parse()
