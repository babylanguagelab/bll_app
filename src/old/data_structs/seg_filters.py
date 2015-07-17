## @package data_structs.seg_filters

from data_structs.base_objects import DBObject
from parsers.filter_manager import FilteredSeg, FilterManager
from db.bll_database import DBConstants
from utils.backend_utils import BackendUtils

import re

## This class (actually, its subclasses) handles all of the segment/chain filtering operations in the BLL Apps.
#  Currently, this class exists as an interface (if Python had those). Subclasses should override the methods indicated.
#  Filters can be saved to the DB.
#  The filtering methods make use of a special data structure called a FilteredSeg (see bll_app.parsers.filter_manager.py). A FilteredSeg wraps a Segment object and provides access to all it's attributes except one - the 'utters' attribute.
#  (The 'utters' attribute is a list of all the utterances that the Segment contains). The FilteredSeg maintains its own separate utters list, and redirects accesses to that list, rather than the original Segment object's list. This means that
#  one can create a FilteredSeg object from a Segment object, then modify the FilteredSeg object's utters <em>list</em> without having any effect on the original Segment's utters list (note that if you modify the actual utterances themselves - as opposed to
# just the list - this will affect the Utterance objects in the original Segment's utters list). This is important because it allows this class to return FilteredSeg objects that represent filtered versions of Segments, without messing with the orignal utterance list, which may
# be needed elsewhere.
class SegFilter(DBObject):
    ## Constructor
    #  @param self
    #  @param db_id (int=None) if this SegFilter is in the DB, this is a primary key id - else it is None. This is set by db_insert() and db_select().
    #  @negate (boolean=False) when set to True, this Filter's effects are inverted (it includes segments it normally excludes, and excludes those it normally includes). When False, the Filter works normally.
    def __init__(self, db_id=None, negate=False):
        self.db_id = db_id
        self.negate = negate

    ## See superclass description.
    def db_insert(self, db):
        last_ids = db.insert('seg_filters',
                             'class_name args'.split(),
                             [[self.__class__.__name__, str(self.get_db_args())]]
                             )
        self.db_id = last_ids[0]

    ## See superclass description.
    def db_delete(self, db):
        db.delete('seg_filters',
                  'id=?',
                  [self.db_id],
                  )

    ## Constructs a list of SegFilter objects from data retreived from the DB.
    #  @param filter_rows (list) this should be a list of the form [ [id, class_name, args], ... ].
    #  @returns (list) list of SegFilter objects (of the appropriate subclass type).
    @staticmethod
    def _reconstruct_from_db(filter_rows):
        filter_list = []
        for cur_row in filter_rows:
            cls = eval(cur_row[1])
            args = eval(cur_row[2])
            filter_obj = cls(*args)
            filter_obj.db_id = cur_row[0]
            filter_list.append(filter_obj)

        return filter_list

    ## See superclass description.
    @staticmethod
    def db_select(db, ids=[]):
        rows = db.select('seg_filters',
                         'id class_name args',
                         DBObject._build_where_cond_from_ids(ids),
                         )
        
        return SegFilter._reconstruct_from_db(rows)

    ## Selects SegFilter objects from the DB via a relationship table.
    #  @param db (BLLDatabase) a database handle object
    #  @param rel_table (string) name of the relationship table
    #  @param filter_id_col (string) name of the column in rel_table that contains filter ids (a foreign key column corresponding to the seg_filters table primary key column).
    #  @param rel_id_col (string) name of the column in rel_table that contains the alternative (non-filter) ids you wish to look up
    #  @param rel_val (int) value of rel_id_col to search for in rel_table. Corresponding values from filter_id_col will be recorded. A select will be done on seg_filters using these ids. Finally, SegFilter objects corresponding to the selected rows will be created and returned.
    #  @returns (list) list of SegFilter objects (or appropriate subclasses)
    @staticmethod
    def db_select_by_ref(db, rel_table, filter_id_col, rel_id_col, rel_val):
        rows = db.select('%s rel join seg_filters sf on rel.%s=sf.id' % (rel_table, filter_id_col),
                         'sf.id sf.class_name sf.args'.split(),
                         '%s=?' % (rel_id_col),
                         [rel_val],
                         )
        
        return SegFilter._reconstruct_from_db(rows)

    ## Handles the filtering of unlinked segments. Subclasses should not override this method - they should override the private method _filter_seg(), which this method calls.
    #  @param seg (Segment/FIlteredSeg) the segment-like object to filter
    #  @param filter_utters (boolean=False) If True, a FilteredSeg is returned, containing only those Utterances that pass the filter. If False, if even one Utterance fails the filter, None will be returned (otherwise a FilteredSeg containing the same Utterances as the parameter seg will be returned).
    #  @returns a FilteredSeg object whose utterances have been filtered according to the filter_utters and negate parameter settings, or None in the case noted in the filter_utters description.
    def filter_seg(self, seg, filter_utters=False):
        return self._filter_seg(seg, self.negate, filter_utters)

    ## Handles the filtering of linked segments. Subclasses should not override this method - they should override the private method _filter_linked_utter(), which this method calls.
    #  Note: This method does not have a 'filter_utters' param (link filter_seg) because each chain is essentially treated like 'a single long utterance'. Therefore, if one utterance in the chain fails the filter, the whole chain fails.
    #  @param self
    #  @param head (Utterance) start of the chain
    #  @returns (Utterance) if the chain passed the filter, returns the start of the chain. Else returns None.
    def filter_linked_utter(self, head):
        return self._filter_linked_utter(head, self.negate)

    ## See superclass description. Subclasses should not override this method - they should override the private method _get_db_args(), which this method calls.
    def get_db_args(self):
        return self._get_db_args(self.negate)

    ## See superclass description. Subclasses should not override this method - they should override the private method _get_filter_type_str(), which this method calls.
    def get_filter_type_str(self):
        return self._get_filter_type_str(self.negate)

    ## See superclass description. Subclasses should not override this method - they should override the private method _get_filter_desc_str(), which this method calls.
    def get_filter_desc_str(self):
        return self._get_filter_desc_str(self.negate)
    
    ## See filter_seg(). Must be overridden by subclasses.
    #  @param seg (Segment/FilteredSeg) the segment-like object to filter
    #  @param negate (boolean=False) if True, the filter should invert its functionality (include what it normally excludes, and exclude what it normally includes). If False, the filter should act normally.
    #  @param filter_utters (boolean=False) see filter_seg() description of this parameter.
    #  @returns a FilteredSeg object whose utterances have been filtered according to the filter_utters and negate parameter settings, or None in the case noted in the filter_utters description.
    def _filter_seg(self, seg, negate, filter_utters=False):
        pass

    ## See filter_linked_utter(). Must be overridden by subclasses.
    #  @param head (Utterance) the start node of the chain to be filtered
    #  @param negate (boolean=False) if True, the filter should invert its functionality (include what it normally excludes, and exclude what it normally includes). If False, the filter should act normally.
    #  @returns (Utterance) if the chain passed the filter, returns the start of the chain. Else returns None.
    def _filter_linked_utter(self, head, negate):
        pass

    ## See get_db_args(). Subclass should override.
    #  @param self
    #  @param negate (boolean) True indicates the filter should invert its functionality. False indicates that it should act normally.
    def _get_db_args(self, negate):
        return [negate]

    ## See get_filter_type_str(). Subclass should override.
    #  @param self
    #  @param negate (boolean) True indicates the filter should invert its functionality. False indicates that it should act normally.
    def _get_filter_type_str(self, negate):
        pass
    
    ## See get_filter_desc_str(). Subclass should override.
    #  @param self
    #  @param negate (boolean) True indicates the filter should invert its functionality. False indicates that it should act normally.
    def _get_filter_desc_str(self, negate):
        pass


    ## Convenience method to wrap Segments in FilteredSeg objects and set the filtered utters list. Subclasses need not override this.
    #  If 'seg' is a Segment, creates a FilteredSeg (with an Utterance list of 'utters') from the 'seg' parameter. If 'seg' is a FilteredSeg, sets the utterance list to 'utters'.
    #  @param self
    #  @param seg (Segment/FilteredSeg) the object you wish to wrap/modify
    #  @param utters (list) list of Utterance objects to assign to the resulting FilteredSeg (this is generally a filtered list)
    def _to_filtered_seg(self, seg, utters):
        result = seg
        if isinstance(seg, FilteredSeg):
            seg.utters = utters
        else:
            result = FilteredSeg(seg, utters)

        return result

