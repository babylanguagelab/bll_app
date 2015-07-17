import logging
import os
import csv
import glob
import numpy
from datetime import datetime
from db.database import Database
from parsers.trs_parser import TRSParser
from parsers.its_parser import ITSParser

#this file contains rows for all children
#taken from 'C:/Experimental Data/Daycare Study/Kelsey Thesis/'
activities_filename = 'C:/Users/Wayne/Documents/baby-lab/bll/dana/activities/all_activities.csv'

#this folder contains one folder for each child
#taken from 'C:/Experimental Data/Daycare Study/ADEX Output/Maddy/'
naptime_folders = (#'C:/Experimental Data/Daycare Study/ADEX Output/Jamie/naptime data/Daycare Centre Data/',
                   #'C:/Experimental Data/Daycare Study/ADEX Output/Jamie/naptime data/Home Daycare Data/',
                   'C:/Experimental Data/Daycare Study/ADEX Output/Jamie/naptime data/Home Data/',
                   )

#this folder contains one file for each child
#taken from 'C:/Experimental Data/Daycare Study/ADEX Output/Praat Interface - Dana/'
src_folders = (#'C:/Experimental Data/Wayne/src/DaycareCentre/',
               #'C:/Experimental Data/Wayne/src/DaycareHome/',
               'C:/Users/Wayne/Documents/baby-lab/bll/dana/src/Home/trimmed/',
               )
#src_folders = ('C:/Experimental Data/Wayne/TempIn/',)

#each child will create 2 output files. (1 - stats like min, max, mean, Q1, Q3, etc. and 2 - desired combined output data like speaker, start, elapsed time, date, activity, naptime)
dest_folders = (#'C:/Experimental Data/Wayne/dest/DaycareCentre/',
                #'C:/Experimental Data/Wayne/dest/DaycareHome/',
                'C:/Users/Wayne/Documents/baby-lab/bll/dana/dest/Home/',
                )
#dest_folders = ('C:/Experimental Data/Wayne/TempOut/',)

dest_cols = 'Start Duration Speaker Activity Date Elapsed_Time Average_SignalLevel Peak_SignalLevel'.split()
stats_cols = 'Speaker Min Max Q1 Mean(Q2) Q3'.split()

speaker_cats = {
    #near
    'CHN': ('CHN',),
    'ADN': ('FAN', 'MAN',),
    'CXN': ('CXN',),
    'OLN': ('OLN',),
    'NVN': ('TVN', 'NON',),
    
    #distance n/a
    'SIL': ('SIL',),
    'FUZ': ('FUZ',),
    
    #far
    'CHF': ('CHF',),
    'ADF': ('FAF', 'MAF',),
    'CXF': ('CXF',),
    'OLF': ('OLF',),
    'NVF': ('TVF', 'NOF',),
    }

def create_db(filename):
    print 'Creating in-memory database...'
    
    #db = Database(':memory:')
    db = Database(filename)

    db.execute_stmt('''
create table activities (
id integer primary key autoincrement,
child_cd text not null,
activity text null,
start real not null,
end real not null
);
''')
    
    db.execute_stmt('''
create index child_index on activities (
child_cd,
start,
end
);
''')

    db.execute_stmt('''
create table trs_segs (
id integer primary key autoincrement,
file_cd text not null,
start real not null,
end real not null,
speaker text not null
);
''')

    db.execute_stmt('''
create index trs_seg_index on trs_segs (
file_cd,
start,
end
);
''')

    print 'done.\n'

    return db

