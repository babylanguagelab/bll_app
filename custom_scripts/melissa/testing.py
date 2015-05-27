from parsers.wav_parser import WavParser
import os
import csv
from db.database import Database
from db.csv_database import CSVDatabase
from utils.praat_interop import PraatInterop
import sys
import random
from collections import OrderedDict

wav_in_dir = 'C:/Experimental Data/Daycare Study/Pitch Study Data/wav/'
wav_out_dir = 'C:/Experimental Data/Daycare Study/Pitch Study Data/testing/clips/'
db_path = 'C:/Experimental Data/Daycare Study/Pitch Study Data/testing/data/clips.db'
sql_path = 'C:/Program Files (x86)/bll_app/custom_scripts/melissa/testing_rename.sql'
data_path = 'C:/Experimental Data/Daycare Study/Pitch Study Data/testing/data/dataset.csv'

filter_from = 0
filter_to = 400
filter_smoothing = 100
short_clip_limit = 0.8 #any clips shorter than this will be filtered out

def get_bounds_list(db, filename):
    rows = db.select(
        'clips',
        ['id', 'Start_Time', 'Stop_Time'],
        where_cond = 'Filename = ?',
        params = [filename]
    )
    return rows

def get_filenames_list(db, age=None):
    where_cond = None
    params = []
    if age is not None:
        where_cond = 'Age = ?'
        params = [age]

    rows = db.select(
        'clips',
        ['distinct Filename', 'Age'],
        where_cond = where_cond,
        params = params
    )
    return rows

def get_file_age(db, filename):
    row = db.select(
        'clips',
        ['Age'],
        group_by = 'Filename',
        where_cond = 'Filename = ?',
        params = [filename]
    )
    return row[0][0]

def del_short_clips(db):
    rowcount = db.delete(
        'clips',
        where_cond='Stop_Time - Start_Time < ?',
        params=[short_clip_limit]
    )

    print 'Removed %d clips' % (rowcount)

def partition_files(db):
    #get a list of pairs of (filename, total duration)
    age_10_rows = db.select(
        'clips',
        ['Filename', 'sum(Stop_Time - Start_Time) as dur'],
        where_cond = 'Age = ?',
        group_by = 'Filename',
        order_by = 'dur',
        params = [10]
    )

    age_14_rows = db.select(
        'clips',
        ['Filename', 'sum(Stop_Time - Start_Time) as dur'],
        where_cond = 'Age = ?',
        group_by = 'Filename',
        order_by = 'dur',
        params = [14]
    )

    batches = []
    i = 0

    #we have the same number of 10 and 14 month-old recordings, so this is safe
    num_batches = len(age_10_rows)
    print 'Batch Num\tFiles\t\t\tTotal Dur'
    while i < num_batches:
        group = [age_10_rows[0][0], age_14_rows[-1][0]] #grab shortest and longest and put them together
        batches.append(group)

        total_dur = age_10_rows[0][1] + age_14_rows[-1][1]
        print '%d\t\t(%s, %s)\t%f sec' % (i + 1, age_10_rows[0][0], age_14_rows[-1][0], total_dur)
        
        age_10_rows = age_10_rows[1:]
        age_14_rows = age_14_rows[:-1]
        i += 1

    return batches
    
#def filter_clips(db, csv_filename, batch_dir):
def filter_batch(db, batch, batch_num):
    batch_dir = 'batch%d/' % (batch_num)
    if not os.path.exists(wav_out_dir + batch_dir):
        os.mkdir(wav_out_dir + batch_dir)

    placeholders = '(%s)' % ( ','.join(['?'] * len(batch)) )
    rows = db.select(
        'clips',
        ['id', 'Filename', 'Start_Time', 'Stop_Time'],
        where_cond = 'Filename in %s' % (placeholders),
        params = batch
    )

    filename_dict = OrderedDict()
    random.shuffle(rows)
    for i in range(len(rows)):
        id, filename, start_time, stop_time = rows[i]
        if not filename in filename_dict:
            filename_dict[filename] = []
        filename_dict[filename].append((id, i + 1, start_time, stop_time)) #order numbers start at 1

    PraatInterop.open_praat()
    
    for i in range(len(filename_dict)):
        csv_filename = filename_dict.keys()[i]
        bounds_list = filename_dict[csv_filename]

        file_code = csv_filename[:-5]
        wav_filename = '%s.wav' % (file_code)
        age = get_file_age(db, csv_filename)
        age_dir = '%d mo/' % (age)

        print '\tFiltering file %s%s' % (age_dir, wav_filename)

        PraatInterop.send_commands([
                'Open long sound file... %s%s%s' % (wav_in_dir, age_dir, wav_filename)
            ])

        for j in range(len(bounds_list)):
            id, order_num, start_time, stop_time = bounds_list[j]
            sys.stdout.write('\r\t\tProcessing clip %d of %d' % (j + 1, len(bounds_list)))
            sys.stdout.flush()

            #print '%s%s%s_%d-%d.wav' % (wav_out_dir, batch_dir, file_code, age, order_num),
            # PraatInterop.send_commands([
            #     'Extract part... %f %f yes' % (start_time, stop_time),
            #     'Filter (pass Hann band)... %d %d %d' % (filter_from, filter_to, filter_smoothing),
            #     'Get maximum...',
            #     'Get minimum...',
            #     'Multiply... %f' % (amplitude_factor),
            #     'Save as WAV file... %s%s%s_%d-%d.wav' % (wav_out_dir, batch_dir, file_code, age, order_num),
            #     'select Sound %s' % (file_code + '_band'),
            #     'Remove',
            #     'select Sound %s' % (file_code),
            #     'Remove',
            #     'select LongSound %s' % (file_code),
            # ])
            
            serversocket = PraatInterop.create_serversocket()
            PraatInterop.send_commands(
                PraatInterop.get_low_pass_filter_script(
                    wav_filename,
                    '%s%s%s_%d-%d.wav' % (wav_out_dir, batch_dir, file_code, age, order_num),
                    file_code,
                    start_time,
                    stop_time,
                    filter_from,
                    filter_to,
                    filter_smoothing
                )
            )

            db.update(
                'clips',
                ['Batch_Num', 'Batch_Order'],
                where_cond='id = ?',
                params=[batch_num, order_num, id]
            )
            
        PraatInterop.send_commands([
            'Remove',
        ])
        print ''

    PraatInterop.close_praat()

def create_db():
    col_datatypes = (
        str,
        int,
        str,
        str,
        str,
        str,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        str,
        float,
        float,
        float,
        float,
        str,
    )

    #remove old db if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = CSVDatabase.create_with_files([data_path], col_datatypes)
    db.execute_script(sql_path)
    db.dump_to_file(db_path)
    db.close()

    return Database(db_path)
    
def run():
    db = create_db()

    print 'Removing clips with duration less than %f' % (short_clip_limit)
    del_short_clips(db)
    print ''

    print 'Partitioning batches...'
    batches = partition_files(db)
    print ''
    
    for i in range(len(batches)):
        print 'Creating batch %d of %d' % (i + 1, len(batches))
        
        filter_batch(db, batches[i], i + 1) #batch numbers start at 1
        
        print ''
    
    db.close()
