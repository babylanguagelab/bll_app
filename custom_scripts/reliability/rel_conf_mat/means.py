from custom_scripts.reliability.rel_conf_mat.state_machine import StateMachine
from parsers.trs_parser import TRSParser
from custom_scripts.reliability.rel_conf_mat.rel_utils import *
from db.database import Database
from utils.enum import Enum
import os
import glob
import csv

input_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/input/'
output_file = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/AWC.csv'
envs = (
    'home',
    'home daycare',
    'daycare centre',
)
#envs = ('test',)

lena_db_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/'

container_types = Enum('TRANS_NO_OVERLAP TRANS_ALL_SPEECH LENA_NO_OVERLAP LENA_ALL_SPEECH'.split())

def get_trans_awc(container_list, lena_db, filename, exclude_angle=False, exclude_nonunderstandable=True, print_utters=False):
    trans_awc = 0
    lena_awc = 0
    utter_count = 0
    for container in container_list:
        if container[0].speaker:
            lena_code = container[0].speaker.speaker_codeinfo.code
            if lena_code in ('FAN', 'MAN'):
                if print_utters:
                    print 'Container:'

                found_utter = False
                for utter in container:
                    if not exclude_utter(utter, exclude_angle, exclude_nonunderstandable):
                        found_utter = True
                        cur_words = get_word_count(utter)
                        trans_awc += cur_words

                        if print_utters:
                            print 'Utterance:'
                            print 'Phrase: %s' % (utter.trans_phrase)
                            print 'Words: %d' % (cur_words)
                            print ''
                if found_utter:
                    utter_count += 1
                    lena_awc += get_lena_awc(lena_db, filename, container)

    return trans_awc, lena_awc, utter_count

def get_lena_awc(db, filename, container):
    name_parts = os.path.basename(filename).split('_')
    filename = '%s_%s.csv' % (name_parts[0], name_parts[1])
    start = container[0].start
    end = container[-1].end
    
    row = db.select(
        'data',
        ['col7'],
        where_cond='col46 = ? and round(col45, 3) = ? and round(col45 + col38, 3) = ?',
        params=[filename, start, end]
    )

    result = 0
    if row:
        result = row[0][0]
    else:
        print filename, start, end

    return result

def exclude_utter(utter, exclude_angle, exclude_nonunderstandable):
    return (exclude_angle and utter.is_trans_overlap) or (exclude_nonunderstandable and not is_understandable(utter))

def is_understandable(utter):
    result = True
    if utter.trans_phrase:
        phrase = utter.trans_phrase.lower().strip()
        result = phrase not in ('xxx', 'bbl')
        
    return result
    
