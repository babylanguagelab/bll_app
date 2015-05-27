import csv

in_file = open('results/_all3.Table', 'rb')
reader = csv.reader(in_file, delimiter='\t')

headers = reader.next()
filename_col = 1
wav_begin_col = 10
headers.append('Elapsed_Time')

line = reader.next()
prev_filename = None
out_file = None
writer = None

while line:
    filename = line[filename_col]
    if filename != prev_filename:
        if writer:
            out_file.close()
        out_file = open('processed_results/' + filename[:-4] + 'Complete.csv', 'wb')
        writer = csv.writer(out_file, delimiter=',')
        writer.writerow(headers)

        prev_filename = filename

    line.append(line[wav_begin_col])
    writer.writerow(line)
    line = reader.next()

if out_file:
    out_file.close()

in_file.close()
