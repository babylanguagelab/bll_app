import logging
import csv
import os
import glob
from parsers.trs_parser import TRSParser
from custom_scripts.reliability.rel_conf_mat.state_machine import StateMachine
from custom_scripts.reliability.rel_conf_mat.rel_utils import *

LENA_CODES = 'CHF CHN CXF CXN FAF FAN MAF MAN NOF NON OLF OLN TVF TVN SIL FUZ CRY/VFX'.split()

LENA_CODE_CATS = 'CHN CXN FAN MAN SIL Far_Speech CRY/VFX OLN OLF Noise CHF CXF FAF MAF TVN TVF NON NOF FUZ'.split()

LENA_CODES_TO_CATS = {
    'CHN': ['CHN'],
    'CXN': ['CXN'],
    'FAN': ['FAN'],
    'MAN': ['MAN'],
    'SIL': ['SIL'],
    'CHF': ['Far_Speech', 'CHF'],
    'CXF': ['Far_Speech', 'CXF'],
    'FAF': ['Far_Speech', 'FAF'],
    'MAF': ['Far_Speech', 'MAF'],    
    'CRY/VFX': ['CRY/VFX'],
    'OLN': ['OLN'],
    'OLF': ['OLF'],
    'TVN': ['Noise', 'TVN'],
    'TVF': ['Noise', 'TVF'],
    'NON': ['Noise', 'NON'],
    'NOF': ['Noise', 'NOF'],
    'FUZ': ['FUZ'],
}

TRANS_CODES = 'T O F M C U non-speech(>=1sec) non-speech(<1sec) overlap'.split()
MIN_UTTER_TIMESPAN = 1 #seconds

input_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/input/'
output_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/'
envs = (
    'home',
    'home daycare',
    'daycare centre',
)

def get_timespan(utter):
    return utter.end - utter.start

def print_container(container):
    container_str = '\t'
    for i in range(len(container)):
        container_str += '['
        speaker = container[i].speaker.speaker_codeinfo.code if container[i].speaker else 'None'
        time_range = '%s-%s (%s-%s)' % ( get_time_str(container[i].start), get_time_str(container[i].end), container[i].start, container[i].end )
        trans_phrase = container[i].trans_phrase if container[i].trans_phrase else 'None'
        trans_codes = '|%s|' % ('|'.join(container[i].trans_codes) if len(container[i].trans_codes) == 4 and container[i].trans_codes != ([''] * 4) else 'None')
        container_str += '%s;%s;%s;%s' % (speaker, time_range, trans_phrase, trans_codes)
        container_str += ']'
        if i < len(container) - 1:
            container_str += ', '

    print container_str
        
def build_matrix(row_axis, col_axis):
    matrix = {}
    
    # for i in range(len(LENA_CODES)):
    #     matrix[LENA_CODES[i]] = {}
    #     for j in range(len(TRANS_CODES)):
    #         matrix[LENA_CODES[i]][TRANS_CODES[j]] = 0

    for i in range(len(col_axis)):
        matrix[col_axis[i]] = {}
        for j in range(len(row_axis)):
            matrix[col_axis[i]][row_axis[j]] = 0

    return matrix

def collapse_columns(in_matrix):
    out_matrix = build_matrix(TRANS_CODES, LENA_CODE_CATS)

    for trans_code in TRANS_CODES:
        for lena_code in LENA_CODES:
            cats = LENA_CODES_TO_CATS[lena_code]
            for cur_cat in cats:
                out_matrix[cur_cat][trans_code] += in_matrix[lena_code][trans_code]

    return out_matrix

