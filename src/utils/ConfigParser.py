# csv and json reader and writer
# author: unioah@gmail.com

import csv
import json


class ConfigParser:
    def __init__(self):
        self.content = {}

    def json_reader(self, filename):
        with open(filename, 'rb') as fp:
            self.content = json.load(fp)

    def json_writer(self, filename, data=None):
        with open(filename, 'wb') as fp:
            res = data
            if data is None:
                res = self.content
            json.dump(res, fp)

    def change_config(self, key, value):
        self.content[key] = value

    def csv_reader(self, filename):
        with open(filename, 'rb') as fp:
            reader = csv.reader(fp)
            for row in reader:
                self.content.append(row)

    def csv_writer(self, filename, data=None):
        with open(filename, 'wb') as fp:
            res = data
            if data is None:
                for key, value in self.content:
                    tmp = [key, value]
                    res.append(tmp)
            writer = csv.writer(fp, quoting=csv.QUOTE_ALL)
            for row in res:
                writer.writerow(row)
