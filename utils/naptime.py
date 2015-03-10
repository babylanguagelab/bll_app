import glob
import logging
import os
import csv
import datetime
import traceback
from db.bll_database import DBConstants
from db.bll_database import _get_constants
from utils.ui_utils import UIUtils

class Naptime:
    @staticmethod
    def select_files(db):
        filenames = []
        rows = db.select(
            'naptime_files',
            'id filename'.split()
        )

        for cur_row in rows:
            filenames.append(cur_row[1])

        return filenames

    @staticmethod
    def _update_settings(db, filenames, path):
        path = path.replace('\\', '/')
        
        #update naptime filenames in naptime_files table
        db.delete('naptime_files')
        db.insert(
            'naptime_files',
            ['filename'],
            map(lambda name: [name], filenames)
        )

        #update timestamp and path in naptime table
        db.update_timestamp_col(
            'settings',
            'val',
            where_cond='code_name=?',
            params=['LAST_NAPTIME_UPDATE']
        )

        db.update(
            'settings',
            ['val'],
            where_cond='code_name=?',
            params=[path, 'LAST_NAPTIME_FOLDER']
            )

        #Refresh DBConstants (re-query the DB and rebuild the DBConstants.SETTINGS Enums).
        #This is to force an update the LAST_NAPTIME_FOLDER and LAST_NAPTIME_UPDATE
        #properties of DBConstants.SETTINGS, which have just changed.
        #This is ugly, but it works...
        _get_constants() #this is defined in bll_database.py, and imported at the top of this file

    @staticmethod
    def get_naptime_files(path):
        items = os.listdir(path)
        files = []
        for cur_item in items:
            cur_item = '%s/%s' % (path, cur_item)
            if os.path.isdir(cur_item):
                 files.extend(Naptime.get_naptime_files(cur_item))
            elif cur_item.lower().endswith('complete.csv'):
                files.append(cur_item)

        return files

    @staticmethod
    def update_naptime_data(db, path, prog_diag=None):
        logger = logging.getLogger()
        
        naptime_filenames = Naptime.get_naptime_files(path)
        processed_filenames = []
        error_filenames = []

        #remove all previous naptime zone data
        db.delete('naptime')
            
        for i in range(len(naptime_filenames)):
            try:
                nap_file = open(naptime_filenames[i], 'rb')
                #print 'Reading naptime file "%s"' % (naptime_filenames[i])

                reader = csv.DictReader(nap_file)
                rows = list(reader)

                month, day, year = rows[0]['Clock_Time_TZAdj'].split(' ')[0].split('/')
                if len(year) == 2:
                    year = '20%s' % (year)
                child_id = rows[0]['File_Name'].split('_')[0].upper()
                child_cd = '%s_%d%02d%02d' % (child_id, int(year), int(month), int(day))


                dur_cols = ['Segment_Duration', 'Audio_Duration', 'Block_Duration']
                k = 0
                while dur_cols[k] not in rows[0] and k < len(dur_cols):
                    k += 1

                dur_col_title = None
                if k < len(dur_cols):
                    dur_col_title = dur_cols[k]
                    print 'Using dur_col_title="%s"' % (dur_col_title)
                else:
                    raise Exception('Raising a fuss because there\'s no Segment_Duration or Audio_Duration column in this file.')

                if 'Naptime' not in rows[0]:
                    print 'Can\'t find "Naptime" column!'
                    print rows[0]
                    print rows[0].keys()
                    
                last_is_naptime = bool(rows[0]['Naptime'].strip().lower() == 'naptime') #naptime col is blank if seg is not naptime
                accum_time = float(rows[0]['Elapsed_Time']) + float(rows[0][dur_col_title]) #elapsed time will restart periodically, so we need to keep a time accumulator var
                accum_time = round(accum_time, 2)
                nap_start = accum_time if last_is_naptime else None
                nap_end = None

                for j in range(1, len(rows)):
                    cur_is_naptime = bool(rows[j]['Naptime'].strip().lower() == 'naptime') #naptime col is blank if seg is not naptime
                    cur_dur = float(rows[j][dur_col_title])
                    cur_dur = round(cur_dur, 2)

                    if cur_is_naptime and not last_is_naptime:
                        nap_start = accum_time

                    elif not cur_is_naptime and last_is_naptime:
                        nap_end = accum_time

                        db.insert(
                            'naptime',
                            'child_cd start end'.split(),
                            ((child_cd,
                              round(nap_start, 2),
                              round(nap_end, 2),
                          ),),
                        )

                    #last row
                    if cur_is_naptime and j == len(rows) - 1:
                        nap_end = accum_time + cur_dur

                        db.insert(
                            'naptime',
                            'child_cd start end'.split(),
                            ((child_cd,
                              round(nap_start, 2),
                              round(nap_end, 2),
                          ),),
                        )

                    accum_time += cur_dur
                    last_is_naptime = cur_is_naptime

                nap_file.close()
                processed_filenames.append(naptime_filenames[i])

                if prog_diag:
                    prog_diag.set_fraction(float(i + 1) / float(len(naptime_filenames)))
                
            except Exception as e:
                #logger.error('%s %s' % (naptime_filenames[i], str(e)))
                print 'Error processing %s:' % (naptime_filenames[i])
                print e
                print "Stack trace: %s" % (traceback.format_exc())
                error_filenames.append(naptime_filenames[i])

        Naptime._update_settings(db, processed_filenames, path)
        
        return error_filenames

    @staticmethod
    def filter_file(db, input_path, output_path):
        file_in = open(input_path, 'rb')
        file_out = open(output_path, 'wb')

        src_reader = csv.DictReader(file_in)
        dest_writer = csv.DictWriter(file_out, src_reader.fieldnames)
        dest_writer.writeheader()

        rows = list(src_reader)
        accum_start = float(rows[0]['Elapsed_Time'])
        accum_start = round(accum_start, 2)
        accum_end = None

        month, day, year = rows[0]['Clock_Time_TZAdj'].split(' ')[0].split('/')
        if len(year) == 2:
            year = '20%s' % (year)
            
        child_id = rows[0]['File_Name'].split('_')[0].upper()
        child_cd = '%s_%d%02d%02d' % (child_id, int(year), int(month), int(day))

        dur_col = 'Segment_Duration' if 'Segment_Duration' in rows[0] else 'Audio_Duration'
        
        for i in range(len(rows)):
            seg_dur = float(rows[i][dur_col])
            seg_dur = round(seg_dur, 2)
            accum_end = accum_start + seg_dur

            #check if this seg intersects with any naptime zones
            intersect_rows = db.select(
                'naptime',
                'start end'.split(),
                where_cond='child_cd = ? and ' +
                '((end > ? and end <= ?) or ' + #db end pt intersects range, or db start pt and db end pt both intersect range
                '(start < ? and start >= ?) or ' + #db start pt inersects range, or db start pt and db end pt both intersect range
                '(start < ? and end > ?))', #some db middle pts intersects range
                params=(child_cd,
                        accum_start, accum_end,
                        accum_end, accum_start,
                        accum_start, accum_end,
                    ),
                    order_by='id ASC'
            )

            #determine the magnitude of the overlap (in seconds)
            largest_mag = -1
            #note: results are ordered by id (order of insertion) ascending, so the looping here will ensure that in the case of two naptimes that equally overlap the segment, the last one (i.e. the one from the naptime file, if present) will be used.
            for db_row in intersect_rows:
                db_start, db_end = db_row
                mag = 0
                #db end pt intersects range, or db start pt and db end pt both intersect range
                if db_end > accum_start and db_end <= accum_end:
                    mag = db_end - max(accum_start, db_start)

                    #db start pt inersects range, or db start pt and db end pt both intersect range
                elif db_start < accum_end and db_start >= accum_start:
                    mag = min(accum_end, db_end) - db_start

                    #some db middle pts intersects range (db_row completely covers file_row
                else: #if db_start < accum_start and db_end > accum_end:
                    mag = accum_end - accum_start

                #update if mag is equal to largest mag, since we want to prefer later naptime
                if mag >= largest_mag:
                    largest_mag = mag

            #We exclude if >= 50% of the seg overlaps with a naptime zone.
            #=> We include if the segment does not overlap a naptime zone (largest_mag == -1) or if we have < 50% overlap.
            if round(largest_mag, 2) < round(seg_dur / 2.0, 2): #covers case when largest_mag == -1 (then largest_mag is also < seg_dur / 2.0)
                dest_writer.writerow(rows[i])

            accum_start += seg_dur
        
        file_in.close()
        file_out.close()
