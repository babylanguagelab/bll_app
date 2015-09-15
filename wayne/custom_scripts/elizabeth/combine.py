import glob
import csv
import os
from db.csv_database import CSVDatabase

in_path = 'G:/ACRP-Sam/data/'
out_filename = 'G:/ACRP-Sam/combined.csv'
col_datatypes = [
    str,
    str,
    float,
    float,
    str,
    float
] + [float] * 45

def fix_header_section(row, start_index, l1, l2, num_cols):
    for i in range(num_cols):
        row[start_index + i] = '%s-%s-%s' % (l1, l2, row[start_index + i][1:-1])

def fix_header_names(row):
    l1 = ['AWC', 'CVC', 'CTC']
    l2 = ['CC', 'AC', 'R']
    lens = [5, 5, 4]
    start_index = 6

    for i in range(len(l1)):
        for j in range(len(l2)):
            fix_header_section(row, start_index, l1[i], l2[j], lens[j])
            start_index += lens[j]

def run():
    file_list = glob.glob(in_path + '*.csv')
    out_file = open(out_filename, 'wb')
    writer = csv.writer(out_file)
    wrote_headers = False

    for cur_file in file_list:
        file_in = open(cur_file, 'rb')
        reader = csv.reader(file_in)
        rows = list(reader)
        file_in.close()

        if not wrote_headers:
            for cur_row in rows[:3]:
                writer.writerow(cur_row[0:1] + cur_row[2:]) #cut out 'Recording' row
            wrote_headers = True
            
        header = rows[2]
        fix_header_names(header)

        db = CSVDatabase(header, col_datatypes)
        
        for cur_row in rows[3:]:
            db.csv_insert(cur_row)

        db.set_blanks_to_null()

        #db.dump_to_file('%s.db' % (os.path.basename(cur_file)[:-4]))

        avg_col_indices = filter(lambda i: col_datatypes[i] == float, range(len(col_datatypes)))

        avg_rows = db.csv_select_by_index(
            fcn_indices=avg_col_indices,
            fcns=['avg'] * len(avg_col_indices),
            group_by_index=0
        ) 

        for cur_row in avg_rows:
            writer.writerow(cur_row[0:1] + cur_row[2:]) #cut out 'Recording' row

    out_file.close()

        
        
        
        
