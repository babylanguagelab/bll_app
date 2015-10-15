class Code():
    def __init__(self, options_dict):
        self.options_dict = options_dict

    def get_option(self, code_str):
        result = None
        if code_str in self.options_dict:
            result = self.options_dict[code_str]

        return result

    def get_all_options_codes(self):
        return self.options_dict.keys()


class CodeInfo():
    def __init__(self, db_id, code, desc, is_linkable, distance, speaker_type,
                 props=[]):
        self.db_id = db_id
        self.desc = desc
        self.code = code
        self.is_linkable = is_linkable
        self.distance = distance
        self.speaker_type = speaker_type
        self.props_dict = dict(zip(props, [True] * len(props)))

    def has_property(self, prop):
        return prop in self.props_dict

    def is_linkable(self):
        return self.is_linkable

    def is_distance(self, distance):
        return self.distance == distance

    def is_speaker_type(self, speaker_type):
        return self.speaker_type == speaker_type

    def get_code_desc(self):
        return self.desc

    def get_code(self):
        return self.code
