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
input_dir = 'C:\\Users\\Wayne\\Desktop\\bll\\test_in\\10 mo'
wav_dir = 'C:\\Users\\Wayne\\Desktop\\bll\\wav\\10 mo'
out_dir = 'C:\\Users\\Wayne\\Desktop\\bll\\test_out\\10 mo'

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

    PraatInterop.send_commands( PraatInterop.get_octave_corrected_pitch_script() )

    PraatInterop.send_commands( PraatInterop.get_pitch_sample_vals_script(start, end, wav_filename) )
    pt1_time, pt1_pitch, pt2_time, pt2_pitch = PraatInterop.socket_receive(socket)

    PraatInterop.send_commands( PraatInterop.get_pitch_extrema() )
    min_pitch, max_pitch, mean_pitch = PraatInterop.socket_receive(socket)

    wav_object_name = (os.path.basename(wav_filename)[:-4])
    PraatInterop.send_commands([
            'Remove', #pitch
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
    db.add_column('question_type', str)
    col_dict['Question Type'] = 'question_type'
   
    db.add_column('pitch_slope', str)
    col_dict['Pitch Slope'] = 'pitch_slope'

    db.add_column('pt1_pitch', float)
    col_dict['Point 1 Pitch'] = 'pt1_pitch'

    db.add_column('pt2_pitch', float)
    col_dict['Point 2 Pitch'] = 'pt2_pitch'

    db.add_column('pitch_delta', float)
    col_dict['Pitch Delta'] = 'pitch_delta'

    db.add_column('pitch_slope_match', str)
    col_dict['Pitch Slope Match'] = 'pitch_slope_match'
    
    db.add_column('max_pitch', float)
    col_dict['Max Pitch'] = 'max_pitch'

    db.add_column('min_pitch', float)
    col_dict['Min Pitch'] = 'min_pitch'

    db.add_column('mean_pitch', float)
    col_dict['Mean Pitch'] = 'mean_pitch'

def populate_db(db, col_datatypes, filename):
    file_in = open(filename, 'rb')
    reader = csv.reader(file_in, delimiter=',')
    rows = list(reader)
    file_in.close()
    num_headers = len(rows[0]) + 1 #extra is for filename

    i = 1 #skip headers
    while i < len(rows) and not rows[i][0].startswith('File Stats'):
        for j in range(len(rows[i])):
            if col_datatypes[j + 2] == bool:
                rows[i][j] = int(rows[i][j] == 'True')
        
        db.insert(
            CSVDatabase.TABLE_NAME,
            map(lambda j: '%s%d' % (CSVDatabase.COL_PREFIX, j), range(num_headers)),
            [[os.path.basename(filename)] + rows[i]],
            )
        i += 1

    return ['Filename'] + rows[0] #headers

def update_question_type(db, col_dict):
    db.update(
        CSVDatabase.TABLE_NAME,
        ['question_type'],
        where_cond="%s='M' AND %s='Q' AND %s=1 AND %s <= ?" % (
            col_dict['Speaker'],
            col_dict['Sentence Type'],
            col_dict['Marked'],
            col_dict['Lag Time'],
            ),
        params=['Y/N', lag_cutoff],
        )

    db.update(
        CSVDatabase.TABLE_NAME,
        ['question_type'],
        where_cond="%s='M' AND %s='Q' AND %s=0 AND %s <= ?" % (
            col_dict['Speaker'],
            col_dict['Sentence Type'],
            col_dict['Marked'],
            col_dict['Lag Time'],
            ),
        params=['WH Question', lag_cutoff],
        )

def update_pitch_val(db, pitch_val, id, col_name):
    if pitch_val != None:
        db.update(
            CSVDatabase.TABLE_NAME,
            [col_name],
            'id=?',
            [float(pitch_val), id],
            )

def update_pitch_delta_name(db, pt1_pitch, pt2_pitch, id):
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
            ['pitch_delta',
             'pitch_slope',
             ],
            'id=?',
            [delta,
             slope_name,
             id
             ],
            )
            
    return slope_name

def update_pitch_slope_match(db, m_id, b_id, m_slope_name, b_slope_name):
    if m_slope_name != None and b_slope_name != None:
        db.update(
            CSVDatabase.TABLE_NAME,
            ['pitch_slope_match'],
            'id=? OR id=?',
            [str(m_slope_name == b_slope_name), m_id, b_id]
            )

# def get_next_range(table, i):
#     start = None
#     end = None
    
#     while i < len(table) and table[i] == None:
#         i += 1

#     if i < len(table):
#         start = i
#         end = start
#         i += 1

#         while i < len(table) and table[i] != None:
#             end = i
#             i += 1

#     return start, end, i

# def process_pitch_listing_longest_stretch(lines):
#     table = []
#     for i in range(1, len(lines) - 1): #first row is headers, last row is empty
#         cells = re.split(r'\s+', lines[i])
#         pitch = None if cells[1] == '--undefined--' else float(cells[1])
#         table.append(pitch)

#     best_begin = None
#     best_end = None
#     i = 0
#     while i < len(table):
#         begin, end, i = get_next_range(table, i)
#         if begin != None and end != None:
#             #since samples in the pitch listing are at regular (10ms) intervals, we can determine the longest sequence by subtracting begin and end indices
#             if best_begin == None or ((end - begin) > (best_end - best_begin)):
#                 best_begin, best_end = begin, end

#         i += 1

#     begin_pitch = table[best_begin] if best_begin != None else None
#     end_pitch = table[best_end] if best_end != None else None
    
#     return begin_pitch, end_pitch

# def process_pitch_listing_first_last(lines):
#     start = None
#     end = None
    
#     for i in range(1, len(lines) - 1):
#         cells = re.split(r'\s+', lines[i])
#         if cells[1] != '--undefined--':
#             time, pitch = float(cells[0]), float(cells[1])
#             if start == None:
#                 start = time
#             else:
#                 end = time

#     return start, end

def update_freq_val(db, freq_val, freq_col, id):
    if freq_val != '--undefined--':
        db.update(
            CSVDatabase.TABLE_NAME,
            [freq_col],
            'id=?',
            [freq_val, id]
            )

def populate_calced_cols(db, col_dict):
    rows = db.select(
        '%s d1, %s d2' % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME),
        ['d1.id',
         'd1.%s' % (col_dict['Start Time']),
         'd1.%s' % (col_dict['Stop Time']),
         'd2.id',
         'd2.%s' % (col_dict['Start Time']),
         'd2.%s' % (col_dict['Stop Time']),
         'd1.%s' % (col_dict['Filename'])
         ],
        "d1.%s = d2.%s AND d1.id = d2.id - 1 AND d1.%s = 'M' AND d2.%s = 'B' AND d1.%s <= ?" % (col_dict['Filename'], col_dict['Filename'], col_dict['Speaker'], col_dict['Speaker'], col_dict['Lag Time']),
        [lag_cutoff]
        )
    
    update_question_type(db, col_dict)

    PraatInterop.open_praat()
    prev_wav_filename = None
    for cur_row in rows:
        m_id, m_start, m_end, b_id, b_start, b_end, filename = cur_row
        wav_filename = wav_dir + '\\' + os.path.basename(filename)[:-5] + '.wav'

        if wav_filename != prev_wav_filename:
            PraatInterop.send_commands([
                    'Open long sound file... %s' % (wav_filename)
                    ])
            prev_wav_filename = wav_filename
        
        m_pt1_time, m_pt1_pitch, m_pt2_time, m_pt2_pitch, m_min_pitch, m_max_pitch, m_mean_pitch = get_praat_vals(m_start, m_end, wav_filename)

        b_pt1_time, b_pt1_pitch, b_pt2_time, b_pt2_pitch, b_min_pitch, b_max_pitch, b_mean_pitch = get_praat_vals(b_start, b_end, wav_filename)

        #pitch
        update_pitch_val(db, m_pt1_pitch, m_id, 'pt1_pitch')
        update_pitch_val(db, m_pt2_pitch, m_id, 'pt2_pitch')

        update_pitch_val(db, b_pt1_pitch, b_id, 'pt1_pitch')
        update_pitch_val(db, b_pt2_pitch, b_id, 'pt2_pitch')

        m_slope_name = update_pitch_delta_name(db, m_pt1_pitch, m_pt2_pitch, m_id)
        b_slope_name = update_pitch_delta_name(db, b_pt1_pitch, b_pt2_pitch, b_id)
        
        update_pitch_slope_match(db, m_id, b_id, m_slope_name, b_slope_name)

        #freq
        update_freq_val(db, m_min_pitch, 'min_pitch', m_id)
        update_freq_val(db, m_max_pitch, 'max_pitch', m_id)
        update_freq_val(db, m_mean_pitch, 'mean_pitch', m_id)

        update_freq_val(db, b_min_pitch, 'min_pitch', b_id)
        update_freq_val(db, b_max_pitch, 'max_pitch', b_id)
        update_freq_val(db, b_mean_pitch, 'mean_pitch', b_id)
        
    PraatInterop.close_praat()

