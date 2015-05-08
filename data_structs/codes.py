## @package data_structs.codes

from data_structs.base_objects import BLLObject
from parsers.errors import *
from utils.enum import Enum

import re

## This class provides information about/validation for a particular code. This could be a transcriber code, a LENA speaker code, a LENA notes code, or other potential types of codes.
# A code can have any number of options. Each option is a specific string value that the code can take on (eg. a LENA speaker code has options like 'MAN', 'FAN', etc.).
# This class also provides the ability fo valide code options that have been read from a TRS file.
class Code(object):
    ## Constructor
    #  @param self
    #  @param options_dict (dictionary) this is a dictionary with one key for each possible option. The value for each key must be a CodeInfo object for that particular option.
    def __init__(self, options_dict):
        self.options_dict = options_dict

    ## Retreives a CodeInfo object for a specified option.
    #  @param self
    #  @param code_str (string) a string representing the option to lookup (eg. 'MAN' or 'FAN' for a LENA speaker code, 'M' or 'F' for transcriber code 1, etc.)
    #  @returns (CodeInfo) a CodeInfo object that can be used to retreive further details about the individual option
    def get_option(self, code_str):
        result = None
        if code_str in self.options_dict:
            result = self.options_dict[code_str] #returns codeinfo object
            
        return result

    ## Retreives a list of all possible options for this code.
    #  @param self
    #  @returns (list) list of strings, one for each possible option
    def get_all_options_codes(self):
        return self.options_dict.keys()

    ## This function returns a list of functions that are called, one by one, upon validation.
    # Each function should accept a single argument, a string containing the option text. They should return an array containing any error messages to present to the UI (or empty list if none).
    # @param self
    # @returns (list) list of functions
    def get_tests(self):
        #For validation applying to all types of codes, add new test functions here, and append the name to the returned list.
        #For validation applying to one type of code, create a subclass and override this function.
        #Test functions should accept a single parameter: a string representing the transcriber code currently being validated.
        #Test functions should return an array containing error messages from all errors encountered (or empty list if none)
        return []

    ## Validates an option string for this Code object.
    # To do so, it retreives a list of test functions from get_tests() and executes them one by one.
    # The resulting lists are concatenated and the final list is returned.
    # @param self
    # @param cd_str (string) string for the code option being validated.
    # @returns (list) list of error messages, or empty list if no errors were encountered.
    def is_valid(self, cd_str):
        errors = []
        for test_fcn in self.get_tests():
            error_msgs = test_fcn(cd_str)
            if error_msgs:
                errors.extend(error_msgs)
            
        return errors

## Transcriber codes 1, 2, and 4 have some things in common. For example, they are all single-character codes (unlike
# code 3, which may contain multiple characters). This class encapsulates common validation tests for codes 1, 2, and 4.
class TranscriberCode124(Code):
    ## See superclass description.
    def __init__(self, options_dict):
        Code.__init__(self, options_dict)

    ## See superclass description.
    def get_tests(self):
        #grab tests from superclass
        tests = Code.get_tests(self)

        def char_test(cd_str):
            errors = []
            #ensure the string is composed only of characters in the set
            invalid_re = '[^%s]' % ( reduce(lambda accum, key: accum + key, self.options_dict.keys()) )
            it = re.finditer(invalid_re, cd_str)
            matches = list(it)
            if matches:
                invalid_cds = ''
                for i in range(len(matches)):
                    invalid_cds += '"' + matches[i].group() + '"'
                    if i < len(matches) - 1:
                        invalid_cds += ', '
                    
                errors.append('Invalid code character(s): %s' % (invalid_cds))

            return errors

        #transcriber codes 1, 2, and 4 must only consist of a single character
        def len_test(cd_str):
            errors = []
            if len(cd_str) > 1:
                errors.append('This code should not contain more than one character.')
                
            return errors

        tests.extend([char_test, len_test])
        
        return tests

## The third transcriber code is slightly different from the others because it can contain multiple characters. This subclass holds data about the code and provides some special overridden methods that work on multiple characters.
class TranscriberCode3(Code):
    ## See superclass description.
    def __init__(self, options_dict):
        Code.__init__(self, options_dict)

    ## See superclass description.
    def get_tests(self):
        #grab tests from superclass
        tests = Code.get_tests(self)
        
        def char_test(cd_str):
            errors = []
            #ensure the string is composed only of characters in the set
            invalid_re = r'[^%s0-9]' % ( reduce(lambda accum, key: accum + key, self.options_dict.keys()) )
            it = re.finditer(invalid_re, cd_str)
            matches = list(it)

            invalid_re2 = r'([^IC][0-9]+)' #make sure it's not just a single number without a preceding I or C. This should really be integrated into the above regex somehow...
            it2 = re.finditer(invalid_re2, cd_str)
            matches2 = list(it2)

            all_matches = []
            i = 0
            
            if matches is not None:
                all_matches.extend(matches)
            if matches2 is not None:
                all_matches.extend(matches2)
                    
            if all_matches:
                invalid_cds = ''
                for i in range(len(all_matches)):
                    invalid_cds += '"' + all_matches[i].group() + '"'
                    if i < len(all_matches) - 1:
                        invalid_cds += ', '
                    
                errors.append('Invalid code character(s): %s' % (invalid_cds))

            return errors

        #since we can have multiple characters in a single code here, ensure there are no duplicate characters in the code string
        def freq_test(cd_str):
            errors = []
            freq_dict = {}
            for c in cd_str:
                if c in freq_dict and not c.isdigit():
                    errors.append('Code contains more than one "%c".' % c)
                    freq_dict.pop(c) #remove so we won't get redundant errors if c is encountered again
                else:
                    freq_dict[c] = 1

            return errors

        #according to the transcriber manual, if code 3 contains a U or F, it may not contain a C or I.
        def link_test(cd_str):
            errors = []
            if 'U' in cd_str and 'F' in cd_str and ('I' in cd_str or 'C' in cd_str):
                errors.append('Codes containing U and F may not contain C or I')

            return errors

        #append the subclass tests
        tests.extend([char_test, freq_test, link_test])
        
        return tests

