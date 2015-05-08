from db.database import Database
import os
import shutil
import csv

def _get_header():
    return [
        'Batch Number',
        'Participant Number',
        'Order Number',
        'Question Rating',
        'Filename',
        'Age',
        'Condition',
        'Speaker',
        'Sentence Type',
        'Question Type',
        'Start Time',
        'Stop Time',
        'Duration',
        'Lag Time',
        'Mother Max Pitch',
        'Mother Min Pitch',
        'Mother Mean Pitch',
        'Mother Pitch Delta',
        'Mother Pitch Category',
        'Baby Max Pitch',
        'Baby Min Pitch',
        'Baby Mean Pitch',
        'Baby Pitch Delta',
        'Baby Pitch Category',
    ]

def _get_agregate_header():
    return [
        'Batch Number',
        'Order Number',
        'Filename',
        'Age',
        'Min Question Rating',
        'Max Question Rating',
        'Mean Question Rating',
        'Filename',
        'Age',
        'Condition',
        'Speaker',
        'Sentence Type',
        'Question Type',
        'Start Time',
        'Stop Time',
        'Duration',
        'Lag Time',
        'Mother Max Pitch',
        'Mother Min Pitch',
        'Mother Mean Pitch',
        'Mother Pitch Delta',
        'Mother Pitch Category',
        'Baby Max Pitch',
        'Baby Min Pitch',
        'Baby Mean Pitch',
        'Baby Pitch Delta',
        'Baby Pitch Category',
    ]


def _get_part_data(db, batch_num, part_num):
    rows = db.select(
        'clips c join ratings r on c.id = r.clip_id',
        [
            'c.Batch_Num',
            'r.Participant_Num',
            'c.Batch_Order',
            'r.Question_Rating',
            'c.Filename',
            'c.Age',
            'c.Condition',
            'c.Speaker',
            'c.Sentence_Type',
            'c.Question_Type',
            'c.Start_Time',
            'c.Stop_Time',
            'c.Duration',
            'c.Lag_Time',
            'c.Mother_Max_Pitch',
            'c.Mother_Min_Pitch',
            'c.Mother_Mean_Pitch',
            'c.Mother_Pitch_Delta',
            'c.Mother_Pitch_Category',
            'c.Baby_Max_Pitch',
            'c.Baby_Min_Pitch',
            'c.Baby_Mean_Pitch',
            'c.Baby_Pitch_Delta',
            'c.Baby_Pitch_Category',
        ],
        where_cond = 'c.Batch_Num = ? and r.Participant_Num = ?',
        order_by = 'c.Batch_Order',
        params = [batch_num, part_num]
    )
    
    return rows

def _get_agregate_part_data(db, batch_num):
    rows = db.select(
        'clips c join ratings r on c.id = r.clip_id',
        [
            'c.Batch_Num',
            'c.Batch_Order',
            'c.Filename',
            'c.Age',
            'min(r.Question_Rating)',
            'max(r.Question_Rating)',
            'avg(r.Question_Rating)',
            'c.Filename',
            'c.Age',
            'c.Condition',
            'c.Speaker',
            'c.Sentence_Type',
            'c.Question_Type',
            'c.Start_Time',
            'c.Stop_Time',
            'c.Duration',
            'c.Lag_Time',
            'c.Mother_Max_Pitch',
            'c.Mother_Min_Pitch',
            'c.Mother_Mean_Pitch',
            'c.Mother_Pitch_Delta',
            'c.Mother_Pitch_Category',
            'c.Baby_Max_Pitch',
            'c.Baby_Min_Pitch',
            'c.Baby_Mean_Pitch',
            'c.Baby_Pitch_Delta',
            'c.Baby_Pitch_Category',
        ],
        where_cond = 'c.Batch_Num = ?',
        group_by = 'c.Batch_Order',
        params = [batch_num]
    )
    
    return rows

def _export_agregate_part(db, out_dir, batch_num):
    out_filename = '%sStats.csv' % (out_dir)
    out_file = open(out_filename, 'wb')
    writer = csv.writer(out_file)

    writer.writerow(_get_agregate_header())
    rows = _get_agregate_part_data(db, batch_num)

    for cur_row in rows:
        writer.writerow(cur_row)

    out_file.close()
    
def _export_part(db, out_dir, batch_num, part_num):
    out_filename = '%sParticipant%d.csv' % (out_dir, part_num)
    out_file = open(out_filename, 'wb')
    writer = csv.writer(out_file)

    writer.writerow(_get_header())
    rows = _get_part_data(db, batch_num, part_num)

    for cur_row in rows:
        writer.writerow(cur_row)

    out_file.close()

def _export_batch(db, batch_num, save_dir):
    rows = db.select(
        'clips c join ratings r on c.id = r.clip_id',
        ['distinct r.Participant_Num'],
        where_cond = 'c.Batch_Num = ?',
        params = [batch_num]
    )

    out_dir = '%sbatch%d/' % (save_dir, batch_num)
    #make way! ...
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.mkdir(out_dir)

    part_nums = map(lambda line: line[0], rows)
    for cur_part_num in part_nums:
        _export_part(db, out_dir, batch_num, cur_part_num)

    _export_agregate_part(db, out_dir, batch_num)

def export_data(db_path, save_dir, progress_fraction_fcn):
        db = Database(db_path)

        rows = db.select(
            'clips',
            ['distinct Batch_Num'],
            where_cond = 'Batch_Num is not null'
        )
        batch_nums = map(lambda line: line[0], rows)

        for i in range(len(batch_nums)):
            _export_batch(db, batch_nums[i], save_dir)
            progress_fraction_fcn((i + 1) / float(len(batch_nums)))
        
        db.close()
