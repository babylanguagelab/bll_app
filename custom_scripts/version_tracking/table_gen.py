import glob
import csv
import os
import sys
import datetime

envs = {
        'C003': 'Home',
        'C004': 'Home',
        'C005': 'Home',
        'C006': 'Home',
        'C007': 'Home',
        'C023': 'Home',
        'C031': 'Home',
        'C036': 'Home',
        'C042': 'Home',
        'C043': 'Home',
        'C056': 'Home',
        'C057': 'Home',
        'C074': 'Home',
        'C085': 'Home',
        'C113': 'Home',
        'C116': 'Home',

        'C026': 'DaycareHome',
        'C033': 'DaycareHome',
        'C034': 'DaycareHome',
        'C038': 'DaycareHome',
        'C041': 'DaycareHome',
        'C044': 'DaycareHome',
        'C055': 'DaycareHome',
        'C117': 'DaycareHome',

        'C001A': 'DaycareCentre',
        'C001B': 'DaycareCentre',
        'C002': 'DaycareCentre',
        'C021': 'DaycareCentre',
        'C022': 'DaycareCentre',
        'C024': 'DaycareCentre',
        'C035': 'DaycareCentre',
        'C045': 'DaycareCentre',
        'C046': 'DaycareCentre',
        'C048': 'DaycareCentre',
        'C049': 'DaycareCentre',
        'C051': 'DaycareCentre',
        'C053': 'DaycareCentre',
        'C054': 'DaycareCentre',
        'C115': 'DaycareCentre',
        }

def get_lena_version(its_filename):
    return '0'

def get_file_dates(filename):
    c_time = os.path.getctime(filename) #this is creation time on windows systems, but date of last change on unix systems
    m_time = os.path.getmtime(filename)

    c_date = datetime.datetime.fromtimestamp(c_time)
    m_date = datetime.datetime.fromtimestamp(m_time)

    return c_date, m_date

def write_its_table(its_folder):
    its_table_cols = (
        'ITS Filename',
        'LENA Version Tag',
        'Created',
        'Last Modified',
        )
    writer = csv.DictWriter(sys.stdout, its_table_cols, delimiter='\t')
    writer.writeheader()

    its_filenames = glob.glob('%s*.its' % (its_folder))
    for i in range(len(its_filenames)):
        c_date, m_date = get_file_dates(its_filenames[i])

        row = dict(zip(its_table_cols,
            (its_filenames[i],
             get_lena_version(its_filenames[i]),
             c_date.strftime('%b %d %Y %H:%M'),
             m_date.strftime('%b %d %Y %H:%M'),
             )))

        writer.writerow(row)

def get_its_ver_dict(its_folder):
    ver_dict = {}

    its_filenames = glob.glob('%s*.its' % (its_folder))

    for i in range(len(its_filenames)):
        c_date, m_date = get_file_dates(its_filenames[i])
        ver = get_lena_version(its_filenames[i])
        if ver in ver_dict:
            ver_dict[ver].append(m_date)
        else:
            ver_dict[ver] = [m_date]

    for ver in ver_dict:
        ver_dict[ver] = min(ver_dict[ver]), max(ver_dict[ver])

    return ver_dict

def write_trs_table(trs_folder, ver_dict):
    trs_filenames = glob.glob('%s*.trs' % (trs_folder))

    trs_table_cols = (
        'TRS Filename',
        'Created',
        'Last Modified',
        'LENA Version (from mod times)',
        'Environment',
        )
    writer = csv.DictWriter(sys.stdout, trs_table_cols, delimiter='\t')
    writer.writeheader()
    for i in range(len(trs_filenames)):
        c_date, m_date = get_file_dates(its_filenames[i])

        lena_version = ''
        ver_list = ver_dict.keys()
        while i < len(ver_list) and not lena_version:
            start, end = ver_dict[ver_list[i]]
            if m_date >= start and m_date <= end:
                lena_version = ver_list[i]
            i += 1

        child_cd = trs_filenames[i].split('_')[0].upper()
        file_env = envs[child_cd] if child_cd in envs else '?'
        
        row = dict(zip(trs_table_cols,
                       (trs_filenames[i],
                        c_date.strftime('%b %d %Y %H:%M'),
                        m_date.strftime('%b %d %Y %H:%M'),
                        lena_version,
                        file_env,
                       )))

        writer.writerow(row)

def write_total_time_table(trs_folder):
    trs_filenames = glob.glob('%s*.trs' % (trs_folder))

    trs_table_cols = (
        'DaycareCentre',
        'DaycareHome',
        'Home',        
        )

    env_sums = {
        'DaycareCentre': 0,
        'DaycareHome': 0,
        'Home': 0,
        }
    
    writer = csv.DictWriter(sys.stdout, trs_table_cols, delimiter='\t')
    writer.writeheader()
    for i in range(len(trs_filenames)):
        child_cd = os.path.basename(trs_filenames).split('_')[0].upper() #eg. C001

        if child_cd in envs:
            parser = TRSParser(trs_filenames[i])
            segs = parser.parse(validate=False)
            file_env = envs[child_cd]
            env_sums[file_env] += (segs[-1].end - segs[0].start)

        else:
            sys.stderr.write('Child code not in lookup: %s\n' % (child_cd))

    row = dict(zip(trs_table_cols,
                   map(lambda col: '%0.2f' % (env_sums[col]), trs_table_cols)
            ))
    
    writer.writerow(row)

def run():
    its_folder = 'C:/Experimental Data/Daycare Study/its/'
    trs_folder = 'F:/Transcriber Files/Transcriber Files/Original Files/'

    write_its_table(its_folder)
    sys.stdout.write('\n')
    
    ver_dict = get_its_ver_dict(its_folder)
    write_trs_table(trs_folder, ver_dict)
    sys.stdout.write('\n')
    
    write_total_time_table(trs_folder)
    sys.stdout.write('\n')