def output_matrix(wide_matrix, filename, count_single, count_numbered_multi, count_unnumbered_multi, count_angle_brackets):
    out_file = open(filename, 'wb')
    writer = csv.writer(out_file)

    narrow_matrix = collapse_columns(wide_matrix)

    writer.writerow([''] + LENA_CODE_CATS)

    #raw counts
    for trans_code in TRANS_CODES:
        row = [trans_code]

        i = 0
        while i < len(LENA_CODE_CATS):
            count = narrow_matrix[ LENA_CODE_CATS[i] ][trans_code]
            cell = '%d' % (count)
            row.append(cell)
            i += 1
                
        writer.writerow(row)

    #blank row
    writer.writerow([''] * len(LENA_CODE_CATS))

    #output percentages - column-wise (each column is one LENA code)
    writer.writerow(['Column-wise Percentages'] + [''] * (len(LENA_CODE_CATS) - 1))    
    writer.writerow([''] + LENA_CODE_CATS)

    col_totals = []
    for lena_code in LENA_CODE_CATS:
        col_totals.append(sum_col(narrow_matrix, lena_code))
    
    for trans_code in TRANS_CODES:
        row = [trans_code]

        i = 0
        while i < len(LENA_CODE_CATS):
            count = narrow_matrix[ LENA_CODE_CATS[i] ][trans_code]
            ratio = 0
            if col_totals[i] > 0:
                ratio = float(count) / float(col_totals[i]) * 100
            cell = '%0.3f%%' % (ratio)
            row.append(cell)
            i += 1
                
        writer.writerow(row)

    #blank row
    writer.writerow([''] * len(LENA_CODE_CATS))

    #output percentages - row-wise (each row is one transcriber code)
    writer.writerow(['Row-wise Percentages'] + [''] * (len(LENA_CODE_CATS) - 1))    
    writer.writerow([''] + LENA_CODE_CATS)

    for trans_code in TRANS_CODES:
        row = [trans_code]
        row_total = sum_row(narrow_matrix, trans_code)

        i = 0
        while i < len(LENA_CODE_CATS):
            count = narrow_matrix[ LENA_CODE_CATS[i] ][trans_code]
            ratio = 0
            if row_total > 0:
                ratio = float(count) / float(row_total) * 100
            cell = '%0.3f%%' % (ratio)
            row.append(cell)
            i += 1
                
        writer.writerow(row)

    writer.writerow([''] * len(LENA_CODE_CATS))
    writer.writerow(['Utterance stats:'] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Total utterances:', count_single + count_numbered_multi + count_unnumbered_multi] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Single speaker:', count_single] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Numbered speaker:', count_numbered_multi] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Multi-line speakers:', count_unnumbered_multi] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Angle brackets:', count_angle_brackets] + [''] * (len(LENA_CODE_CATS) - 1))
    
    out_file.close()

#for narrow matrix
def sum_matrix(matrix):
    total = 0
    for lena_code in LENA_CODE_CATS:
        for trans_code in TRANS_CODES:
            total += matrix[lena_code][trans_code]

    return total

#for narrow matrix
def sum_col(matrix, lena_code):
    total = 0
    for trans_code in TRANS_CODES:
        total += matrix[lena_code][trans_code]

    return total
    
#for narrow matrix
def sum_row(matrix, trans_code):
    total = 0
    for lena_code in LENA_CODE_CATS:
        if lena_code not in ['Far_Speech', 'Noise']:
            total += matrix[lena_code][trans_code]

    return total

def print_non_speech_containers(container, lena_code):
    if lena_code not in 'TVN TVF NOF NON SIL FUZ'.split():
        lena_notes = container[0].lena_notes.split() if container[0].lena_notes else []
        if ( not lena_notes or ('SIL' not in lena_notes and 'CRY' not in lena_notes and 'VFX' not in lena_notes) ):
            print_container(container)

#Notes:
#Singles will never have transcriber overlap, since that requires an additional line (and therefore would go into one of the multi categories)
def process_single(single, matrix):
    for container in single:
        if container[0].speaker:
            lena_code = container[0].speaker.speaker_codeinfo.code
            lena_notes = container[0].lena_notes.split() if container[0].lena_notes else []
            
            if 'SIL' in lena_notes:
                lena_code = 'SIL'
            elif 'CRY' in lena_notes or 'VFX' in lena_notes:
                lena_code = 'CRY/VFX'
                
            trans_code = 'non-speech(>=1sec)'
            if not container[0].trans_phrase and get_timespan(container[0]) < MIN_UTTER_TIMESPAN:
                trans_code = 'non-speech(<1sec)'
            
            elif container[0].trans_phrase and len(container[0].trans_codes) == 4 and container[0].trans_codes[0] in matrix[lena_code]:
                if container[0].is_trans_overlap:
                    trans_code = 'overlap'
                else:
                    trans_code = container[0].trans_codes[0]

            matrix[lena_code][trans_code] += 1

            # if (get_timespan(container[0]) < MIN_UTTER_TIMESPAN and
            #     lena_code == 'CHN' and
            #     trans_code != 'T' and not trans_code.startswith('non-speech')
            # ):
            #     print_container(container)
            