## This class holds information about a particular code option. A 'code option' is a particular value that a code can have. For example, transcriber code 1 may be set to one of the following options: ('M', 'F', 'T', 'O', 'C', 'U'). See the transcriber manual (or the transcriber_codes db table) for details about the options available for each transcriber code. Similarly, a LENA speaker code can have many different options: ('FAN', "MAN', 'NON', 'TVF', etc.). See the speaker_codes db table or the LENA documentation for more info about these codes. Other types of codes also exist.
class CodeInfo(BLLObject):
    ## Constructor
    #  @param self
    #  @param db_id (int) database id for this code option. This is from one of the code tables like transcriber_codes, lena_nodes_codes, etc.
    #  @param code (string) the option text
    #  @param desc (string) a description for this option that can be used for display purposes in the UI
    #  @param is_linkable (boolean integer) If an option is linkable (param is 1), then segments containing that code option will be considered when linking C/I transcriber codes. If an option is not linkable (param is 0), then segments containing that code option will be skipped when linking C/I transcriber codes (i.e. the segments can exist between I and C coded segments without causing errors).
    #  @param distance (int) one of the options from the Enum DBConstants.SPEAKER_DISTANCES (if this class is not being instantiated for a speaker code, this can be set to DBConstants.SPEAKER_CODES.NA).
    #  @param speaker_type (int) one of the options from the Enum DBConstants.SPEAKER_TYPES (if this class is not being instantiated for a speaker code, this can be set to DBConstants.SPEAKER_TYPES.NA)
    #  @param props (list) list of ints - each should be an option from DBConstants.SPEAKER_PROPS. Pass empty list if properties are not applicable or needed for this code.
    def __init__(self,
                 db_id,
                 code,
                 desc,
                 is_linkable,
                 distance,
                 speaker_type,
                 props=[]):
        self.db_id = db_id
        self.desc = desc
        self.code = code
        self.is_linkable = is_linkable
        self.distance = distance
        self.speaker_type = speaker_type
        self.props_dict = dict(zip(props, [True] * len(props)))

    ## Checks if this option has a given property from DBConstants.SPEAKER_PROPS.
    # These properties record secondary characteristics like whether or not the option represents media noise, or overlapping speach.
    #  @param self
    #  @param prop (int) one of the options from DBConstants.SPEAKER_PROPS
    #  @returns (boolean) True if this option has the specified property, False otherwise.
    def has_property(self, prop):
        return prop in self.props_dict

    ## Checks if this option is linkable.
    # If an option is linkable, then segments containing that code option will be considered when linking C/I transcriber codes. If an option is not linkable, then segments containing that code option will be skipped when linking C/I transcriber codes (i.e. the segments can exist between I and C coded segments without causing errors).
    # @param self
    # @returns (boolean) True if this option is linkable, False otherwise
    def is_linkable(self):
        return is_linkable

    ## Checks if this option has a particular distance property (eg. NEAR, FAR, NA)
    # @param self
    # @param distance (int) one of the options from DBConstants.SPEAKER_DISTANCES (pass the NA option if distance is not applicable for this code option).
    # @returns (boolean) True if this option has the distance property, False otherwise.
    def is_distance(self, distance):
        return self.distance == distance

    ## Checks if this option has a given speaker type (where speaker types are defined as for transcriber code 1 in the transcriber manual).
    # @param self
    # @param speaker_type (int) one of the options from DBConstants.SPEAKER_TYPES (pass the NA option if speaker type is not applicable for this code option)
    # @returns (boolean) True if this option has the specified speaker type, False otherwise.
    def is_speaker_type(self, speaker_type):
        return self.speaker_type == speaker_type

    ## Returns the description for this option.
    # @param self
    # @returns (string) description text
    def get_code_desc(self):
        return self.desc

    ## Returns the code string for this option.
    # @param self
    # @returns (string) an options string (like 'MAN' or 'FAN')
    def get_code(self):
        return self.code
