## @package parsers.filter_manager

from utils.enum import Enum
from collections import OrderedDict

## This class impersonates a Segment instance, but maintains an alternate (filtered) utterance list. This filtered utterance <em>list</em> can be set or modified without altering up the original Segment's utterance list.
#  However, modifying the underlying Utterance instances themselves will affect the original Segment's utterance list (i.e. we are dealing with pointers).
#  An instance of this class will return properties of the underlying Segment object for everything except the 'utters' property. Similarly, setting any attribute other
#  than 'utters' will set the attribute in the underlying Segment object.
# Instances of this class can therefore be used in any context where a Segment instance would be used.
class FilteredSeg(object):
    ## Constructor
    #  @param self
    #  @param orig_seg (Segment) the Segment that's being filtered (this segment will be impersonated)
    #  @param filtered_utters (list) a list of utterances representing the contents of orig_seg after it has been filtered.
    def __init__(self, orig_seg, filtered_utters):
        # Note: attributes of this instance are prefixed with an underscore. This indicates that they should not be accessed directly and lessens the confusion between this instance's attributes and the underlying Segment's attributes.
        # See __getattr__() for more details.        
        self._filtered_utters = filtered_utters
        self._orig_seg = orig_seg

    ## Retreives an attribute for this FilteredSeg. You may request any of the attributes of the Segment class.
    # This method overrides Python's attribute retreival for this object.
    # This allows us to return the corresponding attribute of the underlying Segment when anything other than 'utters' is requested.
    # When 'utters' is requested, we return this object's list instead of the underlying Segment's list.
    # @param self
    # @param name (string) the name of the attribute being requested.
    # @returns (object/primitive) returns the requested attribute, or throws an AttributeError if it doesn't exist
    def __getattr__(self, name):
        result = None

        #check if the requested name exists in this instance's (Python maintained) internal attribute dictionary - (note: requests originating inside this instance also hit this method, so this case is needed to prevent infinite recursion.)
        if name in self.__dict__:
            result = self.__dict__[name]
        #if they're requesting the 'utters' attribute, give them this FilteredSeg's list instead of the orig_seg's list
        elif name == 'utters':
            result = self.__dict__['_filtered_utters']
        #this case provides the ability to retreive the underlying segment's attributes
        elif hasattr(self.__dict__['_orig_seg'], name):
            result = getattr(self.__dict__['_orig_seg'], name)
        #if the attribute doesn't exist in either the underlying segment, or this instance, raise an exception
        else:
            raise AttributeError('FilteredSeg has no attribute "%s"' % (name))

        return result

    ## Sets an attribute for this FilteredSeg. You may set any of the attributes of the Segment class. However, when the 'utters' attribute is set, the underlying Segment's list is not modified (instead, this instance's '_filtered_utters' attribute is used).
    # This method overrides Python's attribute setting functionality.
    # This allows us to set the corresponding attribute of the underlying Segment when anything other than 'utters' is requested.
    # @param self
    # @param name (string) the name of the attribute to set
    # @param value (object/primitive) the value to set the specified attribute to
    def __setattr__(self, name, value):
        #intercept requests to set the 'utters' attribute, and instead set this instance's '_filtered_utters' attribute
        if name == 'utters':
            self.__dict__['_filtered_utters'] = value
        #requests originating inside this instance also hit this method. This case is needed to prevent infinite recursion.
        elif name == '_orig_seg' or name == '_filtered_utters':
            self.__dict__[name] = value
        #this case provides the ability to set this instance's attributes
        elif name in self.__dict__['_orig_seg']:
            self.__dict__['_orig_seg'][name] = value
        #if the attribute doesn't exist in either the underlying segment, or this instance, raise an exception
        else:
            raise AttributeError('FilteredSeg has no attribute "%s"' % (name))