## This Filter allows utterances to pass through if they (contain at least one 'wh' word (who, what, when, where, why, how) AND are marked as a question in transcriber code 3).
class WHQFilter(SegFilter):
    ## Constructor
    #  @self
    #  @negate (boolean=False) If True, the filter will invert its behaviour. If False, the filter acts normally.
    #  @param db_id (int=None) this is the primary key id from the database table seg_filters. A value of None indicates that this filter is not yet in the DB.
    def __init__(self, negate=False, db_id=None):
        SegFilter.__init__(self, db_id, negate)

    ## See superclass description.
    def _filter_seg(self, seg, negate, filter_utters=False):
        utters = []
        result = None
        passed = False

        i = 0
        while i < len(seg.utters) and not passed:
            if seg.utters[i].trans_codes and len(seg.utters[i].trans_codes) >= 4:
                #check if the utterance was transcribed as a question, and contains a wh word
                cond = ( seg.utters[i].trans_codes[3].find('Q') >= 0 and
                 re.search(r'\bwh|\bhow\b', seg.utters[i].trans_phrase.lower()) )

                #if we're straining out utters that don't pass, append those utterances to a list
                if filter_utters:
                    if (not negate and cond) or (negate and not cond):
                        utters.append(seg.utters[i])
                #otherwise, throw out the whole segment if one utterance doesn't pass
                else:
                    passed = cond
            i += 1

        #ensure the Segment is wrapped in a FilteredSeg containing the filtered utterance list
        if filter_utters:
            result = super(WHQFilter, self)._to_filtered_seg(seg, utters)
            
        else:
            if passed:
                result = super(WHQFilter, self)._to_filtered_seg(seg, seg.utters)
            
        return result

    ## See superclass description.
    def _filter_linked_utter(self, head, negate):
        result = None
        found = False
        cur = head

        #run through the chain nodes until we're done or one fails
        while cur and not found:
            if cur.trans_codes:
                #check if the utterance was transcribed as a question, and contains a wh word
                found = ( cur.trans_codes[3].find('Q') >= 0 and
                          re.search(r'\bwh|\bhow\b', cur.trans_phrase.lower()) )
                
            cur = cur.next

        #if one node in the chain failed, throw out the whole chain. Otherwise, return the head node.
        if (not negate and found) or (negate and not found):
            result = head

        return result

    ## See superclass description.
    def _get_db_args(self, negate):
        return [negate]

    ## See superclass description.
    def _get_filter_type_str(self, negate):
        return '"WH" Question'

    ## See superclass description.
    def get_filter_desc_str(self, negate):
        return 'Is %sa "WH" question' % (' not' if self.negate else '')

