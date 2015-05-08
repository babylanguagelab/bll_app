from parsers.wav_parser import WavParser
import os
import csv
from db.database import Database
from db.csv_database import CSVDatabase
from utils.praat_interop import PraatInterop
import sys
import random
from collections import OrderedDict

wav_in_dir = 'C:/Users/Wayne/Documents/baby-lab/bll/mel/wav/'
wav_out_dir = 'C:/Users/Wayne/Documents/baby-lab/bll/mel/testing/clips/'
db_path = 'C:/Users/Wayne/Documents/baby-lab/bll/mel/testing/data/clips.db'
sql_path = 'C:/Users/Wayne/Documents/baby-lab/bll_app/custom_scripts/melissa/testing_rename.sql'
data_path = 'C:/Users/Wayne/Documents/baby-lab/bll/mel/testing/data/dataset.csv'

filter_from = 0
filter_to = 400
filter_smoothing = 100
amplitude_factor = 5

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

def partition_files(db, age):
    #get a list of pairs of (filename, total duration)
    pairs = db.select(
        'clips',
        ['Filename, sum(Stop_Time - Start_Time) as dur'],
        where_cond = 'Age = ?',
        group_by = 'Filename',
        order_by = 'dur',
        params = [age]
    )

    batches = []
    i = 0

    #we have an even number of recordings, so this will work out exactly
    num_batches = len(pairs) / 2
    while i < num_batches:
        group = [pairs[0], pairs[-1]]
        batches.append(group)
        pairs = pairs[1:-1]
        i += 1

    return batches
    
def divide_clips(db):
    batches_10mo = partition_files(db, 10)
    batches_14mo = partition_files(db, 14)

    batches_10mo.sort(key=lambda pair: pair[0][1] + pair[1][1])
    batches_14mo.sort(key=lambda pair: pair[0][1] + pair[1][1])

    batches = []
    num_batches = len(batches_10mo) #both lists have same length, since we have same number of 10mo and 14mo recordings
    head = lambda x: x[0]
    for i in range(num_batches):
        group = map(head, batches_10mo[i]) + map(head, batches_14mo[num_batches - i - 1])
        batches.append(group)
        
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
    db = CSVDatabase.create_with_files([data_path], col_datatypes)
    db.execute_script(sql_path)
    db.dump_to_file(db_path)
    db.close()

    return Database(db_path)
    
def run():
    db = create_db()

    batches = divide_clips(db)
    for i in range(len(batches)):
        print 'Creating batch %d of %d' % (i + 1, len(batches))
        
        filter_batch(db, batches[i], i + 1) #batch numbers start at 1
        
        print ''
    
    db.close()
