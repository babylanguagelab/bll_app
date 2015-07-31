import time
import datetime
from dateutil.relativedelta import relativedelta

PATH_DICT = {'Serial Number':[('./ProcessingUnit/UPL_Header/TransferredUPL/RecorderInformation/SRDInfo', 'SerialNumber')],
             'Gender': [('./ExportData/Child', 'Gender'), ('./ProcessingUnit/ChildInfo', 'gender'), ('./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', 'Gender')],
             'Algorithm Age': [('./ChildInfo', 'algorithmAge')],
             'Child ID': [('./ExportData/Child', 'id')],
             'Child Key': [('./ExportData/Child', 'ChildKey'), ('./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', 'ChildKey')],
             'Enroll Date': [('./ExportData/Child', 'EnrollDate')],
             'DOB': [('./ExportData/Child', 'DOB'), ('./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', 'DOB')],
             'Time Zone': [('./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime', 'TimeZone')],
             'UTC Time': [('./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime', 'UTCTime')],
             'Clock Time':
             [('./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime', 'LocalTime'),
              ('./ProcessingUnit/Bar', 'startClockTime'),
              ('./ProcessingUnit/Recording', 'startClockTime'),
              ('./ProcessingUnit/Recording', 'endClockTime'),
              ('./ProcessingUnit/Bar/Recording', 'startClockTime'),
              ('./ProcessingUnit/Bar/Recording', 'endClockTime'),
              ('./ProcessingUnit/Bar/FiveMinuteSection', 'startClockTime'),
              ('./ProcessingUnit/Bar/FiveMinuteSection', 'endClockTime'),
              ('./ProcessingUnit/UPL_SectorSummary/Item', 'timeStamp')]}

EXAMPLE_DICT = {"Serial Number": "This is the serial number of the DLP. Fuzz replaces the value with random or specified new values.",
                "Algorithm Age": "This is a value used by LENA in its processing of the UPL files. It is not an exact age.",
                "Gender": "Gender information",
                "Child ID": "Depending on your participant labeling system, you may or may not want to fuzz this. Fuzz replaces the value with random or specified new values.",
                "Child Key": "Depending on your participant labeling system, you may or may not want to fuzz this. Fuzz replaces the value with random or specified new values.",
                "Enroll Date": "This is the date the child was input into LENA's system. If you are anonymizing the dates, it is important to delete this.",
                "DOB": "Fuzz replaces the value of DOB with random or specified new values. Default is January 1, 1000. Clock time for each its file will be calculated based on this new Fuzz'ed value and the child's original age.",
                "Time Zone": "Time Zone information",
                "UTC Time": "UTC Time information",
                "Clock Time": "example"}


class ConfigInfo:
    def __init__(self):
        self.items = ["Serial Number", "Gender", "Algorithm Age",
                      "Child ID", "Child Key", "Enroll Date", "DOB",
                      "Time Zone", "UTC Time", "Clock Time"]

        # 0-keep, 1-delete, 2-change
        self.config = {}
        self.original = {}

    def get_path(self, key):
        return PATH_DICT[key]

    def set_config(self, key, config, value=None):
        if value is None:
            self.config[key][0] = config
        else:
            self.config[key] = [config, value]

    def get_config(self, key):
        return self.config[key]

    def set_original(self, key, value):
        self.original[key] = value

    def get_original(self, key):
        return self.original[key]

    def get_exp(self, key):
        return EXAMPLE_DICT[key]

    def get_fuzzy(self, key):
        value = " "

        if key == 'Clock Time':
            # example: 2015-06-10T11:30:20Z
            if self.original['Clock Time'][-1] == 'Z':
                clock_time = datetime.datetime.strptime(self.original['Clock Time'], "%Y-%m-%dT%H:%M:%SZ")
            else:
                clock_time = datetime.datetime.strptime(self.original['Clock Time'], "%Y-%m-%dT%H:%M:%S")
            dob_time = datetime.datetime.strptime(self.original['DOB'], "%Y-%m-%d")
            new_time = datetime.date(2000, 01, 01) + relativedelta(clock_time, dob_time)

            if self.original['Clock Time'][-1] == 'Z':
                value = new_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                value = new_time.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            value = self.config[key][1]

        return value
