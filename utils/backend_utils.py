## @package utils.backend_utils

import re
import logging
import logging.config
import os

## This class contains a collection of static methods for various backend-ish uses. This class should never
#  be instantiated. Similar UI tools should go in the UIUtils (utils.ui_utils.py) class.
class BackendUtils(object):
    @staticmethod
    ## Sets up logging for an application.
    #  @param full_log_filename (string) Full path to the log file to use - if the file does not exist, it will be created.
    def setup_logging(full_log_filename):
        #create log file if it doesn't exist
        if not os.path.exists(full_log_filename):
            logfile = open(full_log_filename, 'w')
            logfile.close()

            #set up basic logging
            logging.basicConfig(level=logging.ERROR,
                                filename=full_log_filename,
                                format='%(asctime)s %(message)s') #prefix each message with a timestamp

    ## Counts the number of words in a string.
    #  @param text (string) the string to operate upon.
    #  @returns (int) number of words in the string. Hyphens and apostrophies will be converted to spaces before the count is performed, so contractions or hyphenated expressions will count as multiple words (e.g. "can't" => "can t" = 2 words).
    @staticmethod
    def get_word_count(text):
        #strip out any punctuation, replacing it with a space. This means that contractions and hyphonated words will count as two words (as their apostrophy is relaced with a space).
        text = re.sub(r'[\.\'\"\?\,\!\:;\-\\\/\(\)]', ' ', text)
        
        return len(text.split())
    
    ## Spilts a given time duration (expressed in seconds) into hours, minutes, and seconds.
    #  @param total_sec (int/float) an amount of time, expressed in seconds
    #  @returns (int, int, int/float) three values representing hours, minutes (< 60), seconds (< 60)
    @staticmethod
    def break_time(total_sec):
        hours = None
        mins = None
        secs = None
        if total_sec != None:
            #these two lines use the int() function, which will round down to the nearest whole second - the remainder will come out in the secs calculation
            hours = int(total_sec) / (60 * 60)
            mins = ( int(total_sec) - (hours * 60 * 60) ) / 60
            secs = total_sec - (hours * 60 * 60) - (mins * 60) #this may be a float

        return hours, mins, secs

    ## Creates a formatted string (suitable for display) from a given time duration (expressed in seconds)
    #  @param total_sec (int/float) an amount of time, expressed in seconds
    #  @param pad_hour_min (boolean=True) Set whether or not to zero-pad hours and minutes placeholders (seconds are always zero-padded)
    #  @param show_hours (boolean=True) Set whether or not to show hours placeholder
    #  @param show_decimals (boolean=True) Set whether or not to show seconds decimal places (if not, seconds are truncated - not rounded!)
    #  @returns (string) a string in the format 'hh:mm:ss.ss'
    @staticmethod
    def get_time_str(total_sec, pad_hour_min=True, show_hours=True, show_decimals=True):
        result = '-'
        hours, mins, secs = BackendUtils.break_time(total_sec)
        if hours != None: #if one is valid, all will be
            #hours placeholder
            if show_hours:
                result = ('%02d:' if pad_hour_min else '%d:') % (hours)
            else:
                result = ''

            #minutes placeholder
            result += ('%02d:' if pad_hour_min else '%d:') % (mins)

            #seconds placeholder
            if show_decimals:
                result += '%s%0.2f' % ('0' if secs < 10 else '', secs)
            else:
                result += '%02d' % (int(secs))
                
        return result

    @staticmethod
    def time_str_to_float(time_str):
        chunks = time_str.split(':')
        
        if len(chunks) > 3: #note: if time_str == '', then the loop below will crash upon trying to convert the chunks[i] to a float
            raise Exception('Cannot convert time string "%s" to float - invalid format.' % (str(time_str)))

        result = 0
        for i in range(len(chunks)):
            result += float(chunks[i]) * (60.0 ** (len(chunks) - i - 1))

        return result

    ## Accepts a string (containing only digits), and prefixes it with a zero if it is < 10
    #  @param num_str (string) an integer in string form
    #  @returns (string) if num_str contains an integer that is less than 10, returns a new string that is num_str prefixed with a zero; otherwise returns num_str
    @staticmethod
    def pad_num_str(num_str):
        return '0%s' % (num_str) if int(num_str) < 10 else num_str
    
    ## Converts a date (string) to an integer that's suitable for comparison.
    #  @param date_str (string) date string in the form 'mm/dd/yyyy', followed by an optional space and 'hh:mm'
    #  @returns (int) an integer representing this date - safe to use for comparing dates
    @staticmethod
    def _get_date_val(date_str):
        #format is 'mm/dd/yyyy', then optionally ' hh:mm'
        parts = re.split(r'[/\s:]', date_str)
        parts[0], parts[1], parts[2] = parts[2], parts[0], parts[1]

        date_str = ''
        for cur_part in parts:
            date_str += BackendUtils.pad_num_str(cur_part)
        
        return int(date_str)

    ## Checks if a given string contains a float.
    #  @param num_str (string) the string to check
    #  @returns (boolean) True if num_str contains a float, False otherwise
    @staticmethod
    def is_float(num_str):
        result = False
        
        #this is not the right way to do it...
        try:
            num = float(num_str)
            result = True
        except ValueError:
            pass

        return result
