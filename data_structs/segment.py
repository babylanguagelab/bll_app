## @package data_structs.segment

from data_structs.base_objects import DBObject
from db.bll_database import DBConstants
from data_structs.speaker import Speaker

##This class holds a chunk of information from the TRS file.
#This corresponds to the information between a <Turn></Turn> pair of tags in a TRS file. Each <sync> or <who> group within the turn tags is an Utterance (caveat:  if one <sync> or <who> tag has multiple lines, each line is a separate Utterance).
#Each Segment has a list of Utterances it contains.
#Note: this class differs slightly from the linguistic definition of a "segment". However, this is the organization that I finally settled on coding when I started....
#To the best of my knowledge, the linguistic definition is usually equivalent to what the Utterance object represents.
#I make sure metrics presented in units of "Segments" in the UI correspond to the linguistic definition (which is usually Utterance objects).
class Segment(DBObject):
    ## Constructor
    #  @param self
    #  @param num (int) a unique number that can be used to identify this segment (assigned by the TRS Parser)
    #  @param start (float) start time (as recorded in the <Turn> tag)
    #  @param end (float) end time (as recorded in the <Turn> tag)
    #  @param speakers (list=[]) list of Speaker objects.
    #  @param utters (list=[]) list of Utterance objects that this Segment contains
    #  @param db_id (int=None) database table primary key (segments table). Is None if this Segment is not in the DB.
    def __init__(self, num, start, end, speakers=[], utters=[], db_id=None, user_adj_start=None, user_adj_end=None):
        super(DBObject, self).__init__()
        
        self.num = num
        self.speakers = speakers
        self.utters = utters
        self.start = start
        self.end = end
        self.db_id = db_id
        self.user_adj_start = user_adj_start
        self.user_adj_end = user_adj_end

    ## Iterates through this segment's list of speakers until a specified condition is reached.
    #  @param self
    #  @param cond_fcn (function) this function should accept a Speaker object, and return True (a value that Python considers True) when the iteration should stop. Otherwise it should return False (or None, 0, etc.)
    #  @returns (anything) returns whatever the cond_fcn returns, provided it evaluates to something Python considers True
    def _iterate_speakers_until(self, cond_fcn):
        result = False
        
        while not result and i < len(self.speakers):
            result = cond_fcn(self.speakers[i])
            i += 1

        return result

    ## Checks if this segment contains silence (i.e. if it contains the 'SIL' LENA speaker code)
    #  @param self
    #  @returns (boolean) True if one or more speakers is silence, False otherwise
    def has_silence(self):
        return self._iterate_speakers_until(
            lambda speaker: speaker.is_type(DBConstants.SPEAKER_TYPES.SILENCE))

    ## Checks if this segment contains a speaker that is considered 'far/distant' (eg. FAF, MAF)
    #  @param self
    #  @returns (boolean) True if one or more speakers is considered 'far , False otherwise.
    def has_distant(self):
        return self._iterate_speakers_until(
            lambda speaker: speaker.is_distance(DBConstants.SPEAKER_DISTANCES.FAR))

    ## Checks if this segment contains a speaker that is considered 'overlapping speech' (eg. OLN, OLF)
    #  @param self
    #  @returns (boolean) True if one or more speakers is considered to be overlapping speech.
    def has_overlapping_speech(self):
        return self._iterate_speakers_until(
            speaker.has_property(DBConstants.SPEAKER_PROPS.OVERLAPPING))

    ## Checks if this segment contains a speaker that is considered to be media. (i.e. TVF, TVN)
    #  @param self
    #  @returns (boolean) True if one or more speakers are media, False otherwise
    def has_media(self):
        return self._iterate_speakers_until(
            lambda speaker: speaker.has_property(DBConstants.SPEAKER_PROPS.MEDIA))

    ## Checks if this segment contains a speaker that represents nonverbal noise (i.e. NON, NOF)
    #  @param self
    #  @returns (boolean) True if one or more speakers are nonverbal noise, False otherwise
    def has_non_verbal_noise(self):
        return self._iterate_speakers_until(
            lambda speaker: speaker.has_property(DBConstants.SPEAKER_PROPS.NON_VERBAL_NOISE))

    ## See superclass description.
    def db_insert(self, db):
        super(Segment, self).db_insert(db)
        
        last_ids = db.insert('segments',
                             'start_time end_time user_adj_start user_adj_end'.split(),
                             [[self.start, self.end, self.user_adj_start, self.user_adj_end]],
                             )

        self.db_id = last_ids[0]

        #insert into this relationship table to record the mapping of segments to speaker codes
        #note: this will potentially insert multiple rows in a single call
        db.insert('segs_to_speaker_codes',
                  'seg_id speaker_code_id'.split(),
                  map(lambda person: [self.db_id, person.speaker_codeinfo.db_id], self.speakers),
                  )

    ## See superclass description.
    def db_delete(self, db):
        super(Segment, self).db_insert(db)
        if self.db_id != None:
            #note: db foreign key cascade property will cause this to automatically drop corresponding segs_to_speaker_codes
            db.delete('segments',
                           'id=?',
                           [self.db_id],
                           )

    ## See superclass description.
    #  Note: this method does not populate the 'num', or 'utters' attributes of segments. In addition, the segment's Speakers do not have their speaker_id attribute populated. The segments DB table does not bother to store this info, as currently, Utterance objects are only ever used after parsing a TRS file. This is probably not a very good reason - but if utterances or speaker objects ever need to be stored in the future, it's not difficult to add extra tables and link them to segments via foreign keys.
    @staticmethod
    def db_select(db, ids=[]):
        DBObject.db_select(db, ids)
        
        rows = db.select('segments',
                         'id start_time end_time user_adj_start user_adj_end'.split(),
                         DBObject._build_where_cond_from_ids(ids),
                         )

        seg_list = []
        for cur_row in rows:
            speaker_rows = db.select('segs_to_speaker_codes rel join speaker_codes sc on rel.speaker_code_id=sc.id',
                                     ['sc.code'],
                                     'rel.seg_id=?',
                                     [cur_row[0]],
                                     )

            #create the segment's speaker objects
            speaker_list = []
            for cur_speaker in speaker_rows:
                codeinfo = DBConstants.SPEAKER_CODES.get_option(cur_speaker[0])
                speaker = Speaker(None, codeinfo)
                speaker_list.append(speaker)

            seg = Segment(None, float(cur_row[1]), float(cur_row[2]), speaker_list, [], cur_row[0], cur_row[3], cur_row[4])
            seg_list.append(seg)

        return seg_list
