import re

def print_container(label, container_list):
    print label
    for container in container_list:
        for utter in container:
            print utter

def get_word_count(utter):
    count = 0
    if utter.trans_phrase:
        words = re.split(r'\s+', utter.trans_phrase.strip())
        words = filter(lambda w: w.lower() not in ('xxx', 'bbl', '<>'), words)
        count = len(words)

    return count

def get_trans_segs(segs):
    trans_segs = []
    i = 0
    #while i < len(segs) and not seg_contains_speech(segs[i]) and segs[i].end < 60 * 60:
    while i < len(segs) and not seg_contains_speech(segs[i]):
        i += 1

    low = i

    i = len(segs) - 1
    while i > low and not seg_contains_speech(segs[i]) or seg_has_void_speaker(segs[i]):
        i -= 1
    high = i + 1

    i = low
    while i < high:
        trans_segs.append(segs[i])
        i += 1
    
    #while i < len(segs) and (seg_contains_speech(segs[i]) or (segs[i].start < 75 * 60) and not seg_has_void_speaker(segs[i])):
    #while i < len(segs) and seg_contains_speech(segs[i]) and not seg_has_void_speaker(segs[i]):
    #    trans_segs.append(segs[i])
    #    i += 1

    return trans_segs

def seg_contains_speech(seg):
    i = 0
    contains_speech = False
    while not contains_speech and i < len(seg.utters):
        contains_speech = bool(seg.utters[i].trans_phrase and len(seg.utters[i].trans_codes) == 4)
        i += 1

    return contains_speech

def seg_has_void_speaker(seg):
    i = 0
    found = False
    while seg.speakers and i < len(seg.speakers) and not found:
        found = seg.speakers[i].speaker_codeinfo.code == 'VOID'
        i += 1

    return found

def get_time_str(total_sec):
    hours = 0
    mins = 0
    sec = 0

    hours = int(total_sec / (60 * 60))
    total_sec -= (hours * 60 * 60)
    mins = int(total_sec / 60)
    total_sec -= (mins * 60)
    sec = total_sec

    return '%02d:%02d:%05.2f' % (hours, mins, sec)
