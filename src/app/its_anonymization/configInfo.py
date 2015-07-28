import time
from datetime import date
from dateutil.relativedelta import relativedelta

PATH_DICT = {'Serial Number':
             [('./ProcessingUnit/UPL_Header/TransferredUPL/RecorderInformation/SRDInfo', 'SerialNumber')],
             'Gender': [('./ExportData/Child', 'Gender'),
                        ('./ProcessingUnit/ChildInfo', 'gender'),
                        ('./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', 'Gender')],
             'Algorithm Age': [('./ChildInfo', 'algorithmAge')],
             'Child ID': [('./ExportData/Child', 'id')],
             'Child Key': [('./ExportData/Child', 'ChildKey'),
                           ('./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', 'ChildKey')],
             'Enroll Date': [('./ExportData/Child', 'EnrollDate')],
             'DOB': [('./ExportData/Child', 'DOB'),
                     ('./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', 'DOB')],
             'Time Zone': [('./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime',
                            'TimeZone')],
             'UTC Time': [('./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime',
                           'UTCTime')],
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

EXAMPLE_DICT = {'Serial Number': 'example',
                'Gender': 'example',
                'Algorithm Age': 'example',
                'Child ID': 'example',
                'Child Key': 'example',
                'Enroll Date': 'example',
                'DOB': 'example',
                'Time Zone': 'example',
                'UTC Time': 'example',
                'Clock Time': 'example'}


class ConfigInfo:
    def __init__(self):
        self.items = ['Serial Number', 'Gender', 'Algorithm Age',
                      'Child ID', 'Child Key', 'Enroll Date', 'DOB',
                      'Time Zone', 'UTC Time', 'Clock Time']

        # 0-keep, 1-delete, 2-change
        self.config = {}
        self.original = {}

    def get_path(self, key):
        return PATH_DICT[key]

    def set_config(self, key, config, value=None):
        if value == None:
            self.config[key][0] = config
        else:
            self.config[key] = [config, value]

    def get_config(self, key):
        return self.config[key]

    def set_original(self, key, value):
        self.original[key] = value

    def get_original(self, key):
        return self.original[key]

    def get_example(self, key):
        return EXAMPLE_DICT[key]

    def get_fuzzy(self, key):
        value = " "

        if key == 'Clock Time':
            # example: 2015-06-10T11:30:20Z
            clock_time = strptime(self.original['Clock Time'],
                                  "%Y-%m-%dT%H-%M-%SU")
            dob_time = strptime(self.original['DOB'], "%Y-%m-%dT%H-%M-%SU")
            new_time = date(1000, 01, 01) + relativedelta(clock_time, dob_time)

            value = new_time
        else:
            value = self.config[key][1]

        return value