def populate_activities(db):
    print 'Populating db using activities file...'
    
    acts_file = open(activities_filename, 'rb')
    reader = csv.DictReader(acts_file)
    rows = list(reader)

    last_child = '%s_%d%02d%02d' % (rows[0]['child_id'].upper(), int(rows[0]['year']), int(rows[0]['month']), int(rows[0]['day']))
    accum_time = float(rows[0]['Elapsed_Time']) #elapsed time will restart periodically, so we need to keep a time accumulator var
    last_act = rows[0]['Activity']
    last_act_start = accum_time
    last_act_end = None
    last_dur = float(rows[0]['Interval_Duration'])
    
    for i in range(1, len(rows)):
        cur_child = '%s_%d%02d%02d' % (rows[i]['child_id'].upper(), int(rows[i]['year']), int(rows[i]['month']), int(rows[i]['day']))
        cur_act = rows[i]['Activity']
        cur_dur = float(rows[i]['Interval_Duration'])
        cur_el_time = float(rows[i]['Elapsed_Time'])

        if cur_act != last_act or cur_child != last_child or i == len(rows) - 1:
            last_act_end = accum_time + last_dur

            #insert
            db.insert('activities',
                  'child_cd activity start end'.split(),
                  ((last_child,
                    last_act,
                    last_act_start,
                    last_act_end,
                    ),),
                  )

            #reset vars for next iteration (set last vars to cur values)
            if cur_child != last_child:
                last_act_start = cur_el_time
                accum_time = cur_el_time
                #last_dur = 0
                last_dur = cur_dur
            else:
                last_act_start = accum_time + last_dur
                accum_time += cur_dur
                last_dur = cur_dur
                
            last_act = cur_act
            last_child = cur_child
            
        else:
            accum_time += cur_dur

    acts_file.close()
    print 'done.\n'

def populate_naptime(db, naptime_folder):
    print 'Populating db using naptime files...'

    #note: Windows filesnames are case-insensitive
    naptime_filenames = glob.glob('%s*COMPLETE.csv' % (naptime_folder))

    for i in range(len(naptime_filenames)):
        nap_file = open(naptime_filenames[i], 'rb')
        print 'Reading naptime file "%s"' % (naptime_filenames[i])

        reader = csv.DictReader(nap_file)
        rows = list(reader)

        month, day, year = rows[0]['Clock_Time_TZAdj'].split(' ')[0].split('/')
        if len(year) == 2:
            year = '20%s' % (year)
        child_id = rows[0]['File_Name'].split('_')[0].upper()
        child_cd = '%s_%d%02d%02d' % (child_id, int(year), int(month), int(day))

        #remove all existing naptime db rows for this child (these came from the activities file), and use the naptime file info instead (more accurate)
        db.delete(
            'activities',
            where_cond='child_cd = ? and activity = ?',
            params=((child_cd, 'naptime')),
            )

        dur_cols = ['Segment_Duration', 'Audio_Duration', 'Block_Duration']
        i = 0
        while dur_cols[i] not in rows[0] and i < len(dur_cols):
            i += 1

        dur_col_title = None
        if i < len(dur_cols):
            dur_col_title = dur_cols[i]
            print 'Using dur_col_title="%s"' % (dur_col_title)
        else:
            raise Exception('Raising a fuss because there\'s no Segment_Duration or Audio_Duration column in this file.')
            
            #print 'Warning: no "Segment_Duration" col found. Using "Block_Duration" instead.'    
        
        last_is_naptime = bool(rows[0]['Naptime'].strip().lower() == 'naptime') #naptime col is blank if seg is not naptime
        accum_time = float(rows[0]['Elapsed_Time']) + float(rows[0][dur_col_title]) #elapsed time will restart periodically, so we need to keep a time accumulator var
        #nap_start = accum_time if last_is_naptime else None
        nap_start = float(rows[0]['Elapsed_Time']) if last_is_naptime else None
        if nap_start is not None:
            print 'nap_start: %f' % (nap_start)
        nap_end = None

        for j in range(1, len(rows)):
            cur_is_naptime = bool(rows[j]['Naptime'].strip().lower() == 'naptime') #naptime col is blank if seg is not naptime
            cur_dur = float(rows[j][dur_col_title])

            if cur_is_naptime and not last_is_naptime:
                nap_start = accum_time
                print 'nap_start: %f' % (nap_start)
                
            elif not cur_is_naptime and last_is_naptime:
                nap_end = accum_time
                print 'nap_end: %f' % (nap_end)

                resolve_naptime_insert(
                    db,
                    child_cd,
                    nap_start,
                    nap_end,
                    )

            #last row
            if cur_is_naptime and j == len(rows) - 1:
                nap_end = accum_time + cur_dur
                print 'nap_end: %f' % (nap_end)

                resolve_naptime_insert(
                    db,
                    child_cd,
                    nap_start,
                    nap_end
                    )

            accum_time += cur_dur
            last_is_naptime = cur_is_naptime
            
        nap_file.close()
        smooth_db(db, child_cd)
    
    print 'done.\n'

