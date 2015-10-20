# the information between a <Turn></Turn> pair of tags in a TRS file.
class Segment():
    def __init__(self, num, start, end, speakers=[], utters=[]):

        self.num = num
        self.speakers = speakers
        self.utters = utters
        self.start = start
        self.end = end
