import glob
import csv
import os
import numpy
from db.csv_database import CSVDatabase
from utils.backend_utils import BackendUtils

task = 3

envs = (
    'home',
    'home daycare',
    'daycare centre',
)

stats_input_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/results/Task%d/stats/' % (task)

adex_input_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/results/ADEX/'

results_output_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/results/Task%d/comparison/' % (task)

def build_stats_db(cur_file):
    file_in = open(cur_file, 'rb')
    reader = csv.reader(file_in)
    rows = list(reader)
    file_in.close()
    header_index = 18 + int(task == 3)
    header_row = rows[header_index]
    rows = rows[header_index + 1:-4]

    col_datatypes = (str, str, str, int,)
    db = CSVDatabase(header_row, col_datatypes)
    
    for cur_row in rows:
        start_time, end_time, phrase, count = cur_row
        start_time = '%0.2f' % (BackendUtils.time_str_to_float(start_time))
        end_time = '%0.2f' % (BackendUtils.time_str_to_float(end_time))
        db.csv_insert([start_time, end_time, phrase, count])
        
    db.cursor.execute('create index time_index on data (col0, col1);')
    
    db.cursor.execute(
        'select * from (select min(id), max(id), count(col0) as dup_count, sum(col3) from data group by col0, col1) where dup_count > 1;'
    )
    
    dup_rows = db.cursor.fetchall()

    if dup_rows:
        print 'Found %d multi-speaker situations.' % (len(dup_rows))

    # print 'min(id), max(id), dup_count, total'
    # for cur_row in dup_rows:
    #     print cur_row

    for cur_dup in dup_rows:
        if task == 2:
            combine_multi_speaker_occur(db, cur_dup)
        elif task == 3:
            delete_multi_speaker_occur(db, cur_dup)

    #db.dump_to_file('C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/results/Task%d/test.db' % (task))
    return db

def delete_multi_speaker_occur(db, cur_dup):
    min_id, max_id, dup_count, new_sum = cur_dup
    db.cursor.execute('delete from data where id >= ? and id <= ?;',
                      (min_id, max_id)
    )
    
def combine_multi_spkr_occur(db, cur_dup):
    min_id, max_id, dup_count, new_sum = cur_dup

    db.cursor.execute('select col2 from data where id >= ? and id <= ?;',
                      (min_id, max_id)
    )
    phrase_rows = db.cursor.fetchall()

    new_phrase = ''
    i = 0
    while i < len(phrase_rows):
        new_phrase += phrase_rows[i][0]
        if i < len(phrase_rows) - 1:
            new_phrase += ' '
        i += 1

    db.cursor.execute(
        'update data set col2 = ?, col3 = ? where id = ?;',
        (new_phrase, new_sum, min_id)
    )

    db.cursor.execute(
        'delete from data where id > ? and id <= ?;',
        (min_id, max_id)
    )

def build_adex_db(cur_file):
    file_in = open(cur_file, 'rb')
    reader = csv.DictReader(file_in)
    rows = list(reader)
    file_in.close()

    #AWC, start time, end time
    col_datatypes = (float, str, str)
    db = CSVDatabase(['AWC', 'Start Time', 'End Time'], col_datatypes)
    db.cursor.execute('create index time_index on data (col1, col2);')
    
    accum_time = float(rows[0]['Elapsed_Time'])
    i = 0
    while i < len(rows):
        seg_dur = float(rows[i]['Segment_Duration'])
        start_time = '%0.2f' % (accum_time)
        end_time = '%0.2f' % (accum_time + seg_dur)
        awc = float(rows[i]['AWC'])
        
        db.csv_insert([awc, start_time, end_time])

        accum_time += seg_dur
        i += 1

    return db

def match(stats_db, adex_db):
    stats_db.add_column('AWC', float)
    
    stats_rows = stats_db.select(stats_db.TABLE_NAME, ['id', 'col0', 'col1'])
    for cur_stats_row in stats_rows:
        stats_id, stats_start, stats_end = cur_stats_row
        
        adex_rows = adex_db.select(adex_db.TABLE_NAME, ['col0'], where_cond='col1 = ? and col2 = ?', params=[stats_start, stats_end])
        
        if not adex_rows:
            stats_db.delete(
                stats_db.TABLE_NAME,
                where_cond='id = ?',
                params=[stats_id]
            )
            print 'No match found for this time (row deleted):'
            print stats_start, stats_end

        else:
            awc = adex_rows[0][0]
            stats_db.update(stats_db.TABLE_NAME, ['col4'], where_cond='id = ?', params=[awc, stats_id])

def write_results(stats_db, env, stats_filename, counts, awc):
    output_dir = '%s%s/' % (results_output_path, env)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    filename = '%s-cmp.csv' % (stats_filename.split('-stats')[0])
    output_file = '%s%s' % (output_dir, filename)
    stats_db.write_to_file(output_file)

    file_in = open(output_file, 'rb')
    reader = csv.reader(file_in)
    rows = list(reader)
    file_in.close()
    
    header_row, data_row = get_stats_rows(counts, awc)
    rows.insert(0, [''])
    rows.insert(0, data_row)
    rows.insert(0, header_row)
    
    file_out = open(output_file, 'wb')
    writer = csv.writer(file_out)
    for cur_row in rows:
        writer.writerow(cur_row)
    file_out.close()

def get_counts(stats_db):
    rows = stats_db.select(stats_db.TABLE_NAME, ['col3', 'col4'])
    stats_counts = []
    adex_awc = []
    for cur_row in rows:
        stats_counts.append(cur_row[0])
        adex_awc.append(cur_row[1])

    return stats_counts, adex_awc

def get_stats_rows(stats_counts, adex_awc):
    header = []
    row = []
    data_dict = {'Count': stats_counts, 'AWC': adex_awc}
    for col in data_dict:
        for fcn in [numpy.sum, numpy.mean, numpy.var, numpy.std]:
            header.append('%s(%s)' % (fcn.func_name, col))
            row.append(fcn(data_dict[col]))

    return header, row

def write_env_results(stats_counts, adex_awc, env):
    output_filename = '%s%s/summary.csv' % (results_output_path, env)
    file_out = open(output_filename, 'wb')
    writer = csv.writer(file_out)

    header, row = get_stats_rows(stats_counts, adex_awc)
    
    writer.writerow(header)
    writer.writerow(row)
    file_out.close()
    
def run():
    for cur_env in envs:
        print '\nEntering directory %s/' % (cur_env)
        filenames = glob.glob('%s%s/*.csv' % (stats_input_path, cur_env))

        stats_counts = []
        adex_awc = []

        for cur_file in filenames:
            print '\nProcessing file %s' % (os.path.basename(cur_file))
            
            stats_db = build_stats_db(cur_file)
            adex_db = build_adex_db('%s%s/%s' % (
                adex_input_path,
                cur_env,
                '%s.csv' % (os.path.basename(cur_file).split('_FINAL')[0])
            ))

            match(stats_db, adex_db)

            cur_counts, cur_awc = get_counts(stats_db)
            write_results(stats_db, cur_env, os.path.basename(cur_file), cur_counts, cur_awc)

            stats_counts.extend(cur_counts)
            adex_awc.extend(cur_awc)

        write_env_results(stats_counts, adex_awc, cur_env)
