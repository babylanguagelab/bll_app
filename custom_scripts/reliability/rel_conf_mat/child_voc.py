from parsers.trs_parser import TRSParser
from custom_scripts.reliability.rel_conf_mat.rel_utils import *
from db.database import Database
from parsers.filter_manager import FilterManager
import os
import glob
import csv

input_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/input/'
output_file = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/Child_Voc.csv'
envs = (
    'home',
    'home daycare',
    'daycare centre',
)
#envs = ('test',)

lena_db_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/'

def get_lena_child_vocs(lena_db, filename, start, end):
    filename = os.path.basename(filename)[:-10] + '.csv'
    
    row = lena_db.select(
        'data',
        ['sum(col9)'],
        where_cond='col46 = ? and col45 >= ? and col45 + col38 <= ?',
        params=[filename, start, end]
    )

    vocs = 0
    if row:
        vocs = row[0][0]
        
    return vocs

def get_trans_child_vocs(segs):
    chains = FilterManager.get_chains(segs)
    count = 0
    for head in chains:
        if head.trans_codes and head.trans_codes[0] == 'T':
            count += 1

    return count
    
def process_dir(path, env, par_code, writer):
    trs_filenames = glob.glob('%s*.trs' % (path))

    trans_count = 0
    lena_count = 0

    lena_db = Database('%s%s.db' % (lena_db_path, env))

    for filename in trs_filenames:
        print '\n\tProcessing file %s' % (os.path.basename(filename))

        parser = TRSParser(filename)
        segs = get_trans_segs( parser.parse() )

        if segs:
            zone_start = segs[0].start
            zone_end = segs[-1].end
            print '\tExamining range: %s (%0.2f) - %s (%0.2f)' % (get_time_str(zone_start), zone_start, get_time_str(zone_end), zone_end)

            trans_count += get_trans_child_vocs(segs)
            lena_count += get_lena_child_vocs(lena_db, filename, zone_start, zone_end)

    lena_db.close()
    
    writer.writerow([
        par_code,
        trans_count,
        lena_count
    ])

def setup_output_file():
    out_file = open(output_file, 'wb')
    writer = csv.writer(out_file)
    writer.writerow(['Participant', 'Transcriber Child Voc Count', 'LENA Child Voc Count'])
    
    return writer, out_file
    
def run():
    writer, out_file = setup_output_file()
    
    for i in range(len(envs)):
        cur_env = envs[i]
        print 'Processing environment: %s' % (cur_env)

        writer.writerow(['%s:' % (cur_env.capitalize())])
        
        input_dir = '%s%s/' % (input_path, cur_env)
        dir_contents = os.listdir(input_dir)

        for item in dir_contents:
            full_item_path = '%s%s/' % (input_dir, item)

            if os.path.isdir(full_item_path):
                process_dir(full_item_path, cur_env, item, writer)

        if i < len(envs) - 1:
            writer.writerow([''])

    out_file.close()

    
