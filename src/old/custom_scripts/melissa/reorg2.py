import csv
import glob
import logging
import os
from db.database import Database

in_dirs = ('C:/Users/Wayne/Documents/baby-lab/bll/mel/test_out/10 mo/',
           'C:/Users/Wayne/Documents/baby-lab/bll/mel/test_out/14 mo/'
)

out_dir = 'C:/Users/Wayne/Documents/baby-lab/bll/mel/test_out/'

cols = [
    'filename',
    'age',
    'condition',
    'speaker',
    'sentence_type',
    'question_type',
    'start_time',
    'stop_time',
    'duration',
    'lag_time',
    'mother_max_pitch',
    'mother_min_pitch',
    'mother_mean_pitch',
    'mother_pitch_delta',
    'mother_pitch_category',
    'baby_max_pitch',
    'baby_min_pitch',
    'baby_mean_pitch',
    'baby_pitch_delta',
    'baby_pitch_category',
]

def create_db():
    db = Database(':memory:')
    
    db.execute_stmt(
'''
create table reorg2(
id integer primary key autoincrement,
filename text,
age integer,
condition text,
speaker text,
sentence_type text,
question_type text,
start_time real,
stop_time real,
duration real,
lag_time real,
mother_max_pitch real,
mother_min_pitch real,
mother_mean_pitch real,
mother_pitch_delta real,
mother_pitch_category text,
baby_max_pitch real,
baby_min_pitch real,
baby_mean_pitch reak,
baby_pitch_delta real,
baby_pitch_category text
);
'''
    );

    return db

def populate_db(db):
    filenames = []
    for cur_dir in in_dirs:
        filenames.extend(glob.glob(cur_dir + '*.csv'))

    for cur_filename in filenames:
        cur_filename = cur_filename.replace('\\', '/')
        file_in = open(cur_filename, 'rb')
        reader = csv.reader(file_in)
        rows = list(reader)
        file_in.close()

        for cur_row in rows[1:]:
            age = 10 if cur_filename.find('10 mo/') > -1 else 14
            cur_row.insert(1, age)
            
            db.insert(
                'reorg2',
                cols,
                [cur_row]
            )

def get_file_age_pairs(db):
    data = db.select(
        'reorg2',
        ('distinct(filename)', 'age',),
        order_by='age, filename ASC',
    )

    filenames = []
    ages = []
    for pair in data:
        filenames.append(pair[0])
        ages.append(pair[1])

    return filenames, ages

def maternalUttType(db, filenames, ages):
    file_out = open(out_dir + 'maternalUttType.csv', 'wb')
    writer = csv.writer(file_out)
    writer.writerow(('', '', 'Declaratives', '', '', 'YN', '', '', 'WH', '', '',))
    writer.writerow(('filename', 'age', 'High', 'Low', 'Other', 'High', 'Low', 'Other', 'High', 'Low', 'Other',))
    
    pitches = ('High', 'Low', '',)
    sentence_types = ('D', 'Q', 'Q')
    question_types = ('', 'Y/N', 'WH Question',)
    for i in range(len(filenames)):
        cur_filename = filenames[i]
        cur_age = ages[i]
        csv_row = [cur_filename, cur_age]
        
        for j in range(len(sentence_types)):
            cur_stype = sentence_types[j]
            cur_qtype = question_types[j]
            
            for cur_pitch in pitches:
                db_row = db.select(
                    'reorg2',
                    ('count(id)',),
                    where_cond="filename=? AND speaker=? AND sentence_type=? AND question_type=? AND mother_pitch_category=?",
                    params=(cur_filename, 'M', cur_stype, cur_qtype, cur_pitch,)
                )
                csv_row.append(db_row[0][0])

        writer.writerow(csv_row)
    file_out.close()

def maternalUttPitchDiff(db, filenames, ages):
    file_out = open(out_dir + 'maternalUttPitchDiff.csv', 'wb')
    writer = csv.writer(file_out)
    writer.writerow(('', '', 'Declaratives', '', '', 'YN', '', '', 'WH', '', '',))
    writer.writerow(('filename', 'age', 'High', 'Low', 'Other', 'High', 'Low', 'Other', 'High', 'Low', 'Other',))

    pitches = ('High', 'Low', '',)
    sentence_types = ('D', 'Q', 'Q')
    question_types = ('', 'Y/N', 'WH Question',)
    for i in range(len(filenames)):
        cur_filename = filenames[i]
        cur_age = ages[i]
        csv_row = [cur_filename, cur_age]
        
        for j in range(len(sentence_types)):
            cur_stype = sentence_types[j]
            cur_qtype = question_types[j]
            
            for cur_pitch in pitches:
                db_row = db.select(
                    'reorg2',
                    ('avg(mother_pitch_delta)',),
                    where_cond="filename=? AND speaker=? AND sentence_type=? AND question_type=? AND mother_pitch_category=?",
                    params=(cur_filename, 'M', cur_stype, cur_qtype, cur_pitch,)
                )
                csv_row.append(db_row[0][0])

        writer.writerow(csv_row)
    file_out.close()