#Insert a naptime segment (from a naptime-file) into the db, adjusting overlapping segments accordingly.
def resolve_naptime_insert(db, child_cd, nap_start, nap_end):
    intersect_rows = db.select(
        'activities',
        'id start end'.split(),
        where_cond='child_cd = ? and ' +
        '((end >= ? and end <= ?) or ' + #db end pt intersects range, or db start pt and db end pt both intersect range
        '(start <= ? and start >= ?) or ' + #db start pt inersects range, or db start pt and db end pt both intersect range
        '(start < ? and end > ?))', #some db middle pts intersects range
        params=(child_cd,
                nap_start, nap_end,
                nap_end, nap_start,
                nap_start, nap_end,
                ),
        order_by='id ASC'
        )

    if len(intersect_rows) == 0:
        #insert
        db.insert(
            'activities',
            'child_cd activity start end'.split(),
            ((child_cd,
              'naptime',
              nap_start,
              nap_end,
                    ),),
            )

    i = 0
    while i < len(intersect_rows):
        db_id, db_start, db_end = intersect_rows[i]

        if db_end >= nap_start and db_end <= nap_end: #db end pt intersects range, or db start pt and db end pt both intersect range
            if db_start >= nap_start: #db start pt and db end pt both intersect range
                db.delete(
                    'activities',
                    where_cond='id = ?',
                    params=(db_id,),
                    )
            else: #only db end pt intersects range (db start pt is before nap_start)
                db.update(
                    'activities',
                    ('end',),
                    where_cond='id = ?',
                    params=(nap_start, db_id,),
                    )

        elif db_start <= nap_end and db_start >= nap_start: #db start pt inersects range, or db start pt and db end pt both intersect range
            if db_end <= nap_end: #db start pt and db end pt both intersect range
                db.delete(
                    'activities',
                    where_cond='id = ?',
                    params=(db_id,),
                    )
            else: #only db start pt intersects range (db end point is after nap_end)
                db.update(
                    'activities',
                    ('start',),
                    where_cond='id = ?',
                    params=(nap_end, db_id,),
                    )

        #make sure we never insert the same segment twice (can happen in we have multiple segs intersecting naptime. i.e. if hand-coded naptime starts before activity naptime)
        cur_naptime_rows = db.select(
            'activities',
            ('count(id)',),
            where_cond="child_cd = ? AND activity = 'naptime' AND start = ? AND end = ?",
            params=(child_cd, nap_start, nap_end,),
            )

        if int(cur_naptime_rows[0][0]) == 0:            
            #insert
            db.insert(
                'activities',
                'child_cd activity start end'.split(),
                ((child_cd,
                  'naptime',
                  nap_start,
                  nap_end,
                        ),),
                )

        i += 1
        
#Fill in any gaps left over from removing the activity-file-naptime-info (after naptime-file-info has been inserted). This is necessary beceause naptime-file-info may not line up exactly with activity-file-naptime-info. This function performs this operation for one child.
def smooth_db(db, child_cd):
    rows = db.select(
        'activities',
        'id start end activity'.split(),
        where_cond='child_cd = ?',
        params=(child_cd,),
        order_by=('start ASC',),
        )

