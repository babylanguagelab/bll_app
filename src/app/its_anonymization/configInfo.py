import time
from datetime import date

PATH_DICT = {'Serial Number': [('./ProcessingUnit/UPL_Header/TransferredUPL/RecorderInformation/SRDInfo', 'SerialNumber')],
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
             'Clock Time': [('./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime', 'LocalTime'),
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
        self.value = {}

    def get_path(self, key):
        return PATH_DICT[key]

    def set_config(self, key, value):
        self.config[key] = value

    def set_value(self, key, value):
        self.value[key] = value

    def get_config(self, key):
        return self.config[key]

    def get_example(self, key):
        return EXAMPLE_DICT[key]

    def get_fuzzy(self, key):
        value = ""

        if key == 'DOB':
            value = '1000-01-01'
        if key == 'Child ID':
            value = '0000'
        if key == 'Child Key':
            value = '0000000000000000'
        if key == 'Serial Number':
            value = '0000'
        if key == 'Clock Time':
            # example: 2015-06-10T11:30:20Z
            clock_time = strptime(self.value['Clock Time'], "%Y-%m-%dT%H-%M-%SU")
            dob_time = strptime(self.value['DOB'], "%Y-%m-%dT%H-%M-%SU")
            new_time = date(1000, 01, 01) + relativedelta(clock_time, dob_time)

            value = new_time

        return value