def get_count(db, col_dict, m_sentence_type, m_pitch_slope, b_pitch_slope=None):
    where_cond = "d1.%s = d2.%s AND d1.id = d2.id - 1 AND d1.%s = 'M' AND d2.%s = 'B' AND d1.%s <= ? AND d1.%s = ? AND d1.pitch_slope = ?" % (col_dict['Filename'], col_dict['Filename'], col_dict['Speaker'], col_dict['Speaker'], col_dict['Lag Time'], col_dict['Sentence Type'])
    params = [lag_cutoff, m_sentence_type, m_pitch_slope]

    if b_pitch_slope != None:
        where_cond += " AND d2.pitch_slope = ?"
        params.append(b_pitch_slope)
    
    rows = db.select(
        '%s d1, %s d2' % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME),
        ['count(d1.id)',
         ],
        where_cond,
        params,
        )

    count = str(None)
    if len(rows) and len(rows[0]) and rows[0][0] != None:
        count = str(rows[0][0])
        
    result = 'M%s %s -> B' % (m_sentence_type, m_pitch_slope)
    if b_pitch_slope != None:
        result += ' %s' % (b_pitch_slope)
    result += ': %s' % (count)

    return [result]

def get_stats_rows(db, col_dict):
    stats_rows = [[], ['Counts:']]

    stats_rows.append( get_count(db, col_dict, 'Q', 'Rising') )
    stats_rows.append( get_count(db, col_dict, 'Q', 'Rising', 'Rising') )
    stats_rows.append( get_count(db, col_dict, 'Q', 'Rising', 'Falling') )
    stats_rows.append( get_count(db, col_dict, 'Q', 'Rising', 'Neutral') )

    stats_rows.append( get_count(db, col_dict, 'Q', 'Falling') )
    stats_rows.append( get_count(db, col_dict, 'Q', 'Falling', 'Rising') )
    stats_rows.append( get_count(db, col_dict, 'Q', 'Falling', 'Falling') )
    stats_rows.append( get_count(db, col_dict, 'Q', 'Falling', 'Neutral') )

    stats_rows.append( get_count(db, col_dict, 'D', 'Rising') )
    stats_rows.append( get_count(db, col_dict, 'D', 'Rising', 'Rising') )
    stats_rows.append( get_count(db, col_dict, 'D', 'Rising', 'Falling') )
    stats_rows.append( get_count(db, col_dict, 'D', 'Rising', 'Neutral') )

    stats_rows.append( get_count(db, col_dict, 'D', 'Falling') )
    stats_rows.append( get_count(db, col_dict, 'D', 'Falling', 'Rising') )
    stats_rows.append( get_count(db, col_dict, 'D', 'Falling', 'Falling') )
    stats_rows.append( get_count(db, col_dict, 'D', 'Falling', 'Neutral') )

    return stats_rows

