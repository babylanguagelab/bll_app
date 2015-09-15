## @package parsers.trs_splitter

import traceback
from xml.etree import ElementTree
import logging
import re
import os
from utils.backend_utils import BackendUtils

## This class splits a TRS file into chunks of a given length, writing the split files to a user-specified directory.
class TRSSplitter(object):
    ## Constructor
    #  @param self
    #  @param filename (string) name of the TRS file to split (absolute path)
    #  @param dest_path (string) directory in which to store the split TRS files (absolute path)
    def __init__(self, filename, dest_path):
        self.logger = logging.getLogger(__name__)
        self.dest_path = dest_path
        #grab the portion of the filename between the path prefix or the extension
        self.filename_base = re.match('.*[\\\/]([^\\\/]+)\.[Tt][Rr][Ss]$', filename).groups()[0]
        self.filename = filename

        try:
            self.tree = ElementTree.parse(self.filename)
            
        except Exception as e:
            self.logger.error("Unable to open TRS file. Exception: %s" % e)
            traceback.print_exc()

    ## Speakers are given string ids 'spk0', 'spk1', etc. This method retreives the integer from the next available id.
    #  @param self
    #  @returns (int) next available id for a Speaker
    def _get_next_speaker_num(self):
        max_speaker_num = -1
        for person in self.tree.getroot().find('Speakers').findall('Speaker'):
            cur_speaker_num = int( re.match('^spk(\d+)$', person.attrib['id']).groups()[0] )
            max_speaker_num = max(max_speaker_num, cur_speaker_num)

        return max_speaker_num + 1

    ## Inserts a speaker with code 'VOID' into the xml file. This speaker is used to pad the start and end of the file (from time 0 to start of first segment, and from end of last segment to end of file time). This is done so that whent he split file is opened in transcriber, the wav file will still sync up. This method modifies the "Speakers" tag at the top of a TRS file. This tag contains a list of all the speakers in the file. Nothing is returned - instead, the tree param is directly modified.
    #  @param self
    #  @param tree (etree ElementTree) The XML tree in which to search for the speakers tag
    #  @param speaker_num (int) the number for the new VOID speaker (should be unused by other speakers already present) - see _get_next_speaker_num()
    def _insert_void_speaker(self, tree, speaker_num):
        speakers = tree.getroot().find('Speakers')
        speakers.append(ElementTree.Element('Speaker', attrib={'accent': '',
                                                               'check': 'no',
                                                               'dialect': 'native',
                                                               'id': 'spk%d' % (speaker_num),
                                                               'name': 'VOID',
                                                               'scope': 'local',
                                                               }))

    ## Constructs a string in the format "hh:mm:ss.ss" from a total seconds count.
    #  @param self
    #  @param total_sec (float) The total second count to convert the the specified format
    #  @returns (string) the formatted result, as indicated above
    def _get_time_str(self, total_sec):
        hours, mins, sec = BackendUtils.break_time(total_sec)

        return '%02d_%02d_%s%0.2f' % (hours, mins, '0' if sec < 10 else '', sec)

    ## Splits the TRS file. This will write to the destination file.
    #  @param self
    #  @param win_len (float) The size of the chunks we want to split this file into (specified in seconds)
    #  @param progress_update_fcn (function=None) function that updates the progress bar, accepting a single parameter, a real number in [0.0, 1.0]
    def split(self, win_len, progress_update_fcn=None):
        void_speaker_num = self._get_next_speaker_num()
        sections = list(self.tree.iter('Section'))
        file_num = 0
        i = 0;

        while i < len(sections):
            new_episode, i, start_time, end_time = self._build_episode(sections, i, win_len, void_speaker_num, progress_update_fcn)
            
            temp_tree = ElementTree.parse(self.filename)
            self._insert_void_speaker(temp_tree, void_speaker_num)
            
            trans = temp_tree.getroot()
            old_episode = trans.find('Episode')
            trans.remove(old_episode)
            trans.append(new_episode)

            start_str = str(start_time).replace('.', '_')
            end_str = str(end_time).replace('.', '_')
            dest_filename = '%s\\%s-[%s-%s]-%d.trs' % (self.dest_path, self.filename_base, self._get_time_str(start_time), self._get_time_str(end_time), file_num)
            
            #python ElementTree library isn't adding xml declaration (bug), so we have to add it ourselves
            dest_file = open(dest_filename, 'wb')
            dest_file.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n') #this is not really true, but it works for now...
            dest_file.write('<!DOCTYPE Trans SYSTEM "trans-14.dtd">\n')
            dest_file.close()
            dest_file = open(dest_filename, 'a')
            temp_tree.write(dest_file, xml_declaration=False)
            dest_file.close()

            file_num += 1

    ## Constructs a section element (with a turn subelement) for the void speaker, for the specified time period.
    #  @param start_time (float) section start time, in seconds (specified as offset from beginning of file)
    #  @param end_time (float) section end time, in seconds (specified as offset from beginning of file)
    #  @param speaker_num (int) next available speaker integer - see _get_next_speaker_num()
    #  @returns (Element) etree "section" Element for the void speaker
    def _get_void_section(self, start_time, end_time, speaker_num):
        void_section = ElementTree.Element('Section', attrib={'startTime': str(start_time), 'endTime': str(end_time), 'type': 'report'})
        void_turn = ElementTree.SubElement(void_section, 'Turn', attrib={'startTime': str(start_time), 'endTime': str(end_time), 'speaker': 'spk%d' % (speaker_num)})

        return void_section

    ## Each TRS file contains a single <episode> tag that encloses all <turn> tags. This method constructs a new <episode> tag containing as many sections as will fit into the time period specified by win_len. This can be used to write a new TRS file. If a single section is bigger than win_len, the section is appended separately as a single file.
    #  @param self
    #  @param start_offset (int) section index at which to start building the episode
    #  @param win_len (float) The size of the chunks we want to split this file into (specified in seconds)
    #  @param void_speaker_num (int) next available speaker integer - see _get_next_speaker_num()
    #  @param progress_update_fcn (function=None) function that updates the progress bar, accepting a single parameter, a real number in [0.0, 1.0]
    #  @returns (Element, int, float, float) New Episode XML element, index of the last segment we stuffed into it, start time of the first segment in the episode, end time of the last segment in the episode
    def _build_episode(self, sections, start_offset, win_len, void_speaker_num, progress_update_fcn): #win_len is the length of time (in sec) for each window
        new_episode = ElementTree.Element('Episode')
        
        i = start_offset
        start_seg_time = float(sections[i].attrib['startTime'])
        end_seg_time = float(sections[i].attrib['endTime'])
        limit_end_time = start_seg_time + win_len

        #add 'void' speaker between 0 and start_time of current section. This ensures the wav file is aligned when the split file is opened in transcriber.
        if start_seg_time > 0:
            void_section = self._get_void_section(0, start_seg_time, void_speaker_num)
            new_episode.append(void_section)
        
        while i < len(sections) and float(sections[i].attrib['endTime']) < limit_end_time:
            end_seg_time = float(sections[i].attrib['endTime'])
            new_episode.append(sections[i])
            i += 1
            
            if progress_update_fcn:
                progress_update_fcn(float(i) / float(len(sections)))

        if (i - start_offset) == 0 and i < len(sections) and float(sections[i].attrib['endTime']) >= limit_end_time:
            new_episode.append(sections[i])
            end_seg_time = float(sections[i].attrib['endTime'])
            i += 1
            
            if progress_update_fcn:
                progress_update_fcn(float(i) / float(len(sections)))

        src_file_end_time = float(sections[-1].attrib['endTime'])
        if end_seg_time < src_file_end_time:
            void_section = self._get_void_section(end_seg_time, src_file_end_time, void_speaker_num)
            new_episode.append(void_section)

        return new_episode, i, start_seg_time, end_seg_time

