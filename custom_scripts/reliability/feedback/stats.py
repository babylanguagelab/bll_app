import glob
import csv
import os
import datetime
from db.database import Database

input_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/checking/stats/'

spreadsheet_col_names = [
'Index',
'File_Name',
'Child_Age',
'CHN',
'FAN',
'MAN',
'CXN',
'OLN',
'TVN',
'NON',
'SIL',
'FUZ',
#'Recording_Index',
'Elapsed_Time',
'Clock_Time_TZAdj',
'Block_Type',
'Segment_Duration',
'Speaker_ID'
]

data_col_names = ['file_cd', 'file_date'] + ['Row_Index'] + spreadsheet_col_names[1:]

rec_col_names = ['child_cd', 'start', 'end', 'child_age', 'CHN_segs', 'FAN_segs', 'hours']

def create_db(db_name):
    db = Database(db_name)

    db.execute_stmt('''
create table data (
id integer primary key autoincrement,
file_cd text,
file_date date,
Row_Index integer,
File_Name text,
Child_Age integer,
CHN real,
FAN real,
MAN real,
CXN real,
OLN real,
TVN real,
NON real,
SIL real,
FUZ real,
Recording_Index integer,
Elapsed_Time real,
Clock_Time_TZAdj datetime,
Block_Type text,
Segment_Duration real,
Speaker_ID text
);
''')
    
    db.execute_stmt('''
create table recording (
id integer primary key autoincrement,
child_cd text not null,
file_date text not null,
start datetime not null,
end datetime not null,
child_age integer not null,
CHN_segs integer not null,
FAN_segs integer not null,
hours real not null
);
''')

    return db

def parse_datetime(text):
    dt = None
    try:
        dt = datetime.datetime.strptime(text, '%m/%d/%Y %H:%M')
    except ValueError:
        dt = datetime.datetime.strptime(text, '%m/%d/%Y %H:%M:%S')

    return dt

def dump_db(db):
    create_db('disk.db')
    
    db.execute_stmt(
        "attach 'disk.db' as disk;"
        )
    
    db.execute_stmt('insert into disk.data select * from data;')
    db.execute_stmt('insert into disk.recording select * from recording;')

def populate_recording_table(db):
    filename_rows = db.select(
        'data',
        ['File_Name'],
        group_by='File_Name'
    )

    for cur_row in filename_rows:
        filename = cur_row[0]
        child_cd, file_date = filename[:-4].split('_')

        start_row = db.select(
            'data',
            ['min(Clock_Time_TZAdj)'],
            where_cond='File_Name = ?',
            params=[filename]
        )
        start_time = start_row[0][0]

        end_row = db.select(
            'data',
            ["strftime('%Y-%m-%d %H:%M:%f', strftime('%s', max(Clock_Time_TZAdj)) + Segment_Duration, 'unixepoch')"], #add the segment duration on to the end time
            where_cond='File_Name = ?',
            params=[filename]
        )
        end_time = end_row[0][0]

        age_row = db.select(
            'data',
            ['Child_Age'],
            where_cond='File_Name = ?',
            group_by='File_Name', #we only need one row
            params=[filename]
        )
        age = age_row[0][0]

        chn_row = db.select(
            'data',
            ['count(id)'],
            where_cond='File_Name = ? and CHN > 0',
            params=[filename]
        )
        chn_count = chn_row[0][0]

        fan_row = db.select(
            'data',
            ['count(id)'],
            where_cond='File_Name = ? and FAN > 0',
            params=[filename]
        )
        fan_count = fan_row[0][0]

        #this way of calculating hours is more accurate, but we used the following method for the first draft of the manuscript,
        #so we must keep using it in order to be consistent
        # hours_row = db.select(
        #     'data',
        #     ['sum(Segment_Duration) / (60 * 60)'],
        #     where_cond='File_Name = ?',
        #     params=[filename]
        # )
        # hours = hours_row[0][0]

        #just do this through the db - that way we don't have to mess with python datetime objects...
        hours_row = db.select(
            'data',
            ["(strftime('%s',?) - strftime('%s',?)) / 3600.0"],
            where_cond='File_Name = ?',
            params=[end_time, start_time, filename]
        )
        hours = hours_row[0][0]

        rec_col_names = ['child_cd', 'file_date', 'start', 'end', 'child_age', 'CHN_segs', 'FAN_segs', 'hours']

        db.insert(
            'recording',
            rec_col_names,
            [[child_cd, file_date, start_time, end_time, age, chn_count, fan_count, hours]]
        )
    
def process_file(db, filename):
    file_in = open(filename, 'rb')
    reader = csv.DictReader(file_in)
    rows = list(reader)
    file_in.close()

    for cur_row in rows:
        file_cd, file_date = cur_row['File_Name'].split('_')
        file_date = '%s-%s-%s' % (file_date[0:4], file_date[4:6], file_date[6:8])
        db_row = [file_cd, file_date]
        cur_row['Clock_Time_TZAdj'] = parse_datetime(cur_row['Clock_Time_TZAdj'])
                
        for col in spreadsheet_col_names:
            db_row.append(cur_row[col])

        db.insert('data', data_col_names, [db_row])
        
    
def run():
    db = create_db(':memory:')

    filenames = glob.glob('%s*.csv' % (input_path))
    print 'Populating data table...'
    for cur_file in filenames:
        print 'Processing file %s' % (os.path.basename(cur_file))
        process_file(db, cur_file)

    print 'Populating recording table...'
    populate_recording_table(db)
    
    print 'Dumping db to disk...'
    dump_db(db)

        
