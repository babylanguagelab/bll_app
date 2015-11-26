# csv and json reader and writer
# author: unioah@gmail.com

import csv
import json


def json_reader(filename):
    content = {}
    with open(filename, 'rb') as fp:
        content = json.load(fp)
    return content


def json_writer(filename, data):
    with open(filename, 'wb') as fp:
        json.dump(data, fp)


def csv_reader(filename):
    content = []
    with open(filename, 'rb') as fp:
        reader = csv.reader(fp)
        for row in reader:
            content.append(row)
    return content


def csv_writer(filename, data):
    with open(filename, 'wb') as fp:
        writer = csv.writer(fp, quoting=csv.QUOTE_ALL)
        for row in data:
            writer.writerow(row)

def csv_dict_reader(filename, head=None):
    content = csv.DictReader(open(filename))
    return content

test = csv_dict_reader("C001A_20090615.csv", ["Index"])
for i in test:
    print(i["Index"])