## This filter strains out utterances that start or end after a specific time.
class TimeSegFilter(SegFilter):
    #time cutoff is in seconds
    #filter_type is 
    ## Constructor
    #  @param self
    #  @param filter_type (int) an element from DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.SEG_FILTER_TIME], indicating the behaviour of this filter - eg. whether it should cut of segments that start before, start after, end before, or end after 'time cutoff'.
    #  @param time_cutoff (float) the point time, specified in seconds, for which this filter should apply the behaviour specified by 'filter_type'.
    #  @param inclusive (boolean=True) if True, the filter will allow utterances whose start/end time (depending upon the behaviour specified by 'filter_type') is equal to 'time_cutoff' to pass through the filter. If False, it will strain these out.
    #  @negate (boolean=False) If True, the filter will invert its behaviour. If False, the filter acts normally.
    #  @param db_id (int=None) this is the primary key id from the database table seg_filters. A value of None indicates that this filter is not yet in the DB.
    def __init__(self, filter_type, time_cutoff, inclusive=True, negate=False, db_id=None):
        SegFilter.__init__(self, db_id, negate)
        
        self.filter_type = filter_type
        self.time_cutoff = time_cutoff
        self.inclusive = inclusive

    ## See superclass description.
    def _filter_seg(self, seg, negate, filter_utters=False):
        result = None

        #read the filter type options into a local variable to cut down on the amount ot typing
        options = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.SEG_FILTER_TIME]
        
        #build a dictionary that maps the possible filter_type options to functions. Each function accepts an utterance/segment and returns a boolean that's true if the utterance/segment passed the filter.
        include_dict =  {options.START_TIME_BEFORE: lambda data_obj: (data_obj.start <= self.time_cutoff) if self.inclusive else (data_obj.start < self.time_cutoff),
                         options.START_TIME_AFTER: lambda data_obj: (data_obj.start >= self.time_cutoff) if self.inclusive else (data_obj.start > self.time_cutoff),
                         options.END_TIME_BEFORE: lambda data_obj: (data_obj.end <= self.time_cutoff) if self.inclusive else (data_obj.end < self.time_cutoff),
                         options.END_TIME_AFTER: lambda data_obj: (data_obj.end >= self.time_cutoff) if self.inclusive else (data_obj.end > self.time_cutoff),
                         }

        #if we are supposed to strain out utterances that don't pass, build a list of them
        if filter_utters:
            utter_list = []
            for utter in seg.utters:
                include_utter = include_dict[self.filter_type](utter)
                if (not negate and include_utter) or (negate and not include_utter):
                    utter_list.append(utter)

            #warp result in a FilteredSeg
            result = super(TimeSegFilter, self)._to_filtered_seg(seg, utter_list)

        #otherwise, one failed utterance causes us to discard the entire segment
        else:
            include_seg = include_dict[self.filter_type](seg)

            if (not negate and include_seg) or (negate and not include_seg):
                #wrap result in a FilteredSeg
                result = super(TimeSegFilter, self)._to_filtered_seg(seg, seg.utters)

        return result

    ## See superclass description.
    def _filter_linked_utter(self, head, negate):
        result = None
        #grab the possible filter_type options into a local var, for convenience
        options = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.SEG_FILTER_TIME]

        #find chain endpoint
        tail = FilterManager.get_endpoint(FilterManager.ENDPOINT_TYPES.TAIL, head)

        #build a dictionary that maps the possible filter_type options to functions. Each function accepts an utterance/segment and returns a boolean that's true if the utterance/segment passed the filter.
        include = {options.START_TIME_BEFORE: lambda head, tail: head.start <= self.time_cutoff if self.inclusive else head.start < self.time_cutoff,
                   options.START_TIME_AFTER: lambda head, tail: head.start >= self.time_cutoff if self.inclusive else head.start > self.time_cutoff,
                   options.END_TIME_BEFORE: lambda head, tail: tail.end <= self.time_cutoff if self.inclusive else tail.end < self.time_cutoff,
                   options.END_TIME_AFTER: lambda head, tail: tail.end >= self.time_cutoff if self.inclusive else tail.end > self.time_cutoff,
                   }[self.filter_type](head, tail)

        #return the head if no node in the chain failed
        if (not negate and include) or (negate and not include):
            result = head

        return result

    ## See superclass description.
    def _get_db_args(self, negate):
        return [self.filter_type,
                self.time_cutoff,
                self.inclusive,
                negate,
                ]

    ## See superclass description.
    def _get_filter_type_str(self, negate):
        return 'Time'

    ## See superclass description.
    def _get_filter_desc_str(self, negate):
        options = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.SEG_FILTER_TIME]
        desc = ''
        #handle the negation
        if self.negate:
            desc += 'Does not '

        #append an appropriate description of the behaviour based on 'filter_type'. Also handle the pluralization of words.
        desc += {options.START_TIME_BEFORE: 'start%s before' % ('s' if not negate else ''),
                 options.START_TIME_AFTER: 'start%s after' % ('s' if not negate else ''),
                 options.END_TIME_BEFORE: 'end%s before' % ('s' if not negate else ''),
                 options.END_TIME_AFTER: 'end%s after' % ('s' if not negate else ''),
                 }[self.filter_type]
        desc += ' '
        desc += BackendUtils.get_time_str(self.time_cutoff)
        desc = desc.capitalize() #appease any English teachers in the audience

        return desc

