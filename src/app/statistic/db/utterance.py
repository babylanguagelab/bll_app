from bll_database import BLLConstants


class Utterance():
    # This is a unique identifies that is given to each Utterance object.
    next_id = 0

    def __init__(self):
        self.speaker = None
        self.lena_notes = None
        self.lena_codes = []
        self.trans_phrase = None
        self.start = None
        self.end = None
        self.trans_codes = []
        self.next = None
        self.prev = None
        self.is_trans_overlap = False
        self.seg = None
        self.id = Utterance.next_id
        Utterance.next_id += 1

    def is_linkable(self):
        is_linkable = True

        i = 0
        while is_linkable and i < len(self.seg.speakers):
            is_linkable = self.seg.speakers[i].codeinfo.is_linkable
            i += 1

        notes_opt = BLLConstants.LENA_NOTES_CODES.get_option(self.lena_notes)
        if is_linkable and notes_opt is not None and not self.trans_phrase:
            is_linkable = notes_opt.is_linkable

        return is_linkable