## This class provides various ways of looking up segments or utterances (from a list of Segment-like objects passed to the constructor).
#  It provides lookup methods for both 'Segments' and 'chains'.
#  A 'chain' is a linked list of Utterances that have been linked using I/C transcriber codes.
class FilterManager(object):
    #Used to indicate the beginning or end of a chain
    ENDPOINT_TYPES = Enum('HEAD TAIL'.split(), ['prev', 'next'])

    ## Constructor
    #  @param self
    #  @param segs (list) list of Segment objects
    def __init__(self, segs):
        self.segs = segs        #list of all segments
        self.chains = None      #list containing the heads of chains that have been parsed from self.segs (see get_chains() for how this is done) - this is build upon request
        self.seg_index = None   #dictionary that allows fast access (via segment number) to individual segments in self.segs - built upon request
        self.chain_index = None #dictionary that allows fast access (via the head utterance's id) to individual utterances in self.chains - built upon request

    ## Retreives a list of all of the segments in this FilterManager
    #  @param self
    #  @returns (list) list of Segments
    def get_segs(self):
        return self.segs

    ## Retreives a list of all of the chains in this FilterManager
    #  @param self
    #  @returns (list) list containing Utterance objects - each element is the head of a chain. Chains are parsed from the segs element of the constructor - see get_chains() for how this is done.
    def get_chains(self):
        #'cache' the chains so we don't have to parse them again if this method is called in the future
        if not self.chains:
            self.chains = FilterManager.get_chains(self.segs)

        return self.chains

    ## Retreives a segment by segment number (Segment class's 'num' attribute).
    #  Note: this number is unique to all Segments parsed by the TRSParser class <em>for a single file.</em>
    #  @param self
    #  @param num (int) the segment number to lookup
    #  @returns (Segment) the Segment with the requested number, or None if not found.
    def get_seg_by_num(self, num):
        #use a dictionary to provide a basic index/cache mechanism to speed up future lookups
        if not self.seg_index:
            self.seg_index = {}
            for seg in self.segs:
                self.seg_index[seg.num] = seg

        result = None
        if num in self.seg_index:
            result = self.seg_index[num]
            
        return result

    ## Retreives a chain by the utterance id of the head node (head node is the first Utterance object in the chain)
    #  Note: this number is unique to all Utterances parsed by the TRSParser class <em>for a single file.</em>
    #  @param self
    #  @param num (int) the utterance id to lookup.
    #  @returns (Utterance) the head of the chain, or None if no matching chain was found.
    def get_chain_by_num(self, num):
        #use a dictionary to provide a basic index/cache mechanism to speed up future lookups
        if not self.chain_index:
            self.chain_index = {}
            for cur_head in self.get_chains():
                self.chain_index[cur_head.id] = cur_head

        result = None
        if num in self.chain_index:
            result = self.chain_index[num]

        return result

    ## Retreives a list of chains using the specified list of segments.
    #  The method iterates over all utterances within the specified segments. On each iteration, it follows the 'prev' pointer back to the start of the utterance chain.
    # This means that this method returns a list of (the heads of) all chains have a node that is in the utterance list of one of the specified segments.
    # Steps are taken to ensure that if two utterances lead back to the same head, that head is only included once in the returned list (duplicate heads are discarded).
    # The list that is returned is sorted ascending by the start time of the head nodes.
    #  @param segs (list) list of Segments
    #  @returns (list) list of the (unique) head nodes (utterance objects) of all chains found. The list is sorted in ascending order by the start time of the head utterances.
    @staticmethod
    def get_chains(segs):
        #Note: we use an OrderedDict here to address cases where we have two identical start times.
        #If we used a regular dict in these cases, the ordering sometimes swaps. This appears strange to the user because
        #when clicking the 'Group Linked Segments' checkbox, the ordering changes even when there are no chained utterances
        #in the list.
        #The swap that occurs in these cases is not due to the sort (according to the python docs it's guarenteed to be stable) - it's
        #due to the order that the keys are retreived from the dictionary.
        #Using an OrderedDict causes the keys to be retreived in the same order they were inserted.
        heads = OrderedDict()
        for seg in segs:
            for utter in seg.utters:
                cur = utter
                prev = cur
                while cur != None:
                    prev = cur
                    cur = cur.prev

                heads[prev] = True #dictionary weeds out duplicates

        result = heads.keys()
        result.sort(key=lambda cur_utter: cur_utter.start)
        
        return result
        
    ## Constructs a string containing the transcription phrases or all utterances in a given chain.
    #  @param head (Utterance) the Utterance object at the head of the chain
    #  @returns (string) a string containing the transcription phrases of all nodes in the chain, separated by an arrow (' -> ')
    @staticmethod
    def get_chain_phrase(head):
        result = ''
        cur =  head
        prev = head
        while cur:
            result += cur.trans_phrase

            prev = cur
            cur = cur.next
            if cur:
                result += '\n -> '

        return result, prev

    @staticmethod
    def get_chain_lena_speakers(head):
        result = ''
        cur =  head
        prev = head
        while cur:
            if cur.speaker and cur.speaker.speaker_codeinfo:
                result += cur.speaker.speaker_codeinfo.code
            else:
                result += '?'

            prev = cur
            cur = cur.next
            if cur:
                result += '\n -> '

        return result, prev

    @staticmethod
    def get_chain_trans_codes(head):
        result = ''
        cur =  head
        prev = head
        while cur:
            result += '|%s|' % ('|'.join(cur.trans_codes)) if cur.trans_codes else 'None'

            prev = cur
            cur = cur.next
            if cur:
                result += '\n -> '

        return result, prev

    ## Finds the start/end node of a chain.
    #  @param endpoint_type (int) a member of the enum FilterManager.ENDPOINT_TYPES, indicating whether we're searching for the start or end of the chain
    #  @param utter (Utterance) any utterance in the chain
    #  @returns (Utterance) the start or end node of the chain, as specified by the 'endpoint_type' parameter
    @staticmethod
    def get_endpoint(endpoint_type, utter):
        cur = utter
        while getattr(cur, endpoint_type) != None:
            cur = getattr(cur, endpoint_type)
            
        return cur
