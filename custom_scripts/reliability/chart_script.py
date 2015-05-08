import csv
import glob
from collections import OrderedDict

def get_delim(cur_file):
    line = cur_file.readline()
    delim = '\t' if line.find('\t') > -1 else ','
    cur_file.seek(0)

    return delim

def parse_reliability_filecode(file_handle):
    filecode = None
    row = file_handle.next().strip().strip(',')
    while row != '':
        if row.startswith('TRS file:'):
            filecode = row.split('\\')[-1]
            filecode = filecode[:-12]

        row = file_handle.next().strip().strip(',')

    return filecode

def parse_reliability_row(row1, row2, time_dict, filecode, reliability_time_cols, reliability_in_cols, reliability_out_cols):
    row = row2

    start = float(row[reliability_time_cols[0]]) + float(row['Context Padding'])
    end = float(row[reliability_time_cols[1]]) - float(row['Context Padding'])
    key = filecode + ':' + str(start) + '-' + str(end)
    #print key
    
    if not key in time_dict:
        time_dict[key] = {}

    for i in range(len(reliability_in_cols)):
        in_name = reliability_in_cols[i]
        out_name = reliability_out_cols[i]
        time_dict[key][out_name] = row[in_name]

def process_reliability_file(filename, time_dict, reliability_time_cols, reliability_in_cols, reliability_out_cols):
    f = open(filename, 'rb')
    filecode = parse_reliability_filecode(f)
    reader = csv.DictReader(f)

    rows = [row for row in reader][:-1] #last row is 'ratio correct
    for i in range(len(rows) / 2):
        row1 = rows[i * 2]
        row2 = rows[i * 2 + 1]
        parse_reliability_row(row1, row2, time_dict, filecode, reliability_time_cols, reliability_in_cols, reliability_out_cols)

    f.close()

def parse_other_row(row, time_dict, time_cols, in_cols, out_cols):
    start = row[time_cols[0]]
    end = row[time_cols[1]]
    filecode = row['File_Name'][:-4]

    key = filecode + ':' + str(start) + '-' + str(end)
    #print key

    if not key in time_dict:
        time_dict[key] = {}

    for i in range(len(in_cols)):
        in_name = in_cols[i]
        out_name = out_cols[i]
        time_dict[key][out_name] = row[in_name]

def process_other_file(filename, time_dict, time_cols, in_cols, out_cols):
    f = open(filename, 'rb')
    delim = get_delim(f)
    reader = csv.DictReader(f, delimiter=delim)

    for row in reader:
        parse_other_row(row, time_dict, time_cols, in_cols, out_cols)

    f.close()

def write_output_file(time_dict, bound_out_cols, reliability_out_cols):
    f = open('out.csv', 'wb')
    writer = csv.writer(f)

    #write headers
    line = []
    headers = bound_out_cols + reliability_out_cols
    
    for col in headers:
        line.append(col)
    line.append('File Code')
    writer.writerow(line)
    
    for key in time_dict:
        line = []
        row = time_dict[key]
        for col in headers:
            if col in row:
                line.append(row[col])
            else:
                line.append('')
        line.append(key.split(':')[0])
        writer.writerow(line)

    f.close()

def main():
    bound_time_cols = ('Original_Wav.Begin', 'Original_Wav.End')
    #syllable_time_cols = ('Wav.Begin', 'Wav.End')
    reliability_time_cols = ('LENA Start Time (- padding)', 'LENA End Time (+ padding)')

    #bound_in_cols = ('File_Name', 'Original_Wav.Begin', 'Original_Wav.End', 'Wav.Begin', 'Wav.End')
    bound_in_cols = ('Wav.Begin', 'Wav.End')
    #reliability_in_cols = ('LENA Start Time (- padding)', 'LENA End Time (+ padding)', 'Context Padding', 'User-Adjusted Start Time', 'User-Adjusted End Time')
    reliability_in_cols = ('User-Adjusted Start Time', 'User-Adjusted End Time')

    #bound_out_cols = ('Bound File Name', 'Bound Orig Wav.Begin', 'Bound Orig Wav.End', 'Bound Adj Wav.Begin', 'Bound Adj Wav.End')
    bound_out_cols = ('Praat Adj Wav.Begin', 'Praat Adj Wav.End')
    #reliability_out_cols = ('Rel Orig Wav.Begin', 'Rel Orig Wav.End', 'Rel Context', 'Rel Human Wav.Begin', 'Rel Human Wav.End')
    reliability_out_cols = ('Human Adj Wav.Begin', 'Human Adj Wav.End')
    
    bound_filename = 'C:\\Experimental Data\\Daycare Study\\ADEX Output\\Feedback-Melissa\\exclusion data\\out.txt'
    #bound_filename = 'E:\\baby-lab\\test-data\\reliability\\redefine_pauses Output\\bounds_fixed.txt'
    reliability_folder = 'C:\\Experimental Data\\Daycare Study\\ADEX Output\\Feedback-Melissa\\Reliability\\Reliability Output\\1.1\\CHN'
    #reliability_folder = 'E:\\baby-lab\\test-data\\reliability\\Reliability Output\\test'

    time_dict = OrderedDict()

    reliability_files = glob.glob(reliability_folder + '\\*.csv')

    for cur_filename in reliability_files:
        process_reliability_file(cur_filename, time_dict, reliability_time_cols, reliability_in_cols, reliability_out_cols)

    process_other_file(bound_filename, time_dict, bound_time_cols, bound_in_cols, bound_out_cols)

    write_output_file(time_dict, bound_out_cols, reliability_out_cols)

main()