def infantResponseSummary(db, filenames, ages):
    file_out = open(out_dir + 'infantResponseSummary.csv', 'wb')
    writer = csv.writer(file_out)
    writer.writerow(('', '', 'Declaratives', '', '', 'YN', '', '', 'WH', '', '',))
    writer.writerow(('filename', 'age',
                     'Mother High', 'Mother Low', 'Mother Other',
                     'Mother High', 'Mother Low', 'Mother Other',
                     'Mother High', 'Mother Low', 'Mother Other',
                 ))
    
    pitches = ('High', 'Low', '',)
    sentence_types = ('D', 'Q', 'Q')
    question_types = ('', 'Y/N', 'WH Question',)
    for i in range(len(filenames)):
        cur_filename = filenames[i]
        cur_age = ages[i]
        csv_row = [cur_filename, cur_age]
        
        for j in range(len(sentence_types)):
            cur_stype = sentence_types[j]
            cur_qtype = question_types[j]
            
            for cur_pitch in pitches:
                db_row = db.select(
                    'reorg2',
                    ('count(id)',),
                    where_cond="filename=? AND speaker=? AND sentence_type=? AND question_type=? AND mother_pitch_category=? AND (baby_mean_pitch != '' or baby_max_pitch != '' or baby_min_pitch != '')",
                    params=(cur_filename, 'M', cur_stype, cur_qtype, cur_pitch,)
                )
                csv_row.append(db_row[0][0])

        writer.writerow(csv_row)
    file_out.close()

def infantResponseDeclarative(db, filenames, ages):
    file_out = open(out_dir + 'infantResponseDeclarative.csv', 'wb')
    writer = csv.writer(file_out)
    writer.writerow(('', '', 'Mother High', '', '', 'Mother Low', '', '', 'Mother Other', '', '',))
    writer.writerow(('filename', 'age',
                     'Infant High', 'Infant Low', 'Infant Other',
                     'Infant High', 'Infant Low', 'Infant Other',
                     'Infant High', 'Infant Low', 'Infant Other',
                 ))
    
    pitches = ('High', 'Low', '',)
    for i in range(len(filenames)):
        cur_filename = filenames[i]
        cur_age = ages[i]
        csv_row = [cur_filename, cur_age]
        
        for mother_pitch in pitches:
            for baby_pitch in pitches:
                db_row = db.select(
                    'reorg2',
                    ('count(id)',),
                    where_cond="filename=? AND speaker=? AND sentence_type=? AND question_type=? AND mother_pitch_category=? AND baby_pitch_category=?",
                    params=(cur_filename, 'M', 'D', '',  mother_pitch, baby_pitch)
                )
                csv_row.append(db_row[0][0])

        writer.writerow(csv_row)
    file_out.close()

def infantResponseYN(db, filenames, ages):
    file_out = open(out_dir + 'infantResponseYN.csv', 'wb')
    writer = csv.writer(file_out)
    writer.writerow(('', '', 'Mother High', '', '', 'Mother Low', '', '', 'Mother Other', '', '',))
    writer.writerow(('filename', 'age',
                     'Infant High', 'Infant Low', 'Infant Other',
                     'Infant High', 'Infant Low', 'Infant Other',
                     'Infant High', 'Infant Low', 'Infant Other',
                 ))
    
    pitches = ('High', 'Low', '',)
    for i in range(len(filenames)):
        cur_filename = filenames[i]
        cur_age = ages[i]
        csv_row = [cur_filename, cur_age]
        
        for mother_pitch in pitches:
            for baby_pitch in pitches:
                db_row = db.select(
                    'reorg2',
                    ('count(id)',),
                    where_cond="filename=? AND speaker=? AND sentence_type=? AND question_type=? AND mother_pitch_category=? AND baby_pitch_category=?",
                    params=(cur_filename, 'M', 'Q', 'Y/N',  mother_pitch, baby_pitch)
                )
                csv_row.append(db_row[0][0])

        writer.writerow(csv_row)
    file_out.close()

def infantResponseWHQ(db, filenames, ages):
    file_out = open(out_dir + 'infantResponseWHQ.csv', 'wb')
    writer = csv.writer(file_out)
    writer.writerow(('', '', 'Mother High', '', '', 'Mother Low', '', '', 'Mother Other', '', '',))
    writer.writerow(('filename', 'age',
                     'Infant High', 'Infant Low', 'Infant Other',
                     'Infant High', 'Infant Low', 'Infant Other',
                     'Infant High', 'Infant Low', 'Infant Other',
                 ))
    
    pitches = ('High', 'Low', '',)
    for i in range(len(filenames)):
        cur_filename = filenames[i]
        cur_age = ages[i]
        csv_row = [cur_filename, cur_age]
        
        for mother_pitch in pitches:
            for baby_pitch in pitches:
                db_row = db.select(
                    'reorg2',
                    ('count(id)',),
                    where_cond="filename=? AND speaker=? AND sentence_type=? AND question_type=? AND mother_pitch_category=? AND baby_pitch_category=?",
                    params=(cur_filename, 'M', 'Q', 'WH Question',  mother_pitch, baby_pitch)
                )
                csv_row.append(db_row[0][0])

        writer.writerow(csv_row)
    file_out.close()

def check_log_file(path):
    if not os.path.exists(path):
        logfile = open(path, 'w')
        logfile.close()
    
def run():
    LOGFILE = 'logs/reorg2.log'

    #create log file if it doesn't exist
    check_log_file(LOGFILE)
    #set up logging
    logging.basicConfig(level=logging.ERROR,
                        filename=LOGFILE,
                        format='%(asctime)s %(message)s') #prefix each message with a timestamp
    
    db = create_db()
    populate_db(db)

    filenames, ages = get_file_age_pairs(db)
    
    maternalUttType(db, filenames, ages)
    maternalUttPitchDiff(db, filenames, ages)
    infantResponseSummary(db, filenames, ages)
    infantResponseDeclarative(db, filenames, ages)
    infantResponseYN(db, filenames, ages)
    infantResponseWHQ(db, filenames, ages)

    db.close()
