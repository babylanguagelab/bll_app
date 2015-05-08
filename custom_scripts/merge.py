import csv
import glob

out_file = open('_all.txt', 'wb')
writer = csv.writer(out_file, delimiter='\t')

csv_files = glob.glob('*.csv')
wrote_headers = False

for i in range(len(csv_files)):
    print 'Processing file %d of %d' % (i + 1, len(csv_files))
    
    in_file = open(csv_files[i], 'rb')
    line = in_file.readline()
    delim = '\t' if line.find('\t') > -1 else ','
    in_file.seek(0)
    
    reader = csv.reader(in_file, delimiter=delim)
    
    row = reader.next()
    if not wrote_headers:
        writer.writerow(row)
        wrote_headers = True

    for row in reader:
        writer.writerow(row)

    in_file.close()

out_file.close()
        
