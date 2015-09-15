import csv
import os
import glob

#space is places at the colulmn after this index
COL_SPACES = [3, 6, 8, 9, 17]

input_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/'
envs = (
    'home',
    'home daycare',
    'daycare centre',
)

def space_row(row):
    offset = 0
    for index in COL_SPACES:
        row.insert(index + 1 + 1 + offset, '') #one space for row legend, one space for inserting *after* the index
        offset += 1

    return row

def space_file(csv_filename):
    in_file = open(csv_filename, 'rb')
    reader = csv.reader(in_file)

    in_rows = list(reader)
    in_file.close()
    out_rows = []
    for cur_row in in_rows[:-6]:
        out_rows.append(space_row(cur_row))
        
    for cur_row in in_rows[-6:]:
        out_rows.append(cur_row + [''] * len(COL_SPACES))

    write_file(csv_filename, out_rows)
    
def write_file(filename, rows):
    out_file = open(filename, 'wb')
    writer = csv.writer(out_file)
    for cur_row in rows:
        writer.writerow(cur_row)
    out_file.close()

def run():
    for cur_env in envs:
        input_dir = '%s%s/' % (input_path, cur_env)
        dir_contents = glob.glob('%s*.csv' % (input_dir))

        for filename in dir_contents:
            space_file(filename)
                

