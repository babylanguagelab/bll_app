import os
import sys
import csv

#windows shortcut launches this script in the 'bll_app\ directory., but the python path constains 'bll_app\custom_processing_scripts\'
#We must append the parent directory to the path so the python runtime can find our custom modules properly
sys.path.append( os.path.realpath('.') )

from utils.ui_utils import UIUtils

def main():
    input_foldername = UIUtils.open_folder(title='Select Source Folder')
    output_foldername = None
    if input_foldername:
        output_foldername = UIUtils.open_folder(title='Select Destination Folder')

    if not input_foldername or not output_foldername:
        exit()

    csv_filenames = filter(lambda name: name.lower().endswith('.csv'), os.listdir(input_foldername))
    for filename in csv_filenames:
        process_file(input_foldername + '\\' + filename, output_foldername + '\\' + filename)

    print 'Filtering complete.'

def build_col_info(header_row):
    col_info = {'wav.begin': -1,
                'wav.end': -1,
                'segment_duration': -1,
                'elapsed_time': -1,
                'adult count': -1,
                'child count': -1,
                }
    
    i = 0
    while (i < len(header_row)):
        col_name = header_row[i].lower()
        if col_name in col_info:
            col_info[col_name] = i
        i += 1

    return col_info

def bail_out(input_file, output_filename, output_rows):
    input_file.close()

    if output_rows:
        try:
            output_file = open(output_filename, 'wb')
            writer = csv.writer(output_file, delimiter='\t')
            map(lambda row: writer.writerow(row), output_rows)
            output_file.close()
        except Exception as e:
            print 'Unable to write output file, skipping.'
            print 'Exception %s' % e

def process_file(input_filename, output_filename):
    print 'Processing file %s...' % (input_filename)

    output_rows = []
    try:
        input_file = open(input_filename, 'rb')
    except Exception:
        print 'Unable to read file, skipping.'
        return
    
    reader = csv.reader(input_file)

    #go through header row
    try:
        cur_row = reader.next()
    except StopIteration:
        print 'File contains no rows, skipping.'
        bail_out(input_file, output_filename, output_rows)
        return

    col_info = build_col_info(cur_row)
    if col_info['adult count'] < 0 or col_info['child count'] < 0:
        print 'File is missing "Adult Count" or "Child Count" columns, skipping.'
        bail_out(input_file, output_filename, output_rows)
        return

    add_begin = col_info['wav.begin'] < 0 and col_info['elapsed_time'] >= 0
    add_end = col_info['wav.end'] < 0 and col_info['elapsed_time'] >= 0 and col_info['segment_duration'] >= 0
    if add_begin:
        cur_row.append('Wav.Begin')
    if add_end:
        cur_row.append('Wav.End')

    output_rows.append(cur_row)
    
    #go through any remaining rows
    try:
        cur_row = reader.next()
    except StopIteration: #end of file
        bail_out(input_file, output_filename, output_rows)
        return
        
    while cur_row:
        try:
            adult_count = int(cur_row[col_info['adult count']])
            child_count = int(cur_row[col_info['child count']])
            include_row = adult_count == 1 and child_count == 1
        except ValueError, TypeError:
            include_row = False

        if include_row:
            if add_begin:
                start_time = cur_row[col_info['elapsed_time']]
                if start_time == '' or start_time == None:
                    print 'Warning: Unable to read "Elapsed Time" column, appending "?" to "Wav.End" cell.'
                    start_time = '?'
                cur_row.append(start_time)

            if add_end:
                try:
                    end_time = float(cur_row[col_info['elapsed_time']])
                    end_time += float(cur_row[col_info['segment_duration']])
                    cur_row.append(end_time)
                except ValueError, TypeError:
                    print 'Warning: Unable to read "Elapsed Time" or "Segment Duration" column, appending "?" to "Wav.End" cell.'
                    cur_row.append('?')

            output_rows.append(cur_row)

        try:
            cur_row = reader.next()
        except StopIteration: #end of file
            cur_row = None

    print 'Done File.'
    bail_out(input_file, output_filename, output_rows)

main()