## This type of filter searches for Utterances of types OLN, OLF, and/or transcribed with '<>', filtering out all others.
class OverlappingVocalsSegFilter(SegFilter):
    ## Constructor
    #   @param self
    #  @negate (boolean=False) If True, the filter will invert its behaviour. If False, the filter acts normally.
    #  @param db_id (int=None) this is the primary key id from the database table seg_filters. A value of None indicates that this filter is not yet in the DB.
    def __init__(self, negate=False, db_id=None):
        SegFilter.__init__(self, db_id, negate)

    ## See superclass description.
    def _filter_seg(self, seg, negate, filter_utters=False):
        result = None

        if filter_utters:
            utter_list = []
            for utter in seg.utters:
                if utter.trans_phrase:
                    trans_phrase = utter.trans_phrase.replace('&lt;', '<').replace('&gt;', '>') #undo the xml encoding for the angle brackets (for convenience of regex search below, as regexs have special meaning for ampersand)
                    cond = ( (utter.speaker and utter.speaker.has_property(DBConstants.SPEAKER_PROPS.OVERLAPPING)) or
                             (re.search('(?:^\s*<.*>.*$)|(?:.*<\s*>\s*)', trans_phrase)) )
                    if (not negate and cond) or (negate and not cond):
                        utter_list.append(utter)

            result = super(OverlappingVocalsSegFilter, self)._to_filtered_seg(seg, utter_list)

        else:
            i = 0
            found = False
            while not found and i < len(seg.utters):
                if utter.trans_phrase:
                    trans_phrase = utter.trans_phrase.replace('&lt;', '<').replace('&gt;', '>') #undo xml encoding for angle brackets
                    found = ( (utter.speaker and utter.speaker.has_property(DBConstants.SPEAKER_PROPS.OVERLAPPING)) or
                              (re.search('(?:^\s*<.*>.*$)|(?:.*<\s*>\s*)', trans_phrase)) )
                i += 1

            if (not negate and found) or (negate and not found):
                result = head

        return result

    ## See superclass description.
    def _filter_linked_utter(self, head, negate):
        result = None
        
        found = False
        cur = head
        while not found and cur:
            if cur.trans_phrase:
                trans_phrase = cur.trans_phrase.replace('&lt;', '<').replace('&gt;', '>')
                found = ( (cur.speaker and cur.speaker.has_property(DBConstants.SPEAKER_PROPS.OVERLAPPING)) or
                          (trans_phrase and re.search('(?:^\s*<.*>.*$)|(?:.*<\s*>\s*)', trans_phrase)) )
            cur = cur.next

        if (not negate and found) or (negate and not found):
            result = head

        return result

    ## See superclass description.
    def _get_db_args(self, negate):
        return [negate]

    ## See superclass description.
    def _get_filter_type_str(self, negate):
        return 'Overlapping Vocals'

    ## See superclass description.
    def _get_filter_desc_str(self, negate):
        return 'Not marked by LENA as overlapping and not transcribed as overlapping' if negate else 'Marked by LENA and/or transcribed as overlapping'

