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

lag_cutoff = 2.0
input_dir = ('C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\test_in\\10 mo',
             'C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\test_in\\14 mo',
             )
wav_dir = ('C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\wav\\10 mo',
           'C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\wav\\14 mo',
           )
out_dir = ('C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\test_out\\10 mo',
           'C:\\Users\\Wayne\\Documents\\baby-lab\\bll\\mel\\test_out\\14 mo',
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
    PraatInterop.send_commands( PraatInterop.get_pitch_extrema(wav_filename, start, end) )
    min_pitch, max_pitch, mean_pitch = PraatInterop.socket_receive(socket)

    wav_object_name = (os.path.basename(wav_filename)[:-4])
    PraatInterop.send_commands([
            #'Remove', #pitch
            'select Sound %s' % (wav_object_name),
            'Remove',
            'select LongSound %s' % (wav_object_name),
            ]) 

    return (float_or_none(min_pitch),
            float_or_none(max_pitch),
            float_or_none(mean_pitch),
            )

def append_calced_cols(db, col_dict):
    db.add_column('m_max_pitch', float)
    col_dict['Mother Max Pitch'] = 'm_max_pitch'

    db.add_column('m_min_pitch', float)
    col_dict['Mother Min Pitch'] = 'm_min_pitch'

    db.add_column('m_mean_pitch', float)
    col_dict['Mother Mean Pitch'] = 'm_mean_pitch'

    db.add_column('m_pitch_delta', float)
    col_dict['Mother Pitch Delta'] = 'm_pitch_delta'

    db.add_column('b_max_pitch', float)
    col_dict['Baby Max Pitch'] = 'b_max_pitch'

    db.add_column('b_min_pitch', float)
    col_dict['Baby Min Pitch'] = 'b_min_pitch'

    db.add_column('b_mean_pitch', float)
    col_dict['Baby Mean Pitch'] = 'b_mean_pitch'

    db.add_column('b_pitch_delta', float)
    col_dict['Baby Pitch Delta'] = 'b_pitch_delta'

    db.add_column('question_type', str)
    col_dict['Question Type'] = 'question_type'

    db.add_column('m_pitch_cat', float)
    col_dict['Mother Pitch Category'] = 'm_pitch_cat'

    db.add_column('b_pitch_cat', float)
    col_dict['Baby Pitch Category'] = 'b_pitch_cat'

    # db.add_column('responding_speaker', str)
    # col_dict['Responding Speaker'] = 'responding_speaker'

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

# def update_responding_speaker(db, speaker, col_name, id):
#     db.update(
#         CSVDatabase.TABLE_NAME,
#         [col_name],
#         'id=?',
#         [speaker, id]
#         )

def get_not_null_count(db, col):
    rows = db.select(
        CSVDatabase.TABLE_NAME,
        ['count(%s)' % (col)],
        where_cond='%s is not null' % (col)
    )

    return rows[0][0]

def get_median_pitch(db, pitch_col):
    count = get_not_null_count(db, pitch_col)

    median = None
    
    if count == 0:
        median = None
        
    elif count % 2 > 0:
        rows = db.select(
            CSVDatabase.TABLE_NAME,
            [pitch_col],
            where_cond='%s is not null' % (pitch_col),
            order_by='%s ASC' % (pitch_col),
            offset=count / 2,
            limit=1
        )
        median = rows[0][0]
        
    else:
        rows = db.select(
            CSVDatabase.TABLE_NAME,
            [pitch_col],
            where_cond='%s is not null' % (pitch_col),
            order_by='%s ASC' % (pitch_col),
            offset=count / 2 - 1,
            limit=2
        )
        median = (rows[0][0] + rows[1][0]) / 2.0 #average the two middle values
        
    return median

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
         'd1.%s' % (col_dict['Filename'])
         ],
        where_cond="d1.%s = 'M'" % (col_dict['Speaker']),
        params=[lag_cutoff]
        )

    PraatInterop.open_praat()
    prev_wav_filename = None
    for cur_row in rows:
        m_id, marked, m_sentence_type, m_start, m_end, b_id, b_start, b_end, b_speaker, filename = cur_row
        wav_filename = cur_wav_dir + '\\' + os.path.basename(filename)[:-5] + '.wav'

        if wav_filename != prev_wav_filename:
            PraatInterop.send_commands([
                    'Open long sound file... %s' % (wav_filename)
                    ])
            prev_wav_filename = wav_filename
        
        m_min_pitch, m_max_pitch, m_mean_pitch = get_praat_vals(m_start, m_end, wav_filename)
        update_freq_val(db, m_min_pitch, 'm_min_pitch', m_id)
        update_freq_val(db, m_max_pitch, 'm_max_pitch', m_id)
        update_freq_val(db, m_mean_pitch, 'm_mean_pitch', m_id)
        update_pitch_delta(db, m_max_pitch, m_min_pitch, 'm_pitch_delta', m_id)

        if m_sentence_type == 'Q':
            q_type = 'Y/N' if bool(marked) else 'WH Question'
            update_question_type(db, q_type, col_dict['Question Type'], m_id)

        if b_speaker:
            b_min_pitch, b_max_pitch, b_mean_pitch = get_praat_vals(b_start, b_end, wav_filename)
            update_freq_val(db, b_min_pitch, 'b_min_pitch', m_id)
            update_freq_val(db, b_max_pitch, 'b_max_pitch', m_id)
            update_freq_val(db, b_mean_pitch, 'b_mean_pitch', m_id)
            update_pitch_delta(db, b_max_pitch, b_min_pitch, 'b_pitch_delta', m_id)

        #freq
        #update_responding_speaker(db, r_speaker, col_dict['Responding Speaker'], r_id)
        
    PraatInterop.close_praat()

