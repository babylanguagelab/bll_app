from db.csv_database import CSVDatabase
from db.database import Database
import glob
import csv
import os

path = 'G:/confusion/ADEX/'
col_datatypes = (
    int,
    str,
    int,
    float,
    str,
    int,
    str,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    int,
    int,
    float,
    str,
    float,
    float,
    float,
    int,
    str,
    str,
    float,
    str,
    str,
    int,
    int,
    str,
    str,
    float,
    str
)

envs = (
    'daycare centre',
    'home daycare',
    'home',
)

def time_fix(files):
    for cur_file in files:
        file_in = open(cur_file, 'rb')
        reader = csv.DictReader(file_in)
        rows = list(reader)
        file_in.close()

        file_out = open('%s-fixed.csv' % (cur_file[:-4]), 'wb')
        writer = csv.DictWriter(file_out, reader.fieldnames + ['Wav.Begin', 'TRS Filename'])
        writer.writeheader()

        time = float(rows[0]['Elapsed_Time'])
        rows[0]['Wav.Begin'] = time
        rows[0]['TRS Filename'] = os.path.basename(cur_file)
        writer.writerow(rows[0])
        time += float(rows[0]['Segment_Duration'])
        for cur_row in rows[1:]:
            cur_row['Wav.Begin'] = time
            cur_row['TRS Filename'] = os.path.basename(cur_file)
            time += float(cur_row['Segment_Duration'])
            writer.writerow(cur_row)

        file_out.close()

