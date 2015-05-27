import shutil
import glob
import os
import csv
import sys
from db.csv_database import CSVDatabase

in_path = 'C:/Users/Wayne/Documents/baby-lab/bll/dana/src/Home/'
out_path = 'C:/Users/Wayne/Documents/baby-lab/bll/dana/src/Home/trimmed/'

MIN_SECS = 5 * 60 * 60

input_datatypes = [
    int,
    str,
    int,
    float,
    str,
    int,
    str,
    float,
    float,
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
    str,
    str, #db_datetime
    float, #date_start_time
    float, #date_end_time
    float, #abs_start_time
    float, #abs_end_time 
]

def print_trimmed_files(files):
    print 'Trimmed dates:'
    print 'Date\t\t Filename\t Orig Dur\t Trimmed Dur\t Trimmed start time\t Trimmed end time'
    
    filename_keys = files.keys()
    filename_keys.sort()
    for cur_filename in filename_keys:
        date_keys = files[cur_filename].keys()
        date_keys.sort()
        for cur_date in date_keys:
            orig_dur, trimmed_dur, trimmed_start, trimmed_end = files[cur_filename][cur_date]
            print '%s\t %s \t %s\t %s\t %s\t %s' % (cur_date, cur_filename[:-4], orig_dur, trimmed_dur, trimmed_start, trimmed_end)

def print_omitted_files(files):
    print 'Omitted dates (too short):'
    print 'Date\t\t Filename\t Dur'
    
    filename_keys = files.keys()
    filename_keys.sort()
    for cur_filename in filename_keys:
        date_keys = files[cur_filename].keys()
        date_keys.sort()
        for cur_date in date_keys:
            print '%s\t %s \t %s' % (cur_date, cur_filename[:-4], files[cur_filename][cur_date])

def purge_dir(dir_path):
    filenames = glob.glob('%s*.csv' % (out_path))
    for cur_file in filenames:
        shutil.os.remove(cur_file)

def fix_time(val):
    date, time = val.split()
    month, day, year = map(int, date.split('/'))
    hour, minute, sec = map(
        int,
        time.split(':') + ([0] if time.count(':') == 1 else []) #some files are hh:mm:ss, others are just hh:mm. Assume sec = 0 if no seconds are given.
        )

    #return a string in database-readable format (yyyy-mm-dd hh:mm:ss)
    return '%d-%02d-%02d %02d:%02d:%02d' % (year, month, day, hour, minute, sec)

def select_date_durs(db):
    #get a list of all of the dates we have in the file and their end time (durations)
    return db.csv_select_by_name(
        col_names=['File_Name', 'tz_date', 'date_end_time'],
        fcn_col_names=['date_end_time'],
        fcns=['max'],
        group_by='tz_date'
    )

def select_info(db, db_col_names, date):
    rows = db.select(
        CSVDatabase.TABLE_NAME,
        ['min(%s)' % (db_col_names['tz_time']), 'max(%s)' % (db_col_names['tz_time'])],
        where_cond='%s=?' % (db_col_names['tz_date']),
        params=[date]
    )

    return rows[0]

def select_dur_at_6(db, db_col_names, date):
    rows = db.select(
        CSVDatabase.TABLE_NAME,
        ['min(%s)' % (db_col_names['date_start_time'])],
        where_cond="%s = ? AND %s >= '18:00'" % (db_col_names['tz_date'], db_col_names['tz_time']),
        params=[date]
    )

    result = None
    if rows:
        result = rows[0][0]
        
    return result