def process_numbered_multi(multi, matrix):
    for container in multi:
        if container[0].speaker: #numbered speakers should always be the same
            lena_code = container[0].speaker.speaker_codeinfo.code
            trans_code = 'overlap' #transcriber has numbered this segment, so take that as an indication of overlap
            matrix[lena_code][trans_code] += 1

            # if (get_timespan(container[0]) < MIN_UTTER_TIMESPAN and
            #     lena_code == 'CHN' and
            #     trans_code != 'T' and not trans_code.startswith('non-speech')
            # ):
            #     print_container(container)

            #if trans_code == 'non-speech(>=1sec)':
            #    print_non_speech_containers(container, lena_code)
            
def process_unnumbered_multi(multi, matrix):
    for container in multi:
        if container[0].speaker:
            lena_code = container[0].speaker.speaker_codeinfo.code
            lena_notes = container[0].lena_notes.split() if container[0].lena_notes else []
            
            if 'SIL' in lena_notes:
                lena_code = 'SIL'
            elif 'CRY' in lena_notes or 'VFX' in lena_notes:
                lena_code = 'CRY/VFX'
                
            i = 0
            while i < len(container):
                trans_code = 'non-speech(>=1sec)'

                if not container[i].trans_phrase and get_timespan(container[i]) < MIN_UTTER_TIMESPAN:
                    trans_code = 'non-speech(<1sec)'
                    i += 1

                elif container[i].is_trans_overlap:
                    trans_code = 'overlap'
                    i += 1
                    while i < len(container) and container[i].is_trans_overlap:
                        i += 1

                else:
                    if container[i].trans_phrase and len(container[i].trans_codes) == 4 and container[i].trans_codes[0] in matrix[lena_code]:
                        trans_code = container[i].trans_codes[0]
                    i += 1

                matrix[lena_code][trans_code] += 1

                # if (get_timespan(container[0]) < MIN_UTTER_TIMESPAN and
                #     lena_code == 'CHN' and
                #     trans_code != 'T' and not trans_code.startswith('non-speech')
                # ):
                #     print_container(container)

                #if trans_code == 'non-speech(>=1sec)':
                #    print_non_speech_containers(container, lena_code)

def check_log_file(path):
    if not os.path.exists(path):
        logfile = open(path, 'w')
        logfile.close()

def count_angle_bracket_segs(segs):
    count = 0
    for container in segs:
        found = False
        i = 0
        while not found and i < len(container):
            found = container[i].is_trans_overlap
            i += 1
        if found:
            count += 1

    return count

def process_dir(full_item_path, output_dir):
    trs_filenames = glob.glob('%s*.trs' % (full_item_path))
    matrix = build_matrix(TRANS_CODES, LENA_CODES)

    for filename in trs_filenames:
        print '\n\tProcessing file %s' % (os.path.basename(filename))

        parser = TRSParser(filename)
        segs = get_trans_segs( parser.parse() )
        if segs:
            print '\tExamining range: %s - %s' % (get_time_str(segs[0].start), get_time_str(segs[-1].end))

            sm = StateMachine()
            single, numbered_multi, unnumbered_multi = sm.divide_segs(segs, use_lena_segmentation=False)

            count_single = len(single)
            count_numbered_multi = len(numbered_multi)
            count_unnumbered_multi = len(unnumbered_multi)
            count_angle_brackets = count_angle_bracket_segs(single) + count_angle_bracket_segs(numbered_multi) + count_angle_bracket_segs(unnumbered_multi)

            process_single(single, matrix)
            process_numbered_multi(numbered_multi, matrix)
            process_unnumbered_multi(unnumbered_multi, matrix)

    output_name = '%s%s-matrix.csv' % (output_dir, full_item_path.split('/')[-2])
    output_matrix(matrix, output_name, count_single, count_numbered_multi, count_unnumbered_multi, count_angle_brackets)

def run():
    LOGFILE = 'logs/confusion.log'
    
    #create log file if it doesn't exist
    check_log_file(LOGFILE)
    #set up logging
    logging.basicConfig(level=logging.ERROR,
                        filename=LOGFILE,
                        format='%(asctime)s %(message)s') #prefix each message with a timestamp

    for cur_env in envs:
        print 'Processing environment: %s' % (cur_env)
        output_dir = '%s%s/' % (output_path, cur_env)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        
        input_dir = '%s%s/' % (input_path, cur_env)
        dir_contents = os.listdir(input_dir)

        for item in dir_contents:
            full_item_path = '%s%s/' % (input_dir, item)

            if os.path.isdir(full_item_path):
                process_dir(full_item_path, output_dir)
