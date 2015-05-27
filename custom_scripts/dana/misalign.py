import csv
import glob
import os
from parsers.trs_parser import TRSParser

def get_row_dur(row, speaker_cds):
    dur = 0
    for cd in speaker_cds:
        dur += float(row[cd])

    return dur

def get_time_str(time):
    return '%0.2f' % (time)

def check_pair(csv_filename, trs_filename, speaker_cds):
    csv_file = open(csv_filename, 'rb')

    trs_segs = TRSParser(trs_filename).parse(validate=False)
    csv_reader = csv.DictReader(csv_file)
    csv_segs = list(csv_reader)
    csv_file.close()

    i = 0
    j = 0
    csv_start = float(csv_segs[i]['Elapsed_Time'])
    trs_start = trs_segs[j].start
    error_msg = ''
    misaligned = round(csv_start, 2) != round(trs_start, 2)
    if misaligned:
        error_msg = 'File start times are different.'
    
    while i < len(csv_segs) and j < len(trs_segs) and not misaligned:
        csv_end = csv_start + get_row_dur(csv_segs[i], speaker_cds)
        trs_start = trs_segs[j].start
        trs_end = trs_segs[j].end

        r_csv_start = round(csv_start, 2)
        r_trs_start = round(trs_start, 2)
        r_csv_end = round(csv_end, 2)
        r_trs_end = round(trs_end, 2)

        if r_csv_end == r_trs_end:
            i += 1
            j += 1
            csv_start = csv_end
            
        elif r_csv_end < r_trs_end:
            i += 1
            csv_start = csv_end
            
        elif r_csv_end > r_trs_end:
            misaligned = True
            error_msg = 'csv: %f - %f\ntrs: %f - %f' % (r_csv_start, r_csv_end, r_trs_start, r_trs_end)

    return misaligned, error_msg

def run():
    folders = ('E:/test/Home/',
           'E:/test/DaycareCentre/',
           )

    speaker_cds = 'CHN FAN MAN CXN OLN TVN NON SIL FUZ'.split()

    for cur_folder in folders:
        csv_filenames = glob.glob('%s*.csv' % (cur_folder))
        for i in range(len(csv_filenames)):
            folder_msg = 'Entering folder %s/' % (cur_folder.split('/')[-2])
            msg_sep = '-' * len(folder_msg)
            print msg_sep
            print folder_msg
            print msg_sep
            
            trs_filename = '%strs' % (csv_filenames[i][:-3])

            print 'Checking %s...' % (os.path.basename(csv_filenames[i])[:-4])
            
            if os.path.exists(trs_filename):
                misaligned, error_msg = check_pair(csv_filenames[i], trs_filename, speaker_cds)
                print 'Alignment: %s' % ('good bad'.split()[int(misaligned)])
                if misaligned:
                    print error_msg
            else:
                print 'No trs file found.'

            print ''
