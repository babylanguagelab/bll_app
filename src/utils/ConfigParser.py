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

# read CSV with specified header(column) names
def csv_dict_reader(filename, header):
    content = []
    with open(filename, 'rt') as fp:
        csv_content = csv.DictReader(fp)
        for row in csv_content:
            new_row = []
            for i in header:
                new_row.append(row[i])
            content.append(new_row)
    return content