## Merges split files back into a single TRS file.
class TRSMerger(object):
    ## Constructor
    #  @param self
    #  @param src_dir (string) full path to the directory containing the split files
    def __init__(self, src_dir):
        self.src_dir = src_dir
        
        self.split_files = os.listdir(self.src_dir)
        self.split_files = filter(lambda name: re.match('.+?-\[\d+_\d+_\d+\.\d+-\d+_\d+_\d+\.\d+\]-\d+\.[Tt][Rr][Ss]$', name), self.split_files)
        
        self.split_files.sort(self._cmp_filenames)
        self.filename_base = re.match('^(.+?)-\[\d+_\d+_\d+\.\d+-\d+_\d+_\d+\.\d+\]-\d+\.[Tt][Rr][Ss]$', self.split_files[0]).groups()[0]

    ## Finds the id number of the VOID speaker that was inserted when the original TRS file was split (see TRSSplitter class)
    #  @param self
    #  @param tree (etree ElementTree) The XML tree object to search.
    #  @returns (int) the id of the void speaker, as determined from the "Speaker" tag (which lists all speakers in the file)
    def _get_void_speaker_id(self, tree):
        speakers = tree.getroot().find('Speakers').findall('Speaker')
        
        void_id = None
        i = 0
        while not void_id and i < len(speakers):
            if speakers[i].attrib['name'] == 'VOID':
                void_id = speakers[i].attrib['id']
            
            i += 1

        return void_id

    ## Removes the void speaker from the given XML tree.
    #  @param self
    #  @param tree (etree ElementTree) the XML tree to search
    def _remove_void_speaker(self, tree):
        speakers_el = tree.getroot().find('Speakers')
        speakers = speakers_el.findall('Speaker')
        
        found = False
        i = 0
        while not found and i < len(speakers):
            if speakers[i].attrib['name'] == 'VOID':
                speakers_el.remove(speakers[i])
                found = True
            
            i += 1

    ## Performs the acutal merger, writing the results to a destination file with the name "<old name>-merged.trs"
    #  @param self
    #  @param progress_update_fcn (function=None) function that updates the progress bar, accepting a single parameter, a real number in [0.0, 1.0]
    def merge(self, progress_update_fcn=None):
        new_episode = ElementTree.Element('Episode')
        num_split_files = len(self.split_files)
        void_speaker_id = None
        
        for i in range(num_split_files):
            tree = ElementTree.parse('%s\\%s' % (self.src_dir, self.split_files[i]))

            #void speaker id is the same for all split files, so only retreive it once
            if not void_speaker_id:
                void_speaker_id = self._get_void_speaker_id(tree)

            episode = tree.getroot().find('Episode')
            for child in episode:
                turn = child.find('Turn') #grab the first turn element - if the void speaker is present, it will always be in the first turn
                if not (child.tag == 'Section' and turn is not None and turn.attrib['speaker'] == void_speaker_id):
                    new_episode.append(child)

            if progress_update_fcn:
                progress_update_fcn(float(i + 1) / float(num_split_files))

        merged_tree = ElementTree.parse('%s\\%s' % (self.src_dir, self.split_files[0]))
        self._remove_void_speaker(merged_tree)
        
        trans = merged_tree.getroot()
        trans.remove(trans.find('Episode'))
        trans.append(new_episode)

        #python ElementTree library isn't adding xml declaration (bug), so we have to add it ourselves
        dest_filename = '%s\\%s-merged.trs' % (self.src_dir, self.filename_base)
        dest_file = open(dest_filename, 'wb')
        dest_file.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n') #this is not really true, but it works for now...
        dest_file.write('<!DOCTYPE Trans SYSTEM "trans-14.dtd">\n')
        dest_file.close()
        dest_file = open(dest_filename, 'a')
        merged_tree.write(dest_file, xml_declaration=False)
        dest_file.close()

    ## This comparison function is used to sort the split files into ascending order before they are merged. This is done using the index appended to the end of the filename by the splitter app.
    #  @param self
    #  @param x (string) filename number one
    #  @param y (string) filename number two
    #  @returns (int) 0 if names are identical, -1 if filename x should come before filename y, 1 if filename x should come after filename y
    def _cmp_filenames(self, x, y):
        result = 0
        
        match = re.match('.*?-(\d+)\.[Tt][Rr][Ss]$', x)
        x_num = int(match.groups()[0])

        match = re.match('.*?-(\d+)\.[Tt][Rr][Ss]$', y)
        y_num = int(match.groups()[0])
        
        if x_num < y_num:
            result = -1
        elif x_num > y_num:
            result = 1

        return result
        