def populate_pitch_cat_cols(db, col_dict):
    m_median = get_median_pitch(db, col_dict['Mother Pitch Delta'])
    b_median = get_median_pitch(db, col_dict['Baby Pitch Delta'])

    if m_median != None:
        db.update(
            CSVDatabase.TABLE_NAME,
            [col_dict['Mother Pitch Category']],
            where_cond="%s='M' and %s >= ?" % (col_dict['Speaker'], col_dict['Mother Pitch Delta']),
            params=['High', m_median]
        )
        db.update(
            CSVDatabase.TABLE_NAME,
            [col_dict['Mother Pitch Category']],
            where_cond="%s='M' and %s < ?" % (col_dict['Speaker'], col_dict['Mother Pitch Delta']),
            params=['Low', m_median]
        )

    if b_median != None:
        db.update(
            CSVDatabase.TABLE_NAME,
            [col_dict['Baby Pitch Category']],
            where_cond="%s='M' and %s >= ?" % (col_dict['Speaker'], col_dict['Baby Pitch Delta']),
            params=['High', b_median]
        )
        db.update(
            CSVDatabase.TABLE_NAME,
            [col_dict['Baby Pitch Category']],
            where_cond="%s='M' and %s < ?" % (col_dict['Speaker'], col_dict['Baby Pitch Delta']),
            params=['Low', b_median]
        )

def export(db, col_dict, filename):
    headers = ['Filename', 'Condition', 'Speaker', 'Sentence Type', 'Question Type', 'Start Time', 'Stop Time', 'Duration', 'Lag Time', 'Mother Max Pitch', 'Mother Min Pitch', 'Mother Mean Pitch', 'Mother Pitch Delta', 'Mother Pitch Category', 'Baby Max Pitch', 'Baby Min Pitch', 'Baby Mean Pitch', 'Baby Pitch Delta', 'Baby Pitch Category']

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

            populate_pitch_cat_cols(db, col_dict)

            export(db, col_dict, out_dir[i] + '\\' + os.path.basename(cur_filename))

            file_index += 1