##    if rows:
##        last_id, last_start, last_end = rows[0]
##        for i in range(1, len(rows)):
##            row_id, row_start, row_end = rows[i]
##            if last_end < row_start:
##                db.update(
##                    'activities',
##                    ('end',),
##                    where_cond='id = ?',
##                    params=(row_start, last_id,),
##                    )
##                
##            last_start = row_start
##            last_end = row_end
##            last_id = row_id

    if rows:
        i = 0
        
        while i < len(rows):
            while i < len(rows) and rows[i][3] == 'naptime':
                i += 1
                
            if i < len(rows):
                last_id, last_start, last_end, last_activity = rows[i] #last row is first non-naptime row

                #read next row
                i += 1
                if i < len(rows):
                    row_id, row_start, row_end, row_activity = rows[i]
                    if last_end < row_start: #if last row ends before this one starts, adjust last row's end time
                        db.update(
                            'activities',
                            ('end',),
                            where_cond='id = ?',
                            params=(row_start, last_id,),
                            )
                    
                i += 1

def populate_segs(db, trs_folder):
    print 'Populating db using trs files...'
    
    trs_filenames = glob.glob('%s*.trs' % (trs_folder))
    trs_filenames.extend(glob.glob('%s*.its' % (trs_folder)))
    
    for i in range(len(trs_filenames)):
        print 'File %d of %d' % (i + 1, len(trs_filenames))

        is_trs = trs_filenames[i].endswith('.trs')

        segs = None
        if is_trs:
            trs_parser = TRSParser(trs_filenames[i])
            segs = trs_parser.parse(validate=False)

        else:
            trs_parser = ITSParser(trs_filenames[i])
            segs = trs_parser.parse()

            #<hack for its files>
            utters = []
            for s in segs:
                utters.extend(s.utters)
            segs = utters
            #</hack for its files>
        
        file_cd = os.path.basename(trs_filenames[i][:-4]).upper()

        for cur_seg in segs:
            #commented out for .its hack
            if is_trs:
                is_fuz = False
                j = 0
                while not is_fuz and j < len(cur_seg.speakers):
                    is_fuz = cur_seg.speakers[j].speaker_codeinfo.code == 'FUZ'
                    j += 1

                if is_fuz and len(cur_seg.speakers) > 1:
                    print 'Warning: Found multi-speaker FUZ seg in file: "%s"' % (os.path.basename(trs_filenames[i]))

            db.insert(
                'trs_segs',
                'file_cd start end speaker'.split(),
                ((file_cd,
                  cur_seg.start,
                  cur_seg.end,
                  #commented out for its hack
                  cur_seg.speakers[0].speaker_codeinfo.code if is_trs else cur_seg.speaker.speaker_codeinfo.code
                  ),)
                )
            
    print 'done.\n'

def find_real_fuz_speaker(db, src_filename, accum_start, accum_end):
    file_cd = os.path.basename(src_filename[:-4]).upper()
    intersect_rows = db.select(
        'trs_segs',
        'start end speaker'.split(),
        where_cond='file_cd = ? and ' +
        '((end >= ? and end <= ?) or ' + #db end pt intersects range, or db start pt and db end pt both intersect range
        '(start <= ? and start >= ?) or ' + #db start pt inersects range, or db start pt and db end pt both intersect range
        '(start < ? and end > ?))', #some db middle pts intersects range
        params=(file_cd,
                accum_start, accum_end,
                accum_end, accum_start,
                accum_start, accum_end,
                ),
        order_by='id ASC'
        )

    #find segment with largest amount of overlap, and grab its speaker
    real_speaker = 'FUZ'
    largest_mag = 0
    for db_row in intersect_rows:
        db_start, db_end, db_speaker = db_row
        mag = 0
        #db end pt intersects range, or db start pt and db end pt both intersect range
        if db_end >= accum_start and db_end <= accum_end:
            mag = db_end - max(accum_start, db_start)

        #db start pt inersects range, or db start pt and db end pt both intersect range
        elif db_start <= accum_end and db_start >= accum_start:
            mag = min(accum_end, db_end) - db_start

        #some db middle pts intersects range (db_row completely covers file_row)
        else: #if db_start < accum_start and db_end > accum_end:
            mag = accum_end - accum_start

        #update if mag is equal to largest mag, since we want to prefer trs speaker over csv speaker (FUZ)
        if mag >= largest_mag and db_speaker.endswith('F'): #make sure we got far speaker
            largest_mag = mag
            real_speaker = db_speaker

    #translate to combined speaker code
    if real_speaker != 'FUZ':
        i = 0
        combined_cats = speaker_cats.keys()
        found = False
        while not found and i < len(combined_cats):
            found = real_speaker in speaker_cats[combined_cats[i]]
            if found:
                real_speaker = combined_cats[i]
            i += 1

    return real_speaker

