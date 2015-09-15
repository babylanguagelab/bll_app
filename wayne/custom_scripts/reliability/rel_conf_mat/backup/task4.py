import glob
import csv

path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/results/Task4/'
states = ['unlinked', 'linked']
envs = ['daycare centre', 'home', 'home daycare']

def run():
    file_out = open('%slinkage.csv' % (path), 'wb')
    writer = csv.writer(file_out)
    writer.writerow(['Environment', 'UnLinked', 'Linked'])
    
    for cur_env in envs:
        out_row = [cur_env]
        
        for cur_state in states:
            state_count = 0
            filenames = glob.glob('%s%s/%s/*.csv' % (path, cur_state, cur_env))
            
            for cur_file in filenames:
                file_in = open(cur_file, 'rb')
                reader = csv.reader(file_in)
                file_count = int(list(reader)[-3][1])
                state_count += file_count
                file_in.close()
            out_row.append(state_count)
            
        writer.writerow(out_row)
        
    file_out.close()
            
