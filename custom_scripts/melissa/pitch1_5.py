import os
import sys
import csv
import glob
import os
import logging
import re

from collections import OrderedDict

from db.csv_database import CSVDatabase
from utils.praat_interop import PraatInterop

pitch_delta_threshold = 50
lag_cutoff = 2.0

input_dir = ('C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\test_in\\10 mo',
             'C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\test_in\\14 mo',
             )
wav_dir = ('C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\wav\\10 mo',
           'C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\wav\\14 mo',
           )
out_dir = ('C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\test_out15\\10 mo',
           'C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\test_out15\\14 mo',
           )

def create_db():
    col_datatypes = (
        int,
        str, #filename
        str, #csv cols from here down
        str,
        str,
        str,
        float,
        float,
        float,
        float,
        str,
        bool,
        )

    db = CSVDatabase(col_datatypes)

    return db, col_datatypes

def float_or_none(val):
    return float(val) if val != '--undefined--' else None

def get_praat_vals(start, end, wav_filename):
    socket = PraatInterop.create_serversocket()

    PraatInterop.send_commands([
            'Extract part... %f %f yes' % (start, end),
            ])

    #PraatInterop.send_commands( PraatInterop.get_octave_corrected_pitch_script() )
    PraatInterop.send_commands( PraatInterop.get_pitch_sample_vals_script(start, end, wav_filename) )
    pt1_time, pt1_pitch, pt2_time, pt2_pitch, min_pitch, max_pitch, mean_pitch = PraatInterop.socket_receive(socket)

    wav_object_name = (os.path.basename(wav_filename)[:-4])
    PraatInterop.send_commands([
            #'Remove', #pitch
            'select Sound %s' % (wav_object_name),
            'Remove',
            'select LongSound %s' % (wav_object_name),
            ]) 

    return (float_or_none(pt1_time),
            float_or_none(pt1_pitch),
            float_or_none(pt2_time),
            float_or_none(pt2_pitch),
            float_or_none(min_pitch),
            float_or_none(max_pitch),
            float_or_none(mean_pitch),
            )

def append_calced_cols(db, col_dict):
    #mother
    db.add_column('question_type', str)
    col_dict['Question Type'] = 'question_type'

    db.add_column('m_pt1_pitch', float)
    col_dict['Mother Point 1 Pitch'] = 'm_pt1_pitch'

    db.add_column('m_pt2_pitch', float)
    col_dict['Mother Point 2 Pitch'] = 'm_pt2_pitch'

    db.add_column('m_pitch_delta', float)
    col_dict['Mother Pitch Delta'] = 'm_pitch_delta'
    
    db.add_column('m_max_pitch', float)
    col_dict['Mother Max Pitch'] = 'm_max_pitch'

    db.add_column('m_min_pitch', float)
    col_dict['Mother Min Pitch'] = 'm_min_pitch'

    db.add_column('m_mean_pitch', float)
    col_dict['Mother Mean Pitch'] = 'm_mean_pitch'

    db.add_column('m_pitch_cat', float)
    col_dict['Mother Pitch Category'] = 'm_pitch_cat'

    #baby
    db.add_column('b_start_time', float)
    col_dict['Baby Start Time'] = 'b_start_time'

    db.add_column('b_end_time', float)
    col_dict['Baby End Time'] = 'b_end_time'

    db.add_column('b_duration', float)
    col_dict['Baby Duration'] = 'b_duration'

    db.add_column('b_lag_time', float)
    col_dict['Baby Lag Time'] = 'b_lag_time'
    
    db.add_column('b_pt1_pitch', float)
    col_dict['Baby Point 1 Pitch'] = 'b_pt1_pitch'

    db.add_column('b_pt2_pitch', float)
    col_dict['Baby Point 2 Pitch'] = 'b_pt2_pitch'

    db.add_column('b_pitch_delta', float)
    col_dict['Baby Pitch Delta'] = 'b_pitch_delta'

    db.add_column('b_max_pitch', float)
    col_dict['Baby Max Pitch'] = 'b_max_pitch'

    db.add_column('b_min_pitch', float)
    col_dict['Baby Min Pitch'] = 'b_min_pitch'

    db.add_column('b_mean_pitch', float)
    col_dict['Baby Mean Pitch'] = 'b_mean_pitch'

    db.add_column('b_pitch_cat', float)
    col_dict['Baby Pitch Category'] = 'b_pitch_cat'

    #match
    db.add_column('pitch_slope_match', str)
    col_dict['Pitch Slope Match'] = 'pitch_slope_match'