def process_src_file(db, src_file, dest_file, stats_file):
    src_reader = csv.DictReader(src_file)
    dest_writer = csv.writer(dest_file)
    stats_writer = csv.writer(stats_file)

    #write "done" file
    stats_durs = {} #dict keyed by cat (speaker), with values that are lists of all the durations from rows with that speaker
    for cat in speaker_cats:
        stats_durs[cat] = []

    dest_writer.writerow(dest_cols)
    rows = list(src_reader)
    accum_start = float(rows[0]['Elapsed_Time'])
    accum_end = None
    for i in range(len(rows)):
        month, day, year = rows[i]['Clock_Time_TZAdj'].split(' ')[0].split('/')
        if len(year) == 2:
            year = '20%s' % (year)
        child_id = rows[i]['File_Name'].split('_')[0].upper()
        child_cd = '%s_%d%02d%02d' % (child_id, int(year), int(month), int(day))

        #signal levels
        row_avg_sig_lev = rows[i]['Average_SignalLevel']
        row_peak_sig_lev = rows[i]['Peak_SignalLevel']
        
        #speaker and duration
        row_speaker = ''
        row_dur = 0
        for cat in speaker_cats:
            cat_dur = reduce(
                lambda accum, key: accum + (float(rows[i][key]) if key in rows[i] else 0), #far speakers are not listed in csv cols - they are combined into FUZ
                speaker_cats[cat],
                0
                )
            if cat_dur > 0:
                row_dur = cat_dur
                row_speaker = cat

        accum_end = accum_start + row_dur

        #FUZ rows in csv files are actually far speakers - the far speakers are given in the trs file
        if row_speaker == 'FUZ':
            row_speaker = find_real_fuz_speaker(db, src_file.name, accum_start, accum_end)

        #date (input is m/d/yy, output will be dd-mon-yy)
        row_date_str = None
        try:
            date = datetime.strptime(rows[i]['Clock_Time_TZAdj'], '%m/%d/%y %H:%M')
            row_date_str = date.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError: #hack for dealing with seconds and other year format(present in only some files)
            date = datetime.strptime(rows[i]['Clock_Time_TZAdj'], '%m/%d/%Y %H:%M:%S')
            row_date_str = date.strftime('%Y-%m-%d %H:%M:%S')
        
        #activity
        results = db.select(
                    'activities',
                    'start end activity'.split(),
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
        row_activity = ''
        #note: results are ordered by id (order of insertion) ascending, so the looping here will ensure that in the case of two activities that equally overlapping the segment, the last one (i.e. the one from the naptime file, if present) will be used.
        for db_row in results:
            db_start, db_end, db_activity = db_row
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

            #update if mag is equal to largest mag, since we want to prefer later overlapping activities from the naptime file (if present) - see comment above the loop
            if mag >= largest_mag:
                largest_mag = mag
                row_activity = db_activity

        row_el_time = float(rows[i]['Elapsed_Time'])
        if 'naptime' not in row_activity:
            stats_durs[row_speaker].append(row_dur)
                
        out_row = (
            str(accum_start),
            str(row_dur),
            str(row_speaker),
            str(row_activity),
            str(row_date_str),
            str(row_el_time),
            str(row_avg_sig_lev),
            str(row_peak_sig_lev),
            )
        dest_writer.writerow(out_row)

        accum_start += row_dur

    #write stats file
    #stats_title_row = ['Durations (from non-naptime rows):']
    #for i in range(len(stats_cols) - 1): 
    #    stats_title_row.append('')
        
    #stats_writer.writerow(stats_title_row)
    stats_writer.writerow(stats_cols)
    
    stats_rows = calc_file_stats(stats_durs)
    for row in stats_rows:
        stats_writer.writerow(row)

def calc_file_stats(stat_durs):
    stats = []
    
    speakers = speaker_cats.keys()
    speakers.sort()
    for cd in speakers:
        data = stat_durs[cd]
        n = len(data)

        if len(stat_durs[cd]) > 0:
            q1 = numpy.percentile(data, 25)
            q3 = numpy.percentile(data, 75)

            #this will loop through all data every time, but we're not too concerned about efficiency here,
            #since n will be small...
            min_val = min(data)
            max_val = max(data)
            mean_val = numpy.average(data)

            stats.append((cd, min_val, max_val, mean_val, q1, q3))
        else:
            stats.append((cd, 'No non-naptime rows found.', '', '', '', ''))
        
    return stats

def check_log_file(path):
    if not os.path.exists(path):
        logfile = open(path, 'w')
        logfile.close()

def textify_csv_files():
    for i in range(len(dest_folders)):
        csv_filenames = glob.glob('%s*.csv' % (dest_folders[i]))

        for j in range(len(csv_filenames)):
            csv_filenames[j] = csv_filenames[j].replace('\\', '/')
            csv_file = open(csv_filenames[j], 'rb')
            reader = csv.reader(csv_file)
            
            txt_filename = '%stxt' % (csv_filenames[j][:-3])
            txt_file = open(txt_filename, 'wb')
            writer = csv.writer(txt_file, delimiter='\t')

            for line in reader:
                writer.writerow(line)
            
            txt_file.close()
            csv_file.close()

def run():
    for i in range(len(src_folders)):
        print 'Processing folder "%s/" (%d of %d)...' % (src_folders[i].split('/')[-2], i + 1, len(src_folders))
        
        db = create_db(':memory:')
        populate_activities(db)
        populate_naptime(db, naptime_folders[i])
        populate_segs(db, src_folders[i])

        # db2_name = ('%s-db.db' % (src_folders[i].split('/')[-2])).replace(' ', '-')
        # db2 = create_db(db2_name)
        # db2.close()

        # db.execute_stmt("attach 'C:/Program Files (x86)/bll_app/%s' as hard_file;" % (db2_name));
        # db.execute_stmt('insert into hard_file.activities (child_cd, activity, start, end) select child_cd, activity, start, end from activities;')
        # db.execute_stmt('insert into hard_file.trs_segs (file_cd, start, end, speaker) select file_cd, start, end, speaker from trs_segs;')

        print 'Examining input files...'
        src_filenames = glob.glob('%s*.csv' % (src_folders[i]))
        for j in range(len(src_filenames)):
            print 'Processing file "%s" (%d of %d)...' % (os.path.basename(src_filenames[j]), j + 1, len(src_filenames))
            
            src_file = open(src_filenames[j], 'rb')
            trs_filename = '%strs' % (src_filenames[j][:-3])
            dest_file = open('%s%s_done.csv' % (dest_folders[i], os.path.basename(src_filenames[j][:-4])), 'wb')
            stats_file = open('%s%s_stats.csv' % (dest_folders[i], os.path.basename(src_filenames[j][:-4])), 'wb')
            
            process_src_file(db, src_file, dest_file, stats_file)

            src_file.close()
            dest_file.close()
            stats_file.close()

            print 'done.\n'

        db.close()
        print 'done folder.\n'

    print 'Textifying csv files in dest folder...'
    textify_csv_files()
    print 'done.'
        
    print 'Script complete!'
