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

    def change_config(self, string_list):
        for x in range(len(self.content)):
            if self.content[x] != string_list[x]:
                self.content[x] = string_list[x]

    def write_config(self, filename, string_list):
        fp = open(filename, 'wb')
        writer = csv.writer(fp)

        for row in self.content:
            writer.writerow(row)