def process_dir(path, env, par_code, writer):
    trs_filenames = glob.glob('%s*.trs' % (path))

    utter_counts = [0] * len(container_types)
    word_counts = [0] * len(container_types)

    lena_db = Database('%s%s.db' % (lena_db_path, env))

    for filename in trs_filenames:
        print '\n\tProcessing file %s' % (os.path.basename(filename))

        parser = TRSParser(filename)
        segs = get_trans_segs( parser.parse() )

        if segs:
            print '\tExamining range: %s (%0.2f) - %s (%0.2f)' % (get_time_str(segs[0].start), segs[0].start, get_time_str(segs[-1].end), segs[-1].end)

            sm = StateMachine()
            single, numbered_multi, unnumbered_multi = sm.divide_segs(segs)

            #for non-overlapping (no numbered_multi)
            trans_awc, lena_awc, utter_count = get_trans_awc(single, lena_db, filename, exclude_angle=True)
            word_counts[container_types.TRANS_NO_OVERLAP] += trans_awc
            word_counts[container_types.LENA_NO_OVERLAP] += lena_awc
            utter_counts[container_types.TRANS_NO_OVERLAP] += utter_count

            trans_awc, lena_awc, utter_count = get_trans_awc(unnumbered_multi, lena_db, filename, exclude_angle=True)
            word_counts[container_types.TRANS_NO_OVERLAP] += trans_awc
            word_counts[container_types.LENA_NO_OVERLAP] += lena_awc
            utter_counts[container_types.TRANS_NO_OVERLAP] += utter_count

            #for all speech
            trans_awc, lena_awc, utter_count = get_trans_awc(single, lena_db, filename, exclude_angle=False)
            word_counts[container_types.TRANS_ALL_SPEECH] += trans_awc
            word_counts[container_types.LENA_ALL_SPEECH] += lena_awc
            utter_counts[container_types.TRANS_ALL_SPEECH] += utter_count

            trans_awc, lena_awc, utter_count = get_trans_awc(numbered_multi, lena_db, filename, exclude_angle=False)
            word_counts[container_types.TRANS_ALL_SPEECH] += trans_awc
            word_counts[container_types.LENA_ALL_SPEECH] += lena_awc
            utter_counts[container_types.TRANS_ALL_SPEECH] += utter_count

            trans_awc, lena_awc, utter_count = get_trans_awc(unnumbered_multi, lena_db, filename, exclude_angle=False)
            word_counts[container_types.TRANS_ALL_SPEECH] += trans_awc
            word_counts[container_types.LENA_ALL_SPEECH] += lena_awc
            utter_counts[container_types.TRANS_ALL_SPEECH] += utter_count

    lena_db.close()
    trans_avg_no_overlap = 0
    trans_avg_all_speech = 0
    lena_avg_no_overlap = 0
    lena_avg_all_speech = 0

    if utter_counts[container_types.TRANS_NO_OVERLAP] > 0:
        trans_avg_no_overlap = word_counts[container_types.TRANS_NO_OVERLAP] / float(utter_counts[container_types.TRANS_NO_OVERLAP])
        #note: lena and transcriber measures have matching segments, so count is the same
        lena_avg_no_overlap = word_counts[container_types.LENA_NO_OVERLAP] / float(utter_counts[container_types.TRANS_NO_OVERLAP])
    if utter_counts[container_types.TRANS_ALL_SPEECH] > 0:
        trans_avg_all_speech = word_counts[container_types.TRANS_ALL_SPEECH] / float(utter_counts[container_types.TRANS_ALL_SPEECH])
        lena_avg_all_speech = word_counts[container_types.LENA_ALL_SPEECH] / float(utter_counts[container_types.TRANS_ALL_SPEECH])

    writer.writerow([
        par_code,
        word_counts[container_types.TRANS_NO_OVERLAP],
        utter_counts[container_types.TRANS_NO_OVERLAP],
        '%0.3f' % (trans_avg_no_overlap),
        word_counts[container_types.TRANS_ALL_SPEECH],
        utter_counts[container_types.TRANS_ALL_SPEECH],
        '%0.3f' % (trans_avg_all_speech),
        
        word_counts[container_types.LENA_NO_OVERLAP],
        utter_counts[container_types.TRANS_NO_OVERLAP],
        '%0.3f' % (lena_avg_no_overlap),
        word_counts[container_types.LENA_ALL_SPEECH],
        utter_counts[container_types.TRANS_ALL_SPEECH],
        '%0.3f' % (lena_avg_all_speech),
    ])

def setup_output_file():
    out_file = open(output_file, 'wb')
    writer = csv.writer(out_file)
    writer.writerow(['Participant', 'Transcriber AWC', '',         '',     ''              '',           '',     'LENA AWC',   '',         '',     '',             '',         ''    ])
    writer.writerow(['',            'No Overlap',      '',         '',     'With Overlap', '',           ''      'No Overlap', '',         '',     'With Overlap', '',         ''    ])
    writer.writerow(['',            'Words',           'Segments', 'Mean', 'Words',        'Segments',   'Mean', 'Words',      'Segments', 'Mean', 'Words',        'Segments', 'Mean'])
    
    return writer, out_file
    
def run():
    writer, out_file = setup_output_file()
    
    for i in range(len(envs)):
        cur_env = envs[i]
        print 'Processing environment: %s' % (cur_env)

        writer.writerow(['%s:' % (cur_env.capitalize())])
        
        input_dir = '%s%s/' % (input_path, cur_env)
        dir_contents = os.listdir(input_dir)

        for item in dir_contents:
            full_item_path = '%s%s/' % (input_dir, item)

            if os.path.isdir(full_item_path):
                process_dir(full_item_path, cur_env, item, writer)

        if i < len(envs) - 1:
            writer.writerow([''])

    out_file.close()

    
