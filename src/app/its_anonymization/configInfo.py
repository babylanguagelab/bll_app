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
            otime = self.value['Clock Time'].split('T')
            [oyear, omonth, oday] = otime[0].split('-')
            [byear, bmonth, bday] = self.value['DOB'].split('-')

            nyear = 0; nmonth = 0
            nday = int(oday) - int(bday)
            if nday <= 0:
                nday += 12
                nmonth = -1
            nmonth += int(omonth) - int(bmonth)
            if nmonth <= 0:
                nmonth += 12
                nyear = -1
            nyear += int(oyear) - int(byear)
            nday = str(nday); nmonth = str(nmonth); nyear = str(nyear)
            if len(nday) == 1:
                nday = '0' + nday
            if len(nmonth) == 1:
                nmonth = '0' + nmonth
            if len(nyear) < 4:
                nyear = '0' * (4 - len(nyear)) + nyear

            ntime = nyear + '-' + nmonth + '-' + nday
            value = ntime + 'T' + otime[1]

        return value