def populate_db(db, col_datatypes, filename):
    file_in = open(filename, 'rb')
    reader = csv.reader(file_in, delimiter=',')
    rows = list(reader)
    file_in.close()
    num_headers = len(rows[0]) + 1 #extra is for filename

    i = 1 #skip headers
    while i < len(rows) and not rows[i][0].startswith('File Stats'):
        if rows[i][1] != 'END PART ONE':
            for j in range(len(rows[i])):
                if col_datatypes[j + 2] == bool:
                    rows[i][j] = int(rows[i][j].lower() == 'true')

            db.insert(
                CSVDatabase.TABLE_NAME,
                map(lambda j: '%s%d' % (CSVDatabase.COL_PREFIX, j), range(num_headers)),
                [[os.path.basename(filename)] + rows[i]],
                )
        i += 1

    return ['Filename'] + rows[0] #headers

def update_freq_val(db, freq_val, freq_col, id):
    if freq_val != '--undefined--':
        db.update(
            CSVDatabase.TABLE_NAME,
            [freq_col],
            'id=?',
            [freq_val, id]
            )

def update_pitch_delta(db, max_pitch, min_pitch, col, id):
    if max_pitch != None and min_pitch != None:
        db.update(
            CSVDatabase.TABLE_NAME,
            [col],
            'id=?',
            [float(max_pitch) - float(min_pitch), id]
        )

def update_question_type(db, q_type, col, id):
    db.update(
        CSVDatabase.TABLE_NAME,
        [col],
        'id=?',
        [q_type, id]
    )

def update_pitch_val(db, pitch_val, id, col_name):
    if pitch_val != None:
        db.update(
            CSVDatabase.TABLE_NAME,
            [col_name],
            'id=?',
            [float(pitch_val), id],
            )

def update_pitch_cat_name(db, pt1_pitch, pt2_pitch, id, col):
    slope_name = None
    if pt1_pitch != None and pt2_pitch != None:
        delta = float(pt2_pitch) - float(pt1_pitch)
        
        slope_name = 'Neutral'
        if delta <= -1.0 * pitch_delta_threshold:
            slope_name = 'Falling'
        elif delta >= pitch_delta_threshold:
            slope_name = 'Rising'

        db.update(
            CSVDatabase.TABLE_NAME,
            [col,
             ],
            'id=?',
            [slope_name,
             id
             ],
            )
            
    return slope_name

def update_pitch_slope_match(db, m_id, m_slope_name, b_slope_name):
    if m_slope_name != None and b_slope_name != None:
        db.update(
            CSVDatabase.TABLE_NAME,
            ['pitch_slope_match'],
            'id=?',
            [str(m_slope_name == b_slope_name), m_id]
            )

def get_not_null_count(db, col):
    rows = db.select(
        CSVDatabase.TABLE_NAME,
        ['count(%s)' % (col)],
        where_cond='%s is not null' % (col)
    )

    return rows[0][0]

def populate_calced_cols(db, col_dict, cur_wav_dir):
    #d1 is mother, d2 is baby
    rows = db.select(
        "%s d1 left join %s d2 on d1.%s = d2.%s AND d1.id = d2.id - 1 AND d1.%s = 'M' AND d2.%s = 'B' AND d1.%s <= ?" % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME, col_dict['Filename'], col_dict['Filename'], col_dict['Speaker'], col_dict['Speaker'], col_dict['Lag Time']),
        ['d1.id',
         'd1.%s' % (col_dict['Marked']),
         'd1.%s' % (col_dict['Sentence Type']),
         'd1.%s' % (col_dict['Start Time']),
         'd1.%s' % (col_dict['Stop Time']),
         'd2.id',
         'd2.%s' % (col_dict['Start Time']),
         'd2.%s' % (col_dict['Stop Time']),
         'd2.%s' % (col_dict['Speaker']),
         'd2.%s' % (col_dict['Lag Time']),
         'd2.%s' % (col_dict['Duration']),
         'd1.%s' % (col_dict['Filename'])
         ],
        where_cond="d1.%s = 'M'" % (col_dict['Speaker']),
        params=[lag_cutoff]
        )

    PraatInterop.open_praat()
    prev_wav_filename = None
    for cur_row in rows:
        m_id, marked, m_sentence_type, m_start, m_end, b_id, b_start, b_end, b_speaker, b_lag_time, b_dur, filename = cur_row
        wav_filename = cur_wav_dir + '\\' + os.path.basename(filename)[:-5] + '.wav'

        if wav_filename != prev_wav_filename:
            PraatInterop.send_commands([
                    'Open long sound file... %s' % (wav_filename)
                    ])
            prev_wav_filename = wav_filename

        m_pt1_time, m_pt1_pitch, m_pt2_time, m_pt2_pitch, m_min_pitch, m_max_pitch, m_mean_pitch = get_praat_vals(m_start, m_end, wav_filename)
        update_pitch_val(db, m_pt1_pitch, m_id, 'm_pt1_pitch')
        update_pitch_val(db, m_pt2_pitch, m_id, 'm_pt2_pitch')
        update_pitch_delta(db, m_pt2_pitch, m_pt1_pitch, 'm_pitch_delta', m_id)
        m_slope_name = update_pitch_cat_name(db, m_pt1_pitch, m_pt2_pitch, m_id, 'm_pitch_cat')
        update_freq_val(db, m_min_pitch, 'm_min_pitch', m_id)
        update_freq_val(db, m_max_pitch, 'm_max_pitch', m_id)
        update_freq_val(db, m_mean_pitch, 'm_mean_pitch', m_id)

        if m_sentence_type == 'Q':
            q_type = 'Y/N' if bool(marked) else 'WH Question'
            update_question_type(db, q_type, col_dict['Question Type'], m_id)

        b_slope_name = None
        if b_speaker:
            b_pt1_time, b_pt1_pitch, b_pt2_time, b_pt2_pitch, b_min_pitch, b_max_pitch, b_mean_pitch = get_praat_vals(b_start, b_end, wav_filename)
            update_pitch_val(db, b_pt1_pitch, m_id, 'b_pt1_pitch')
            update_pitch_val(db, b_pt2_pitch, m_id, 'b_pt2_pitch')
            update_pitch_delta(db, b_pt2_pitch, b_pt1_pitch, 'b_pitch_delta', m_id)
            b_slope_name = update_pitch_cat_name(db, b_pt1_pitch, b_pt2_pitch, m_id, 'b_pitch_cat')
            update_freq_val(db, b_min_pitch, 'b_min_pitch', m_id)
            update_freq_val(db, b_max_pitch, 'b_max_pitch', m_id)
            update_freq_val(db, b_mean_pitch, 'b_mean_pitch', m_id)

            update_pitch_val(db, b_start, m_id, 'b_start_time')
            update_pitch_val(db, b_end, m_id, 'b_end_time')
            update_pitch_val(db, b_lag_time, m_id, 'b_lag_time')
            update_pitch_val(db, b_dur, m_id, 'b_duration')

        update_pitch_slope_match(db, m_id, m_slope_name, b_slope_name)

    PraatInterop.close_praat()

