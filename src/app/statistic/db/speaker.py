class Speaker():
    def __init__(self, speaker_id, speaker_codeinfo):
        self.id = speaker_id
        self.codeinfo = speaker_codeinfo

    def is_type(self, speaker_type):
        return self.codeinfo.is_speaker_type(speaker_type)

    def is_distance(self, distance):
        return self.codeinfo.is_distance(distance)

    def has_property(self, prop):
        return self.codeinfo.has_property(prop)

    def get_codeinfo(self):
        return self.codeinfo