def get_data():
    boundaries = {
        'home': {
            'C003_20090708.csv': (3600.82, 4495.71),
            'C003_20090803.csv': (3598.44, 4493.69),
            'C003_20090824.csv': (3602.95, 4499.33),
            'C004_20090801.csv': (3599.73, 4491.47),
            'C004_20090910.csv': (3603.85, 4515.31),
            'C004_20090914.csv': (3602.07, 4504.48),
            'C005_20090825.csv': (3609.17, 4499.52),
            'C005_20090826.csv': (3599.52, 4458.92),
            'C005_20090902.csv': (3671.34, 4495.31),
            'C006_20090830.csv': (3626.84, 4465.09),
            'C006_20091106.csv': (3597.24, 4499.96),
            'C007_20090903.csv': (3604.35, 4499.34),
            'C007_20090908.csv': (3599.86, 4496.59),
            'C007_20090913.csv': (3600.48, 4497.35),
            'C023_20100823.csv': (29835.05, 30497.47),
            'C023_20100904.csv': (3600.18, 4495.47),
            'C023_20100927.csv': (3613.03, 4414.20),
            'C031_20110614.csv': (3611.59, 4451.47),
            'C031_20110629.csv': (3607.98, 4495.56),
            'C031_20110713.csv': (3600.91, 4459.90),
            'C036_20111205.csv': (3602.08, 4493.48),
            'C036_20120201.csv': (3604.86, 4501.28),
            'C042_20120514.csv': (3598.29, 4417.48),
            'C042_20120516.csv': (3602.31, 4491.58),
            'C042_20120523.csv': (3601.40, 4508.21),
            'C043_20120531.csv': (3608.95, 4394.35),
            'C043_20120607.csv': (3599.68, 4408.05),
            'C043_20120622.csv': (3609.30, 4435.89),
            'C043_20120629.csv': (3599.17, 4440.87),
            'C056_20121127.csv': (3599.72, 4499.66),
            'C056_20121218.csv': (3601.78, 4500.54),
            'C085_20130314.csv': (3657.72, 4467.42),
            'C085_20130315.csv': (3604.72, 4486.07),
        },
        
        'home daycare': {
            'C026_20101025.csv': (3599.43, 4481.55),
            'C026_20101110.csv': (3599.88, 4499.61),
            'C026_20101122.csv': (3604.18, 4494.64),
            'C033_20110816.csv': (3600.26, 4502.10),
            'C033_20110817.csv': (3600.35, 4494.58),
            'C033_20110818.csv': (3627.62, 4500.57),
            'C033_20110830.csv': (3599.84, 4480.82),
            'C034_20110906.csv': (3606.76, 4479.75),
            'C034_20110909.csv': (3600.69, 4510.01),
            'C034_20110912-1.csv': (3616.27, 4500.02),
            'C034_20110912-2.csv': (3606.65, 4499.56),
            'C038_20120502.csv': (3592.41, 4497.81),
            'C038_20120504.csv': (3611.38, 4499.18),
            'C038_20120509.csv': (3597.15, 4305.68),
            'C041_20120503.csv': (3598.63, 4428.87),
            'C041_20120514.csv': (3599.46, 4253.47),
            'C041_20120529.csv': (3599.92, 4500.71),
            'C044_20120613.csv': (4084.26, 4491.75),
            'C044_20120619.csv': (3599.40, 4493.42),
            'C055_20121026.csv': (3600.11, 4461.09),
            'C055_20121119.csv': (3599.45, 4500.57),
        },

        'daycare centre': {
            'C001a_20090615.csv': (3600.63, 4499.31),
            'C001a_20090630.csv': (3618.35, 4493.90),
            'C001a_20090707.csv': (3547.13, 4514.40),
            'C001b_20090811.csv': (3598.06, 4487.87),
            'C001b_20090831.csv': (3583.69, 4512.63),
            'C001b_20090901.csv': (3539.29, 4511.45),
            'C002_20090619.csv': (3598.60, 4501.71),
            'C002_20090622.csv': (3600.79, 4500.89),
            'C002_20090625.csv': (3599.79, 4500.50),
            'C021_20100617.csv': (3604.85, 4498.43),
            'C021_20100623.csv': (3600.15, 4509.76),
            'C021_20100624.csv': (3684.64, 4499.27),
            'C022_20100722.csv': (3597.75, 4501.04),
            'C022_20100728.csv': (3605.03, 4490.78),
            'C022_20100805.csv': (3596.37, 4494.05),
            'C024_20100827.csv': (3596.99, 4494.64),
            'C024_20100903.csv': (3611.24, 4496.10),
            'C024_20100913.csv': (3599.52, 4499.21),
            'C035_20111025.csv': (3598.42, 4500.43),
            'C035_20111103.csv': (3599.59, 4497.04),
            'C035_20111116.csv': (3599.42, 4501.50),
            'C035_20111118.csv': (3601.00, 4500.14),
            'C035_20111122.csv': (3611.32, 4500.66),
            'C045_20120621.csv': (3601.46, 4496.89),
            'C045_20120628.csv': (3630.51, 4496.44),
            'C045_20120712.csv': (3609.20, 4501.09),
            'C049_20120821.csv': (3605.41, 4460.19),
            'C049_20120823.csv': (3599.52, 4347.23),
            'C051_20120823.csv': (3600.54, 4447.20),
            'C051_20120904.csv': (3598.63, 4475.49),
            'C051_20120914.csv': (3599.90, 4454.19),
            'C051_20120921.csv': (3598.60, 4364.91),
            'C053_20121012.csv': (3599.12, 4464.36),
            'C054_20121017.csv': (3599.56, 4493.49),
            'C054_20121108.csv': (3598.38, 4494.12),
            'C115_20131024.csv': (3598.01, 4500.48),
        }
        }

    file_out = open('C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/lena_awc.csv', 'wb')
    writer = csv.writer(file_out)
    writer.writerow(['Child Code', 'Words', 'Segments', 'Mean'])
    
    for cur_env in envs:
        db = Database('C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/%s.db' % (cur_env))
        print cur_env

        for filename in boundaries[cur_env]:
            print filename
            start, end = boundaries[cur_env][filename]
            rowcount = db.delete(
                'data',
                where_cond='col46 = ? and (col30 < ? or col30 + col38 > ? or (col14 = 0 and col17 = 0))',
                params=[filename, start, end]
            )
            print rowcount

        print ''
        rows = db.select(
            'data',
            ['distinct col4']
        )
        for cur_row in rows:
            child_cd = cur_row[0]
            print child_cd
            
            rows = db.select(
                'data',
                ['sum(col7)', 'count(id)', 'avg(col7)'],
                where_cond='col4 = ?',
                params=[child_cd]
            )

            sum_val, count_val, avg_val = rows[0]
            writer.writerow([child_cd, sum_val, count_val, avg_val])

        print ''
        
        db.close()
    file_out.close()

def run():
    get_data()
    
    # for cur_env in envs:
    #     files = glob.glob('G:/confusion/ADEX/%s/*.csv' % (cur_env))
    #     time_fix(files)

    # for cur_env in envs:
    #     files = glob.glob('G:/confusion/ADEX/%s/*-fixed.csv' % (cur_env))
    #     db = CSVDatabase.create_with_files(files, col_datatypes)
    #     db.cursor.execute('create index time_index on data (col46, col45);')
    #     db.dump_to_file('C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/%s.db' % (cur_env))
    #     db.close()