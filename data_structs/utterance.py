## @package data_structs.utterance

import re

from data_structs.base_objects import BLLObject
from db.bll_database import DBConstants
from parsers.errors import ParserError, ParserWarning

## This class represents an Utterance (though this class's representation may differ slightly from the linguistic definition). Utterances. For TRS files, an Utterance object corresponds to a single line of text following a "sync" or "who" tag. For CSV files, an Utterance object corresponds to a single row.
# Utterances are usually contained within a parent Segment object (corresponding to a "Turn" tag in a TRS file), and contain a pointer back to this parent Segment object. There may multiple utterances in a single Segment (see Segment.utters property), but each Utterance may only belong to one Segment.
#Utterances may be chained together (via transcriber C/I codes - see transcriber manual). Such a link is represented using the 'next' and 'prev' instance variables, which point to adjacent Utterances in the chain. These should never by linked circularly (i.e. it is impossible for a transcriber to code a circularly linked utterance).
# Unlike Segments, utterances are not stored in the database, and should never be manually constructed. Instead, they are generated by Parser objects (see parsers directory).

class Utterance(BLLObject):
    #This is a unique identifies that is given to each Utterance object. (This provides a simple way to index them within the Parser classes.)
    next_id = 0

    ## Constructor. Typically, this object is not constructed manually, so no parameters are provided. Instead, the parser objects create Utterances and set their parameters as they process a CSV/TRS file.
    #  @param self
    def __init__(self):
        self.speaker = None         #Speaker object, obtained from enclosing segment
        self.trans_phrase = None    #transcriber-written text (string) containing the words spoken in this utternace
        self.start = None           #absolute start time (float)
        self.end = None             #absolute end time (float)
        self.lena_notes = None      #(string) lena markings like "VOC" - see DBConstants.LENA_NOTES_CODES
        self.lena_codes = []        #(list of strings) lena generated codes
        self.trans_codes = []       #(list of strings) transcriber codes (see transcriber manual / DBConstants.TRANS_CODES
        self.next = None            #(Utterance or None) pointer to the next Utterance in the chain, if any
        self.prev = None            #(Utterance or None) pointer to the previous Utterence in the chain, if any
        self.is_trans_overlap = False #(boolean) True if this object represents was marked as overlapping by the transcribers using the angle brackets (<, >) - see transcriber manual
        self.seg = None               #(Segment) pointer to the enclosing Segment object
        self.is_dot_split = False
        self.id = Utterance.next_id   #(int) unique id for each object that's created
        
        Utterance.next_id += 1

    ## Gives a string-representation of this utterance. Also see superclass definition.
    #  @param
    #  @returns (string) a string with formatted info suitable for printing to the console
    def __str__(self):
        #print out all attributes, except for these
        output = BLLObject.__str__(self, ['next', 'prev', 'seg'])
        #Just print segment number (printing out whole segment would result in infinite recursion, since segment prints out this utterance)
        output += '-seg: %s\n' % (self.seg.num)
        
        #print out id of next/prev utterance in the chain, if present
        output += '-next: %s\n' % (str(self.next.id) if self.next else 'None')
        output += '-prev: %s\n' % (str(self.prev.id) if self.prev else 'None')

        return output

    ## Checks if this Utterance can be linked (chained via the next/prev instance vars) to other Utterances. This is used by the parsers when they go through a file. Utterances that represent silence, for example, should not be linked.
    #  @param self
    #  @returns (boolean) True if it's ok to link this Utterance, False otherwise
    def is_linkable(self):
        is_linkable = True

        #certain speakers (like silence) are not linkable. See the db table 'speaker_codes' (specifically, the 'is_linkable' column) for specific details.
        i = 0
        while is_linkable and i < len(self.seg.speakers):
            #if not self.seg.speakers[i].speaker_codeinfo:
            #    print self.seg.speakers[i].speaker_id
            is_linkable = self.seg.speakers[i].speaker_codeinfo.is_linkable
            i += 1

        #some lena notes are also used to mark silence. Utterances with these markings should not be linkable, unless they have been transcribed (i.e. unless lena was wrong to mark them as silence). See DBConstants.LENA_NOTES_CODES for specific details.
        notes_opt = DBConstants.LENA_NOTES_CODES.get_option(self.lena_notes)
        if is_linkable and notes_opt != None and not self.trans_phrase:
            is_linkable = notes_opt.is_linkable

        return is_linkable

    ## This method checks this Utterance for errors/warnings (e.g. invalid transcriber codes, ambiguous I/C codes, etc.). These are added to the error_collector object.
    #  @param self
    #  @param error_collector (ErrorCollector) An object used to organize and retreive errors in various ways (see data_structs.error_collector.py), so the UI can present them nicely. This method collects errors and adds them to this object.
    def validate(self, error_collector):
        warnings = []
        errors = []

        #if self.is_linkable(): #eliminates silence, media, nonverbal-noise, and other types that don't require transcription
        if self.trans_phrase:
            #note: for now, we don't validate the speaker, since it's not always possible to determine who's speaking with the transcriber multi-line schema

            #if not self.trans_phrase:
            #    error_collector.add(ParserWarning('Utterance has no transcription phrase.', self))
            #else:
            if self.trans_phrase:
                #search for invalid character in trascription phrase
                #replace angle bracket alternative encodings
                self.trans_phrase.replace('&lt;', '<').replace('&gt;', '>')
                bad_chars = re.findall('[^A-Za-z\'\"\<\>\s\^]', self.trans_phrase)
                #remove duplicates
                bad_chars = dict(zip(bad_chars, [True] * len(bad_chars))).keys()
                
                if bad_chars:
                    bad_chars_str = reduce(lambda accum, c: '%s, "%c"' % (accum, c),
                                           bad_chars[1:],
                                           '"%c"' % (bad_chars[0]))
                    error_collector.add(ParserError('Transcription phrase contains the following invalid characters: %s' % (bad_chars_str), self))
                
            #this can happen if the TRS file's XML structure gets messed up
            if self.start == None:
                error_collector.add(ParserError('Parser was unable to determine utterance start time.', self))
            if self.end == None:
                error_collector.add(ParserError('Parser was unable to determine utterance end time.', self))
            if self.lena_notes:
                if DBConstants.LENA_NOTES_CODES.get_option(self.lena_notes) == None:
                    error_collector.add(ParserError('Unrecognized LENA note.', self))

            #make sure we have the right number of transcriber codes
            if self.trans_phrase:
                if len(self.trans_codes) < len(DBConstants.TRANS_CODES):
                    error_collector.add(ParserError('Utterance has less than %d transcriber codes.' % (len(DBConstants.TRANS_CODES)), self))

                i = 0
                bad_indices = []

                for i in range(len(self.trans_codes)):
                    error_msgs = DBConstants.TRANS_CODES[i].is_valid(self.trans_codes[i])
                    if error_msgs:
                        bad_indices.append({'index': i + 1, 'error_msgs': error_msgs})

                if bad_indices:
                    err_str = 'Utterance transcriber codes contain the following errors:\n'
                    for issue in bad_indices:
                        err_str += '  Code %d:\n' % (issue['index'])
                        for msg in issue['error_msgs']:
                            err_str += '    -%s\n' % (msg)

                    error_collector.add(ParserError(err_str, self))