## This type of Filter can be used to include only segments/chains with particular LENA-defined speaker codes (eg. FAN, MAN, CHN).
class SpeakerCodeSegFilter(SegFilter):
    ## Constructor
    #  @param self
    #  @param code_str_list (list) list of strings, each matching a particular LENA speaker code (eg. 'MAN', 'FAN', etc). The filter will OR together multiple codes.
    #  @negate (boolean=False) If True, the filter will invert its behaviour. If False, the filter acts normally.
    #  @param db_id (int=None) this is the primary key id from the database table seg_filters. A value of None indicates that this filter is not yet in the DB.    
    def __init__(self, code_str_list, negate=False, db_id=None):
        SegFilter.__init__(self, db_id, negate)
        
        self.code_str_list = code_str_list

    ## See superclass description.
    # An OR operation is performed using all codes in code_str_list. Eg. if code_str_list == ['FAN', 'MAN'], then only utterances with speaker codes FAN or MAN will pass through the filter.
    def _filter_seg(self, seg, negate, filter_utters=False):
        result = None

        if filter_utters:
            utter_list = []
            for utter in seg.utters:
                i = 0
                utter_has_speaker = False
                while not utter_has_speaker and i < len(self.code_str_list):
                    utter_has_speaker = utter.speaker and utter.speaker.speaker_codeinfo.get_code() == self.code_str_list[i]
                    i += 1
                    
                if negate:
                    if not utter_has_speaker:
                        utter_list.append(utter)
                else:
                    if utter_has_speaker:
                        utter_list.append(utter)
                    
            result = super(SpeakerCodeSegFilter, self)._to_filtered_seg(seg, utter_list)

        else:
            speaker_in_list = False
            i = 0
            j = 0
            while not speaker_in_list and i < len(seg.speakers):
                while not speaker_in_list and j < len(self.code_str_list):
                    speaker_in_list = seg.speakers[i].speaker_codeinfo.get_code() == self.code_str_list[j]
                    j += 1
                i += 1

            if negate:
                if not speaker_in_list:
                    result = super(SpeakerCodeSegFilter, self)._to_filtered_seg(seg, seg.utters)
            else:
                if speaker_in_list:
                    result = super(SpeakerCodeSegFilter, self)._to_filtered_seg(seg, seg.utters)

        return result

    ## See superclass description.
    #  Note the OR behaviour if there are multiple codes in self.code_str_list
    def _filter_linked_utter(self, head, negate):
        result = None
        speaker_in_chain = False
        cur = head
        while not speaker_in_chain and cur:
            i = 0
            while not speaker_in_chain and i < len(self.code_str_list):
                speaker_in_chain = cur.speaker and cur.speaker.speaker_codeinfo.get_code() == self.code_str_list[i]
                i += 1
            cur = cur.next

        include_chain = False
        if negate:
            include_chain = not speaker_in_chain
        else:
            include_chain = speaker_in_chain

        if include_chain:
            result = head

        return result

    ## See superclass description.
    def _get_db_args(self, negate):
        return [self.code_str_list, negate]

    ## See superclass description.
    def _get_filter_type_str(self, negate):
        return 'Speaker'

    ## See superclass description.
    def _get_filter_desc_str(self, negate):
        desc = 'Speaker code is %s' % ('not ' if self.negate else '')
        if len(self.code_str_list) > 1:
            desc += 'one of (%s)' % (' or '.join(self.code_str_list))
        else:
            desc += self.code_str_list[0]

        return desc

