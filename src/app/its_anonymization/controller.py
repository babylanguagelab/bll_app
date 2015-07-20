from myXMLParser import XMLParser2
from myConfig import MyConfig
from configInfo import ConfigInfo
import os


class Controller:
    def __init__(self):
        # get settings from default configuration file
        self.MyConfig = MyConfig()
        self.MyConfig.read_config("config.txt")
        self.conf_list = [ConfigInfo(x[0], x[1], x[2], x[3]) for x in self.MyConfig.content]
        self.file_list = []

    # default configuration list
    def get_conf_dlist(self):
        self.MyConfig.read_config("dconfig.txt")
        return [ConfigInfo(x[0], x[1], x[2], x[3]) for x in self.MyConfig.content]

    # def saveAsDefault(self):

    def get_conf_list(self):
        return [x.config for x in self.conf_list]

    def set_conf_list(self, new_list):
        for x in range(len(new_list)):
            if self.conf_list[x].config != new_list[x]:
                self.conf_list[x].config = new_list[x]

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