def export(db, col_dict, filename):
    stats_rows = get_stats_rows(db, col_dict)

    baby_headers = ['Start Time', 'Stop Time', 'Duration', 'Lag Time', 'Pitch Slope', 'Point 1 Pitch', 'Point 2 Pitch', 'Pitch Delta', 'Pitch Slope Match', 'Max Pitch', 'Min Pitch', 'Mean Pitch']
    mother_headers = ['Sentence Type', 'Question Type', 'Start Time', 'Stop Time', 'Duration', 'Lag Time', 'Pitch Slope', 'Point 1 Pitch', 'Point 2 Pitch', 'Pitch Delta', 'Pitch Slope Match', 'Max Pitch', 'Min Pitch', 'Mean Pitch']

    cols = ['d1.%s' % (col_dict['Filename'])]
    headers = ['Filename']
    
    for cur_header in mother_headers:
        headers.append('Mother %s' % (cur_header))
        cols.append('d1.%s' % (col_dict[cur_header]))

    for cur_header in baby_headers:
        headers.append('Baby %s' % (cur_header))
        cols.append('d2.%s' % (col_dict[cur_header]))

    rows = db.select(
        '%s d1, %s d2' % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME),
        cols,
        "d1.%s = d2.%s AND d1.id = d2.id - 1 AND d1.%s = 'M' AND d2.%s = 'B' AND d1.%s <= ?" % (col_dict['Filename'], col_dict['Filename'], col_dict['Speaker'], col_dict['Speaker'], col_dict['Lag Time']),
        [lag_cutoff],
        )

    file_out = open(filename, 'wb')
    writer = csv.writer(file_out, delimiter=',', quoting=csv.QUOTE_ALL)

    headers.insert(len(mother_headers) + 1, '')
    writer.writerow(headers)
    for cur_row in rows:
        cur_row = list(cur_row)
        cur_row.insert(len(mother_headers) + 1, '')
        writer.writerow(cur_row)

    for cur_row in stats_rows:
        cur_row = list(cur_row)
        cur_row.insert(len(mother_headers) + 1, '')
        writer.writerow(cur_row)
        
    file_out.close()

def check_log_file(path):
    if not os.path.exists(path):
        logfile = open(path, 'w')
        logfile.close()
        
def main():
    LOGFILE = 'logs/pitch_script.log'

    #create log file if it doesn't exist
    check_log_file(LOGFILE)
    #set up logging
    logging.basicConfig(level=logging.ERROR,
                        filename=LOGFILE,
                        format='%(asctime)s %(message)s') #prefix each message with a timestamp

    input_filenames = glob.glob('%s\\*.csv' % (input_dir))

    for cur_filename in input_filenames:
        db, col_datatypes = create_db()

        headers = populate_db(db, col_datatypes, cur_filename)

        #build mapping of spreadsheet column names the database column names
        col_dict = OrderedDict()
        i = 0
        while i < len(headers):
            col_dict[headers[i]] = '%s%d' % (CSVDatabase.COL_PREFIX, i)
            i += 1

        append_calced_cols(db, col_dict)
    
        populate_calced_cols(db, col_dict)
    
        export(db, col_dict, out_dir + '\\' + os.path.basename(cur_filename))

main()
