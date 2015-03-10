import xml.etree.ElementTree as etree
import logging
import traceback
import re

from data_structs.segment import Segment
from data_structs.utterance import Utterance
from data_structs.speaker import Speaker
from db.bll_database import DBConstants

#note: there is no transcriber information or validation to worry about here
class ITSParser(object):
    def __init__(self, filename):
        self.logger = logging.getLogger(__name__)
        self.filename = filename
        self.segments = []
        self.parsed = False

        try:
            self.tree = etree.parse(self.filename)
            
        except Exception as e:
            self.logger.error('Unable to parse ITS file. Exception: %s' % e)
            self.logger.error('Stack trace: %s' % (traceback.format_exc()))

    def parse(self):
        if self.tree and not self.parsed:
            rec_it = self.tree.iter('Recording')

            for rec in rec_it:
                children = rec.getchildren()
                for i in range(len(children)):
                    seg = self._build_seg(i, children[i])
                    self.segments.append(seg)

            self.parsed = True

        return self.segments

    def _parse_time(self, time_str):
        match = re.match(r'^PT(.*)S$', time_str)
        return float(match.groups()[0])
        
    #el is either a "Converstion" or "Pause" element
    def _build_seg(self, num, el):
        start = self._parse_time(el.attrib['startTime'])
        end = self._parse_time(el.attrib['endTime'])

        seg = Segment(
            num,
            start,
            end,
        )

        seg_utters = []
        seg_spkrs = {}
        it = el.iter('Segment')
        for child_el in it:
            utter = self._build_utter(child_el, seg)
            seg_utters.append(utter)
            seg_spkrs[utter.speaker.speaker_codeinfo.code] = utter.speaker

        seg.utters = seg_utters
        seg.speakers = seg_spkrs.values()
        
        return seg

    #el is a "Segment" element
    def _build_utter(self, el, seg):
        start = self._parse_time(el.attrib['startTime'])
        end = self._parse_time(el.attrib['endTime'])
        spkr_cd = el.attrib['spkr']
        codeinfo = DBConstants.SPEAKER_CODES.get_option(spkr_cd)
        speaker = Speaker(None, codeinfo) #ITS files have no speaker_id (e.g. 'spk1') like TRS files do
        
        utter = Utterance()
        utter.start = start
        utter.end = end
        utter.speaker = speaker
        utter.lena_notes = None #don't have access to this info in ITS

        if 'recordingInfo' in el.attrib and len(el.attrib['recordingInfo']) > 1:
            utter.lena_codes.extend(el.attrib['recordingInfo'][1:-1].split('|'))

        if 'conversationInfo' in el.attrib and len(el.attrib['conversationInfo']) > 1:
            utter.lena_codes.extend(el.attrib['conversationInfo'][1:-1].split('|'))
        
        utter.seg = seg

        return utter
        
