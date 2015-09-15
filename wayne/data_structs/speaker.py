## @package data_structs.speaker

from data_structs.base_objects import BLLObject
from db.bll_database import DBConstants

## This class represents a LENA-defined speaker.
#  Every speaker has a LENA speaker code (e.g. MAN, FAN, CHF).
class Speaker(BLLObject):
    ## Constructor
    #  @param self
    #  @param speaker_id (string) this is the 'id' name given to the speaker in the TRS file (eg. 'spk1', 'spk2', etc.)
    #  @param speaker_codeinfo (CodeInfo) A CodeInfo object (code-encapsulating object with info from the DB speaker_codes table) corresponding to this Speaker's LENA speaker code
    def __init__(self, speaker_id, speaker_codeinfo):
        self.speaker_id = speaker_id
        self.speaker_codeinfo = speaker_codeinfo

    ## Checks if this speaker has a particular speaker type.
    #  @param self
    #  @param speaker_type (int) the type to check for - this should be one of the options from the enum DBConstants.SPEAKER_TYPES
    #  @returns (boolean) True if this speaker is of type 'speaker_type', False otherwise
    def is_type(self, speaker_type):
        return self.speaker_codeinfo and self.speaker_codeinfo.is_speaker_type(speaker_type)

    ## Checks if this speaker has particular distance (near/far)
    #  @param self
    #  @param distance (int) the distance to check for - this should be one of the options from the enum DBCONSTANTS.SPEAKER_DISTANCES
    #  @returns (boolean) True if this speaker has the specified distance, False otherwise
    def is_distance(self, distance):
        return self.speaker_codeinfo and self.speaker_codeinfo.is_distance(distance)

    ## Checks if this speaker has a particular property (properties include being media, being overlapping, or being non-verbal noise)
    #  @param self
    #  @param prop (int) the property to check for. This should be one of the options from the enum DBConstants.SPEAKER_PROPS. See BLLDatabase._get_speaker_props_enum() for possible options.
    def has_property(self, prop):
        return self.speaker_codeinfo and self.speaker_codeinfo.has_property(prop)

    ## Accessor method for codeinfo attribute.
    #  @param self
    #  @returns (CodeInfo) A CodeInfo object (parsers.codeinfo.py)
    def get_codeinfo(self):
        return self.speaker_codeinfo
