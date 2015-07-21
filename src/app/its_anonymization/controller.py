from myXMLParser import XMLParser2
from myConfig import MyConfig
from configInfo import ConfigInfo
import os


class Controller:
    def __init__(self):
        self.configFile = MyConfig()
        self.configInfo = ConfigInfo()

        self.configFile.json_reader('configs')
        for i in self.configFile.content:
            self.configInfo.set_config(i, self.configFile.content[i])
        self.file_list = []

    def get_conf(self):
        return self.configInfo

    def set_conf(self, key, value):
        self.configInfo.set_config(key, value)

    def save_config(self):
        self.configFile.json_writer('configs', self.configInfo.config)

    def set_file_list(self, new_list):
        self.file_list = new_list

    def apply_file(self, filename):
        parser = XMLParser2(filename)
        for i in self.conf_list:
            if i.config == "1":
                parser.del_attr(i.xpath, i.key)
            elif i.config == "2":
                parser.set_attr(i.xpath, i.key, i.get_dummy())

        fname, fext = os.path.splitext(filename)
        parser.save(fname + "_after" + fext)

    def run(self):
        if len(self.file_list) == 0:
            return 1
        if len(self.conf_list) == 0:
            return 2

        for x in self.file_list:
            self.apply_file(x)

        return 0