def export(db, col_dict, filename):
    headers = [
        'Filename',
        'Condition',
        'Speaker',
        'Sentence Type',
        'Question Type',
        'Start Time',
        'Stop Time',
        'Duration',
        'Lag Time',
        'Mother Max Pitch',
        'Mother Min Pitch',
        'Mother Mean Pitch',
        'Mother Point 1 Pitch',
        'Mother Point 2 Pitch',
        'Mother Pitch Delta',
        'Mother Pitch Category',
        'Baby Start Time',
        'Baby End Time',
        'Baby Duration',
        'Baby Lag Time',
        'Baby Max Pitch',
        'Baby Min Pitch',
        'Baby Mean Pitch',
        'Baby Point 1 Pitch',
        'Baby Point 2 Pitch',
        'Baby Pitch Delta',
        'Baby Pitch Category',
        'Pitch Slope Match']

    #filename = filename[:-4] + '-out.csv'
    
    cols = []
    for cur_header in headers:
        cols.append(col_dict[cur_header])

    rows = db.select(
        CSVDatabase.TABLE_NAME,
        cols,
        where_cond="%s = 'M'" % (col_dict['Speaker']),
        order_by='%s' % (col_dict['Start Time'])
        )

    file_out = open(filename, 'wb')
    writer = csv.writer(file_out, delimiter=',', quoting=csv.QUOTE_ALL)

    writer.writerow(headers)
    for cur_row in rows:
        writer.writerow(cur_row)

    file_out.close()

def check_log_file(path):
    if not os.path.exists(path):
        logfile = open(path, 'w')
        logfile.close()
        
def run():
    LOGFILE = 'logs/pitch2_script.log'

    #create log file if it doesn't exist
    check_log_file(LOGFILE)
    #set up logging
    logging.basicConfig(level=logging.ERROR,
                        filename=LOGFILE,
                        format='%(asctime)s %(message)s') #prefix each message with a timestamp

    for i in range(len(input_dir)):
        input_filenames = glob.glob('%s\\*.csv' % (input_dir[i]))

        file_index = 0
        for cur_filename in input_filenames:
            print 'File %d of %d' % (file_index + 1, len(input_filenames))

            db, col_datatypes = create_db()

            headers = populate_db(db, col_datatypes, cur_filename)

            #build mapping of spreadsheet column names the database column names
            col_dict = OrderedDict()
            j = 0
            while j < len(headers):
                col_dict[headers[j]] = '%s%d' % (CSVDatabase.COL_PREFIX, j)
                j += 1

            append_calced_cols(db, col_dict)

            populate_calced_cols(db, col_dict, wav_dir[i])

            export(db, col_dict, out_dir[i] + '\\' + os.path.basename(cur_filename))

            file_index += 1