## This is an 'abstract' base class for all types of filters that include/exclude based on a particular transcriber code.
class TransCodeSegFilter(SegFilter):
    ## Constructor
    #  @param self
    #  @param trans_code_index (int) the index (zero-based) of the transcriber code this filter will operate upon.
    #  @param type_str (string) a string to use for the output of _get_filter_type_str()
    #  @param desc_noun (string) used in get_filter_desc_str() to describe the object that this filter is filtering.
    #  @param code_str_list (list) list of codes (that are valid for the transcriber code specified in trans_code_index) to allow through the filter (OR logic is used for multiple codes).
    #  @negate (boolean=False) If True, the filter will invert its behaviour. If False, the filter acts normally.
    #  @param db_id (int=None) this is the primary key id from the database table seg_filters. A value of None indicates that this filter is not yet in the DB.
    def __init__(self, trans_code_index, type_str, desc_noun, code_str_list, negate=False, db_id=None):
        super(TransCodeSegFilter, self).__init__(db_id, negate)

        self.trans_code_index = trans_code_index
        self.type_str = type_str
        self.desc_noun = desc_noun
        self.code_str_list = code_str_list

    ## See superclass description.
    # Note: A logical OR operation is performed using all codes in code_str_list. That is, utterances pass if they match at least one of the codes.
    def _filter_seg(self, seg, negate, filter_utters=False):
        result = None

        if filter_utters:
            utter_list= []
            for utter in seg.utters:
                i = 0
                found = False
                #search for one of the codes in self.code_str_list
                while not found and i < len(self.code_str_list):
                    found = utter.trans_codes and len(utter.trans_codes) > self.trans_code_index and utter.trans_codes[self.trans_code_index].find(self.code_str_list[i]) > -1
                    i += 1

                if negate:
                    if not found:
                        utter_list.append(utter)
                else:
                    if found:
                        utter_list.append(utter)
                        
            result = super(TransCodeSegFilter, self)._to_filtered_seg(seg, utter_list)

        else:
            found = False
            i = 0
            #for chains we only require one node to have a match (then the whole thing is considered a match)
            while not found and i < len(seg.utters):
                j = 0
                while not found and j < len(self.code_str_list):
                    found = seg.utters[i].trans_codes and seg.utters[i].trans_codes[self.trans_code_index].find(self.code_str_list[j]) > -1
                    j += 1
                i += 1

            if negate:
                if not_found:
                    result = super(TransCodeSegFilter, self)._to_filtered_seg(seg, seg.utters)
            else:
                if found:
                    result = super(TransCodeSegFilter, self)._to_filtered_seg(seg, seg.utters)

        return result

    ## See superclass description.
    # Note: A logical OR operation is performed using all codes in code_str_list. That is, utterances pass if they match at least one of the codes.
    def _filter_linked_utter(self, head, negate):
        result = None
        code_in_chain = False
        cur = head
        while not code_in_chain and cur:
            i = 0
            while not code_in_chain and i < len(self.code_str_list):
                if self.trans_code_index < len(cur.trans_codes): #make sure we have the correct number of transcriber codes (so we don't index out of bounds)
                    code_in_chain = cur.trans_codes and cur.trans_codes[self.trans_code_index].find(self.code_str_list[i]) > -1
                i += 1

            cur = cur.next

        if negate:
            if not code_in_chain:
                result = head
        else:
            if code_in_chain:
                result = head

        return result

    ## See superclass description.
    def _get_db_args(self, negate):
        return [self.trans_code_index, self.type_str, self.desc_noun, self.code_str_list, negate]

    ## See superclass description.
    def _get_filter_type_str(self, negate):
        return self.type_str

    ## See superclass description.
    def _get_filter_desc_str(self, negate):
        desc = '%s is %s' % (self.desc_noun, 'not ' if self.negate else '')
        if len(self.code_str_list) > 1:
            desc += 'one of (%s)' % (' or '.join( map(lambda cd: DBConstants.TRANS_CODES[self.trans_code_index].get_option(cd).get_code_desc(), self.code_str_list) ))
        else:
            desc += DBConstants.TRANS_CODES[self.trans_code_index].get_option(self.code_str_list[0]).get_code_desc()

        return desc

