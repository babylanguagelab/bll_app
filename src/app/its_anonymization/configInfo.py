PATH_DICT = {'Serial Number': [('path', 'value')],
             'Gender': [('path', 'value')],
             'Algorithm Age': [('path', 'value')],
             'Child ID': [('path', 'value')],
             'Child Key': [('path', 'value')],
             'Enroll Date': [('path', 'value')],
             'DOB': [('path', 'value')],
             'Time Zone': [('path', 'value')],
             'UTC Time': [('path', 'value')],
             'Clock Time': [('path', 'value')]}

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
                      'Child ID', 'Child Key', 'Enroll Data', 'DOB',
                      'TIME Zone', 'UTC Time', 'Clock Time']

        # 0-keep, 1-delete, 2-change
        self.config = 0

    def get_path(self, key):
        return PATH_DICT[key]

    def get_config(self, key):
        return self.config

    def get_example(self, key):
        return EXAMPLE_DICT[key]

    def get_dummy(self):
        dummy_value = '0000000'

        if self.key == "LocalTime":
            dummy_value = "Tuesday 13:17:33"
        elif self.key == "EnrollDate":
            dummy_value = "2000-01-01"
        elif self.key == "ChildKey":
            dummy_value = "0000000000000000"
        elif self.key == "DOB":
            dummy_value = "2000-01-01"
        elif self.key == "timeStamp":
            dummy_value = "Tuesday 13:17:33"
        elif self.key == "startClockTime":
            dummy_value = "Tuesday 14:23:54"
        elif self.key == "endClockTime":
            dummy_value = "Tuesday 02:00:40"

        return dummy_value
