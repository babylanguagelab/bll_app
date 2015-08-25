import myDebug


# Default Configurations for Domain Items
# 0 - keep
# 1 - delete
# 2 - dummy with follow value
CONF_TABLE = {
    "Serial Number": [2, "0000"],
    "Gender": [0, -1],
    "Algorithm Age": [0, -1],
    "Child ID": [2, "0000"],
    "Child Key": [2, "0000000000000000"],
    "Enroll Date": [1, -1],
    "DOB": [2, "2000-01-01"],
    "Time Zone": [1, -1],
    "UTC Time": [1, -1],
    "Clock Time": [2, "0"]
}

PATH_DICT = {
    'Serial Number':[('./ProcessingUnit/UPL_Header/TransferredUPL/RecorderInformation/SRDInfo', 'SerialNumber')],
    'Gender': [('./ExportData/Child', 'Gender'), ('./ProcessingUnit/ChildInfo', 'gender'),
               ('./ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', 'Gender')],
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
              ('./ProcessingUnit/UPL_SectorSummary/Item', 'timeStamp')]
}


#  function xml filter


class Main:
    def __init__(self):
        myDebug('123')
        # get config list
        # get currrent file list

    def run():
        myDebug('123')
        # run on each file


if __name__ == '__main__':
    main = Main()
    mWindow.run()

