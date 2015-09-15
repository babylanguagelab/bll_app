import csv
import glob

path = 'C:/Users/Wayne/Documents/baby-lab/bll/dana/dest/'

dirs = (
    'DaycareCentre/',
    'DaycareHome/',
    #'Home/',
)

def main():
    for cur_dir in dirs:
        filenames = glob.glob('%s%s*_done.csv' % (path, cur_dir))

        for cur_file in filenames:
            file_in = open(cur_file, 'rb')
            reader = csv.reader(file_in)
            rows = list(reader)
            file_in.close()

            rows[0][4] = 'Date'

            file_out = open(cur_file, 'wb')
            writer = csv.writer(file_out)
            for cur_row in rows:
                writer.writerow(cur_row)
            file_out.close()

main()
