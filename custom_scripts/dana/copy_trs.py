import shutil
import glob
import os

c_dirs = ('C:/Experimental Data/Wayne/src/DaycareCentre/',
          'C:/Experimental Data/Wayne/src/DaycareHome/',
          'C:/Experimental Data/Wayne/src/Home/',
          )
f_dir = 'F:/Transcriber Files/Transcriber Files/Original Files/'

for cur_c_dir in c_dirs:
    print 'Processing dir "%s"' % (cur_c_dir)
    csv_filenames = glob.glob(cur_c_dir + '*.csv')
    for cur_filename in csv_filenames:
        trs_filename = f_dir + os.path.basename(cur_filename)[:-3] + 'trs'
        if os.path.exists(trs_filename):
            shutil.copy(trs_filename, cur_c_dir + os.path.basename(cur_filename)[:-3] + 'trs')
        else:
            print 'Missing trs file: "%s"' % (os.path.basename(trs_filename))
    
