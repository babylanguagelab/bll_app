from __future__ import print_function
import re
import time
import json
import glob
import sys
import os

def load_replacements_file(filePath): #'replacement_dict.json'
    with open(filePath) as f:
        replacements = json.load(f)
    return replacements

def parse_file(inFile, outFile, repalcements):

    with open(inFile, 'rb') as inF:
        with open(outFile, 'wb') as outF:
        
            # print('\n' + os.path.split(inFile)[1] + ':')
            
            for line in inF:
                for node in replacements.keys():
                    if re.search(r'<{}\b'.format(node), line): # word boundary is important here
                        for name, value in replacements[node].items():
                            line = re.sub(r'{}="[a-zA-Z0-9_.:\-]*"'.format(name),
                                          r'{}="{}"'.format(name, value),
                                          line)
                            # print('\t- changed {}/{} to {}'.format(node, name, value))
                outF.write(line)


if __name__ == '__main__':
    itsFolder = sys.argv[1]

    # Check that the ist files directory exists
    if not os.path.isdir(itsFolder):
        raise Exception('Not a valid folder name')

    # Get paths of the its files
    files = glob.glob(os.path.join(itsFolder, '*.its'))
    if not files:
        raise Exception('There are no its files in the folder')

    # Make the output folder
    outFolder = itsFolder + '_anonymised'
    if os.path.isdir(outFolder):
        raise Exception('The output folder already exists')
    else:
        os.mkdir(outFolder)

    # Load the replacements dictionary
    replacements = load_replacements_file('./replacements_dict.json')

    # Process all files
    for inFile in files:

        _, name = os.path.split(inFile)
        outFile = os.path.join(outFolder, name)

        parse_file(inFile, outFile, replacements)
        print('done {}'.format(name))
    
    print('\n-----\nProcessed {} files'.format(len(files)))
