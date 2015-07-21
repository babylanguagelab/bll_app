import csv
import json


class MyConfig:
    def __init__(self):
        self.content = {}

    def json_reader(self, filename):
        with open(filename, 'rb') as fp:
            self.content = json.load(fp)

    def json_writer(self, filename, data=None):
        with open(filename, 'wb') as fp:
            if data is not None:
                self.content = data
            json.dump(self.content, fp)

    def change_config(self, key, value):
        self.content[key] = value

    def csv_reader(self, filename):
        with open(filename, 'rb') as fp:
            reader = csv.reader(fp)
            for row in reader:
                self.content.append(row)

    def csv_writer(self, filename, string_list):
        with open(filename, 'wb') as fp:
            writer = csv.writer(fp)
            for row in string_list:
                writer.writerow(row)

# myDict={
#     "Serial Number":0,
#     "Gender":0,
#     "Algorithm Age":0,
#     "Child ID":0,
#     "Child Key":0,
#     "Enroll Date":0,
#     "DOB":0,
#     "Time Zone":0,
#     "UTC Time":0,
#     "Clock Time":0,
# }
