import sys
import os
import csv
import glob
import re

#windows shortcut launches this script in the 'bll_app\ directory., but the python path constains 'bll_app\custom_processing_scripts\'
#We must append the parent directory to the path so the python runtime can find our custom modules properly
sys.path.append( os.path.realpath('.') )

from utils.ui_utils import UIUtils

def main():
    filename = UIUtils.open_file(title='Select _all.txt File', filters=[UIUtils.build_file_filter('_all.txt', '_all.txt')])
    if not filename:
        exit()
    try:
        input_file = open(filename)
    except Exception as e:
        print 'Unable to open _all.txt file, exiting.'
        print 'Exception info: %s' % (e)

    reader = csv.reader(input_file, delimiter='\t')

    try:
        headers = reader.next()
        line = reader.next()
    except StopIteration:
        input_file.close()
        exit()

    filename_col = -1
    i = 0
    while i < len(headers) and filename_col < 0:
        if headers[i].lower() == 'file_name':
            filename_col = i
        i += 1

    if filename_col < 0:
        print 'Unable to locate "File_Name" column in _all.txt, exiting.'
        input_file.close()
        exit()

    absent_wavs = []
    script_dir = re.match(r'^(.+\\)_all\.txt$', filename).groups()[0]
    present_files = glob.glob(script_dir + '*.wav') #note: this is case insensitive
    present_dict = dict( zip(present_files, [True] * len(present_files)) )
    
    while line:
        wav_name = script_dir + line[filename_col][:-3] + 'wav'
        if not wav_name in present_dict:
            absent_wavs.append(wav_name)
            present_dict[wav_name] = True

        try:
            line = reader.next()
        except StopIteration:
            line = None

    if absent_wavs:
        print 'The following wav files are needed to run the praat script on _all.txt:'
        i = 0
        while i < len(absent_wavs):
            short_name = re.match(r'^.+\\([^\\]+\.wav)$', absent_wavs[i]).groups()[0]
            print '%d: %s' % (i + 1, short_name)
            i += 1
        print ''
    else:
        print 'All of the required wav files are present.'
            
    input_file.close()

main()
    
