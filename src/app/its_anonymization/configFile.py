import csv

class MyConfig:
    def __init__(self):
        self.content = []

    def read_config(self, filename):
        fp = open(filename, 'rb')
        reader = csv.reader(fp)
        for row in reader:
            self.content.append(row)

        fp.close()

    def write_config(self, filename, string_list):
        fp = open(filename, 'wb')
        writer = csv.writer(fp)

        for row in string_list:
            writer.writerow(row)
