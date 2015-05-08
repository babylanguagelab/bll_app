import csv
import glob
import os
import datetime
from db.csv_database import CSVDatabase

path = 'C:/Users/Wayne/Documents/baby-lab/bll/dana/dest/'

dirs = (
    'DaycareCentre/',
    'DaycareHome/',
    'Home/',
)

col_datatypes = [
    float,
    float,
    str,
    str,
    str,
    float,
    float,
    float
]

date_col = 'Date'
date_fmt = '%Y-%m-%d'
time_fmt = '%H:%M:%S'
timestamp_fmt = '%s %s' % (date_fmt, time_fmt)

def run():
    out_file = open(path + 'timetable.csv', 'wb')
    writer = csv.writer(out_file)
    writer.writerow(['Recording', 'Start Date', 'End Date', 'Start Time', 'End Time', 'Total Duration'])
    
    for cur_dir in dirs:
        filenames = glob.glob('%s%s*_done.csv' % (path, cur_dir))

        for cur_file in filenames:
            #print os.path.basename(cur_file)
            
            file_in = open(cur_file, 'rb')
            reader = csv.reader(file_in)
            rows = list(reader)
            file_in.close()

            db = CSVDatabase(rows[0], col_datatypes)
            for cur_row in rows[1:]:
                #print cur_row
                db.csv_insert(cur_row)
            
            min_row = db.csv_select_by_name(
                col_names = [date_col],
                fcn_col_names=[date_col, date_col],
                fcns=['datetime', 'min']
            )

            max_row = db.csv_select_by_name(
                col_names = [date_col],
                fcn_col_names=[date_col, date_col],
                fcns=['datetime', 'max']
            )

            start = datetime.datetime.strptime(min_row[0][0], timestamp_fmt)
            end = datetime.datetime.strptime(max_row[0][0], timestamp_fmt)
            dur = end - start

            writer.writerow([
                os.path.basename(cur_file)[:-4],
                str(start.strftime(date_fmt)),
                str(end.strftime(date_fmt)),
                str(start.strftime(time_fmt)),
                str(end.strftime(time_fmt)),
                str(dur)
            ])
            
