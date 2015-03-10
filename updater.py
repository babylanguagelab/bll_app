import os
import shutil

#no trailing slashes!
src_dir = 'C:/Users/Wayne/Documents/baby-lab/bll_app'
dest_dir = 'F:/baby-lab/bll_app'

#these are relative to the base dir
omit_dirs = ['icons', 'logs']
omit_files = ['bll_db.db']

def process_dir(src_dir, dest_dir):
    src_list = os.listdir(src_dir)
    dest_list = os.listdir(dest_dir)

    #remove files/folders that are in dest_dir, but not in src_dir
    for item in dest_list:
        if not item in src_list:
            if os.path.isdir(dest_dir + '/' + item):
                if not item in omit_dirs:
                    print 'Removing directory: %s' % (dest_dir + '/' + item)
                    shutil.rmtree(dest_dir + '/' + item)
            
            elif not item in omit_files:
                print 'Removing file: %s' % (dest_dir + '/' + item)
                os.remove(dest_dir + '/' + item)

    #add or overwrite files/folders in dest_dir using those in src_dir
    for item in src_list:
        if os.path.isdir(src_dir + '/' + item):
            if not item in omit_dirs:
                if not item in dest_list:
                    print 'Creating directory: %s' % (src_dir + '/' + item)
                    os.mkdir(dest_dir + '/' + item)
            
                process_dir(src_dir + '/' + item, dest_dir + '/' + item)

        elif not item in omit_files:
            if not item.endswith('~') and not item.endswith('.pyc'):
                print 'Copying file: %s' % (src_dir + '/' + item)
                shutil.copyfile(src_dir + '/' + item, dest_dir + '/' + item)

process_dir(src_dir, dest_dir)