## This class filters by transcriber code 1 (speaker type). Utterances with a particular speaker type will pass through the filter.
class SpeakerTypeSegFilter(TransCodeSegFilter):
    ## See superclass description.
    def __init__(self, code_str_list, negate=False, db_id=None):
        super(SpeakerTypeSegFilter, self).__init__(0, 'Speaker Type', 'Speaker Type', code_str_list, negate, db_id)

    ## See superclass description.
    def _get_db_args(self, negate):
        return [self.code_str_list, negate]

## This class filters by transcriber code 2 (target listener). Utterances with a particular target listener will pass through the filter.
class TargetListenerSegFilter(TransCodeSegFilter):
    ## See superclass description.
    def __init__(self, code_str_list, negate=False, db_id=None):
        super(TargetListenerSegFilter, self).__init__(1, 'Target Listener', 'Target Listener', code_str_list, negate, db_id)

    ## See superclass description.
    def _get_db_args(self, negate):
        return [self.code_str_list, negate]

## This class filters by transcriber code 3 (grammaticality/completeness). Utterances with a particular grammaticality/completeness will pass through the filter.
class GrammaticalitySegFilter(TransCodeSegFilter):
    ## See superclass description.
    def __init__(self, code_str_list, negate=False, db_id=None):
        super(GrammaticalitySegFilter, self).__init__(2, 'Gramaticality', 'Utterance', code_str_list, negate, db_id)

    ## See superclass description.
    def _get_db_args(self, negate):
        return [self.code_str_list, negate]

## This class filters by transcriber code 4 (utterance type). Utterances with a particular utterance type will pass through the filter.
class UtteranceTypeSegFilter(TransCodeSegFilter):
    ## See superclass description.
    def __init__(self, code_str_list, negate=False, db_id=None):
        super(UtteranceTypeSegFilter, self).__init__(3, 'Utterance Type', 'Utterance', code_str_list, negate, db_id)

    ## See superclass description.
    def _get_db_args(self, negate):
        return [self.code_str_list, negate]

