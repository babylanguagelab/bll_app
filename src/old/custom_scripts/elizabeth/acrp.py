import csv
import glob
import os
from db.csv_database import CSVDatabase

in_path = 'G:/ACRP-Sam/data/'
out_path = 'G:/ACRP-Sam/data/'
dirs = (
    'daycare-centre/',
    'home/',
    'home-daycare/',
)

col_datatypes = (
    int,   #Index
    int,   #File_Name
    str,   #Number_Recordings
    int,   #File_Hours
    float, #Child_ChildID
    str,   #Child_Age
    int,   #Child_Gender
    str,   #AWC
    int,   #Turn_Count
    int,   #Child_Voc_Count
    float, #CHN
    float, #Child_Voc_Duration
    int,   #FAN_Word_Count
    float, #FAN
    float, #MAN_Word_Count
    float, #MAN
    float, #CXN
    float, #OLN
    float, #TVN
    float, #NON
    float, #SIL
    str,   #EMLU (value can be "ORL" or a float)
    int,   #AVA_DA
    int,   #Recording_Index
    int,   #Elapsed_Time
    str,   #Clock_Time_TZAdj
    float, #Audio_Duration
    int,   #Adult Count
    int,   #Child Count
    float, #Adult:Child Ratio
    str,   #Naptime
    float, #Wav.Begin
    float, #Wav.End
)

def select_fcn_in(db, fcn, fcn_col_name, criteria_name, lower, upper):
    return db.csv_select_by_name(
        col_names = (fcn_col_name,),
        where_body = '%s >= ? and %s <= ?',
        where_cols = (criteria_name, criteria_name),
        params = (lower, upper),
        fcn_col_names = (fcn_col_name,),
        fcns = (fcn,)
    )

def select_fcn_eq(db, fcn, fcn_col_name, criteria_name, val):
    return select_fcn_in(db, fcn, fcn_col_name, criteria_name, val, val)

def select_fcn_ge(db, fcn, fcn_col_name, criteria_name, val):
    return db.csv_select_by_name(
        col_names = (fcn_col_name,),
        where_body = '%s >= ?',
        where_cols = (criteria_name,),
        params = (val,),
        fcn_col_names = (fcn_col_name,),
        fcns = (fcn,)
    )

def to_num(n):
    #return 0 if n == None else n
    return n

def calc_section(db, count_col): #count_col is the top level criteria (AWC, CVC, CTC)
    out_row = []
    
    #Child Count
    rows = select_fcn_eq(db, 'avg', count_col, 'Child Count', 1)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_eq(db, 'avg', count_col, 'Child Count', 2)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_in(db, 'avg', count_col, 'Child Count', 3, 5)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_in(db, 'avg', count_col, 'Child Count', 6, 9)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_ge(db, 'avg', count_col, 'Child Count', 10)
    out_row.append(to_num(rows[0][0]))

    #Adult Count
    rows = select_fcn_eq(db, 'avg', count_col, 'Adult Count', 0)
    out_row.append(to_num(rows[0][0]))
    
    rows = select_fcn_eq(db, 'avg', count_col, 'Adult Count', 1)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_eq(db, 'avg', count_col, 'Adult Count', 2)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_eq(db, 'avg', count_col, 'Adult Count', 3)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_in(db, 'avg', count_col, 'Adult Count', 4, 7)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_ge(db, 'avg', count_col, 'Adult Count', 8)
    out_row.append(to_num(rows[0][0]))

    #Ratio (denominator)
    rows = select_fcn_eq(db, 'avg', count_col, 'Adult:Child Ratio', 1)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_in(db, 'avg', count_col, 'Adult:Child Ratio', 0.33, 0.5)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_in(db, 'avg', count_col, 'Adult:Child Ratio', 0.166, 0.25)
    out_row.append(to_num(rows[0][0]))

    rows = select_fcn_eq(db, 'avg', count_col, 'Adult:Child Ratio', 0.142)
    out_row.append(to_num(rows[0][0]))

    return out_row

def write_headers(writer):
    props = [
        'Participant Code',
        'Recording',
        'Initial Age (months)',
        'Initial AVA_DA (months)',
        'Gender',
        'EMLU'
    ]

    #double-quote to prevent Excel from interpreting ranges as dates. Bad Excel. Bad.
    cats = [
        '"1"',
        '"2"',
        '"3-5"', 
        '"6-9"',
        '"10+"',
        '"0"',
        '"1"',
        '"2"',
        '"3"',
        '"4-7"',
        '"8+"',
        '"1"',
        '"2-3"',
        '"4-6"',
        '"7"'
    ]

    #line3
    line3 = props + (cats * 3)

    #line2
    line2 = [''] * len(line3)
    for i in range(3):
        line2[len(props) + i * len(cats) + 2] = 'Child Count'
        line2[len(props) + i * len(cats) + 7] = 'Adult Count'
        line2[len(props) + i * len(cats) + 12] = 'Ratio (denominator)'

    #line1
    line1 = [''] * len(line3)
    line1[len(props) / 2 - 1] = 'Inter-Participant Variables'
    labels = (
        'Adult Word Count',
        'Child Vocalizations',
        'Conversational Turns'
    )
    for i in range(3):
        line1[len(props) + i * len(cats) + len(cats) / 2] = labels[i]

    #write to file
    for out_row in (line1, line2, line3):
        writer.writerow(out_row)

def run():
    for cur_dir in dirs:
        print 'Entering directory "%s"' % (cur_dir)
        
        file_list = glob.glob('%s%s*.csv' % (in_path, cur_dir))
        file_list.sort()
        
        out_file = open('%s%s.csv' % (out_path, cur_dir[:-1]), 'wb')
        writer = csv.writer(out_file)
        write_headers(writer)

        for filename in file_list:
            print 'Processing File "%s"' % (os.path.basename(filename))
            db = CSVDatabase.create_with_files((filename,), col_datatypes)
            out_row = []

            # --- Inter-Participant Variables ---
            rows = db.csv_select_by_name(
                col_names = (
                    'Child_ChildID',
                    'File_Name',
                    'Child_Age',
                    'AVA_DA',
                    'Child_Gender',
                    'EMLU'
                ),
            )

            out_row.extend(rows[0])

            #Adult Word Count (AWC)
            out_row.extend(calc_section(db, 'AWC'))

            #Child Vocalizations (CVC)
            out_row.extend(calc_section(db, 'Child_Voc_Count'))

            #Conversational Turns (CTC)
            out_row.extend(calc_section(db, 'Turn_Count'))

            #write to file
            writer.writerow(out_row)
            
        out_file.close()
        print ''

    print 'Done.'

