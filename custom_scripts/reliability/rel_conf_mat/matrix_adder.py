import csv
import os
import re
import glob

LENA_CODE_CATS = 'CHN CXN FAN MAN SIL Far_Speech CRY/VFX OLN OLF Noise CHF CXF FAF MAF TVN TVF NON NOF FUZ'.split()
TRANS_CODES = 'T O F M C U non-speech(>=1sec) non-speech(<1sec) overlap'.split()

input_path = 'C:/Users/Wayne/Documents/baby-lab/bll/reliability/confusion/output/'
envs = (
    'home',
    'home daycare',
    'daycare centre',
)

def build_matrix(row_axis, col_axis):
    matrix = {}

    for i in range(len(col_axis)):
        matrix[col_axis[i]] = {}
        for j in range(len(row_axis)):
            matrix[col_axis[i]][row_axis[j]] = 0

    return matrix
    
def output_matrix(matrix, filename, count_single, count_numbered_multi, count_unnumbered_multi, count_angle_brackets):
    out_file = open(filename, 'wb')
    writer = csv.writer(out_file)

    writer.writerow([''] + LENA_CODE_CATS)

    #output counts
    for trans_code in TRANS_CODES:
        row = [trans_code]

        i = 0
        while i < len(LENA_CODE_CATS):
            count = matrix[ LENA_CODE_CATS[i] ][trans_code]
            cell = '%d' % (count)
            row.append(cell)
            i += 1
                
        writer.writerow(row)

    #blank row
    writer.writerow([''] * len(LENA_CODE_CATS))

    #output percentages - column-wise (each column is one LENA code)
    writer.writerow(['Column-wise Percentages'] + [''] * (len(LENA_CODE_CATS) - 1))    
    writer.writerow([''] + LENA_CODE_CATS)

    col_totals = []
    for lena_code in LENA_CODE_CATS:
        col_totals.append(sum_col(matrix, lena_code))
    
    for trans_code in TRANS_CODES:
        row = [trans_code]

        i = 0
        while i < len(LENA_CODE_CATS):
            count = matrix[ LENA_CODE_CATS[i] ][trans_code]
            ratio = 0
            if col_totals[i] > 0:
                ratio = float(count) / float(col_totals[i]) * 100
            cell = '%0.3f%%' % (ratio)
            row.append(cell)
            i += 1
                
        writer.writerow(row)

    #blank row
    writer.writerow([''] * len(LENA_CODE_CATS))

    #output percentages - row-wise (each row is one transcriber code)
    writer.writerow(['Row-wise Percentages'] + [''] * (len(LENA_CODE_CATS) - 1))    
    writer.writerow([''] + LENA_CODE_CATS)

    for trans_code in TRANS_CODES:
        row = [trans_code]
        row_total = sum_row(matrix, trans_code)

        i = 0
        while i < len(LENA_CODE_CATS):
            count = matrix[ LENA_CODE_CATS[i] ][trans_code]
            ratio = 0
            if row_total > 0:
                ratio = float(count) / float(row_total) * 100
            cell = '%0.3f%%' % (ratio)
            row.append(cell)
            i += 1
                
        writer.writerow(row)

    writer.writerow([''] * len(LENA_CODE_CATS))
    writer.writerow(['Utterance stats:'] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Total utterances:', count_single + count_numbered_multi + count_unnumbered_multi] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Single speaker:', count_single] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Numbered speaker:', count_numbered_multi] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Multi-line speakers:', count_unnumbered_multi] + [''] * (len(LENA_CODE_CATS) - 1))
    writer.writerow(['Angle brackets:', count_angle_brackets] + [''] * (len(LENA_CODE_CATS) - 1))
    
    out_file.close()

def sum_matrix(matrix):
    total = 0
    for lena_code in LENA_CODE_CATS:
        for trans_code in TRANS_CODES:
            total += matrix[lena_code][trans_code]

    return total

def sum_col(matrix, lena_code):
    total = 0
    for trans_code in TRANS_CODES:
        total += matrix[lena_code][trans_code]

    return total

def sum_row(matrix, trans_code):
    total = 0
    for lena_code in LENA_CODE_CATS:
        if lena_code not in ['Far_Speech', 'Noise']:
            total += matrix[lena_code][trans_code]

    return total

# def output_matrix(matrix, filename):
#     out_file = open(filename, 'wb')
#     writer = csv.writer(out_file)

#     writer.writerow([''] + LENA_CODE_CATS)
    
#     for trans_code in TRANS_CODES:
#         row = [trans_code]
#         for lena_code in LENA_CODE_CATS:
#             row.append(matrix[lena_code][trans_code])
#         writer.writerow(row)
    
#     out_file.close()

def run():
    for cur_env in envs:
        matrix = build_matrix(TRANS_CODES, LENA_CODE_CATS)
        count_total = 0
        count_single = 0
        count_numbered_multi = 0
        count_unnumbered_multi = 0
        count_angle_brackets = 0
        
        input_dir = '%s%s/' % (input_path, cur_env)
        dir_contents = glob.glob('%s*.csv' % (input_dir))
        dir_contents = filter(lambda name: re.match(r'^c\d\d\d[ab]?-matrix\.csv$', os.path.basename(name).lower()), dir_contents)
        
        for filename in dir_contents:
            in_file = open(filename, 'rb')
            reader = csv.reader(in_file)
            rows = list(reader)
            in_file.close()
            
            for i in range(1, len(TRANS_CODES) + 1):
                for j in range(1, len(rows[i])):
                    lena_code = LENA_CODE_CATS[j - 1]
                    trans_code = TRANS_CODES[i - 1]
                    matrix[lena_code][trans_code] += int(rows[i][j])

            count_angle_brackets += int(rows[-1][1])
            count_unnumbered_multi += int(rows[-2][1])
            count_numbered_multi += int(rows[-3][1])
            count_single += int(rows[-4][1])
            count_total += int(rows[-5][1])

        output_matrix(matrix, '%ssummary-matrix.csv' % (input_dir), count_single, count_numbered_multi, count_unnumbered_multi, count_angle_brackets)