def run():
    purge_dir(out_path)
    
    file_list = glob.glob('%s*.csv' % (in_path))
    trimmed_files = {}
    omitted_files = {}
    
    for i in range(len(file_list)):
        sys.stderr.write('\r' * 14)
        sys.stderr.write('File %d of %d' % (i + 1, len(file_list)))

        in_file = open(file_list[i], 'rb')
        reader = csv.reader(in_file)
        csv_rows = list(reader)
        in_file.close()

        clock_index = csv_rows[0].index('Clock_Time_TZAdj')
        el_time_index = csv_rows[0].index('Elapsed_Time')
        seg_dur_index = csv_rows[0].index('Segment_Duration')

        csv_rows[0].append('db_datetime')
        csv_rows[0].append('date_start_time')
        csv_rows[0].append('date_end_time')
        csv_rows[0].append('abs_start_time')
        csv_rows[0].append('abs_end_time')
        date_accum_time = None
        abs_accum_time = float(csv_rows[1][el_time_index])
        prev_date = None
        
        for j in range(1, len(csv_rows)):
            csv_rows[j].append(fix_time(csv_rows[j][clock_index]))

            date = csv_rows[j][clock_index].split()[0]
            if date != prev_date:
                date_accum_time = float(csv_rows[j][el_time_index])

            seg_dur = float(csv_rows[j][seg_dur_index])
            csv_rows[j].append(date_accum_time) #date_start
            csv_rows[j].append(date_accum_time + seg_dur) #date_end
            csv_rows[j].append(abs_accum_time) #abs_start
            csv_rows[j].append(abs_accum_time + seg_dur) #abs_end

            abs_accum_time += seg_dur
            date_accum_time += seg_dur
            prev_date = date

        #create daterbase
        db = CSVDatabase.create_with_rows(csv_rows, input_datatypes)

        #append separate date and time cols for sanity
        db.add_column('tz_date', str)
        db.add_column('tz_time', str)

        #set their values using the Clock_Time_TZAdj column
        #drop down to database layer for this
        db_col_names = db.get_db_col_names()
        clock_col = db_col_names['db_datetime']
        date_col = db_col_names['tz_date']
        time_col = db_col_names['tz_time']
        stmt = 'UPDATE %s SET %s = date(%s), %s = time(%s)' % (CSVDatabase.TABLE_NAME, date_col, clock_col, time_col, clock_col)
        db.execute_stmt(stmt)

        #db.dump_to_file('%d.db' % (i + 1))
        
        #get a list of all of the dates we have in the file and their end time (durations)
        date_durs = select_date_durs(db)

        for row in date_durs:
            filename, date, dur = row
            
            #delete dates with < 5 hours of recorded time
            if float(dur) < MIN_SECS:
                if filename not in omitted_files:
                    omitted_files[filename] = {}
                omitted_files[filename][date] = dur
                
                db.csv_delete_by_name(
                    where_body='%s=?',
                    where_cols=['tz_date'],
                    params=[date]
                )
                
            else: #we have >= 5 hours of recorded time
                dur_at_6 = select_dur_at_6(db, db_col_names, date)
                
                if dur_at_6 >= MIN_SECS: #recording ends at or after 6pm
                    #delete the rows after 6pm
                    db.csv_delete_by_name(
                        where_body='%s = ? AND %s > ?',
                        where_cols=['tz_date', 'tz_time'],
                        params=[date, '18:00']
                    )
                elif dur_at_6 < MIN_SECS:
                    #delete rows after 5 hours
                    db.csv_delete_by_name(
                        where_body='%s = ? AND %s > ?',
                        where_cols=['tz_date', 'date_start_time'],
                        params=[date, MIN_SECS]
                    )

                #else #dur_at_6 == None:
                    #take the whole recording
                    
                #date, orig dur, trimmed_dur
                if filename not in trimmed_files:
                    trimmed_files[filename] = {}
                trimmed_files[filename][date] = [dur]

        #get a list of all of the dates we have in the file and their end time (durations) after trimming
        date_durs = select_date_durs(db)
        for (filename, date, dur) in date_durs:
            trimmed_files[filename][date].append(dur)
            min_time, max_time = select_info(db, db_col_names, date)
            trimmed_files[filename][date].append(min_time)
            trimmed_files[filename][date].append(max_time)

        db.write_to_file(
            out_path + os.path.basename(file_list[i]),
            omit_col_indices=[22, 23, 24, 27, 28]
        )

    print ''
    print_trimmed_files(trimmed_files)
    print ''
    print_omitted_files(omitted_files)
