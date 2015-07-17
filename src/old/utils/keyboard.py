import win32api
import win32con
import time

class Keyboard(object):
    COMBS = {
        'A': [
            'SHIFT',
            'a'],
        'B': [
            'SHIFT',
            'b'],
        'C': [
            'SHIFT',
            'c'],
        'D': [
            'SHIFT',
            'd'],
        'E': [
            'SHIFT',
            'e'],
        'F': [
            'SHIFT',
            'f'],
        'G': [
            'SHIFT',
            'g'],
        'H': [
            'SHIFT',
            'h'],
        'I': [
            'SHIFT',
            'i'],
        'J': [
            'SHIFT',
            'j'],
        'K': [
            'SHIFT',
            'k'],
        'L': [
            'SHIFT',
            'l'],
        'M': [
            'SHIFT',
            'm'],
        'N': [
            'SHIFT',
            'n'],
        'O': [
            'SHIFT',
            'o'],
        'P': [
            'SHIFT',
            'p'],
        'R': [
            'SHIFT',
            'r'],
        'S': [
            'SHIFT',
            's'],
        'T': [
            'SHIFT',
            't'],
        'U': [
            'SHIFT',
            'u'],
        'W': [
            'SHIFT',
            'w'],
        'X': [
            'SHIFT',
            'x'],
        'Y': [
            'SHIFT',
            'y'],
        'Z': [
            'SHIFT',
            'z'],
        'V': [
            'SHIFT',
            'v'],
        'Q': [
            'SHIFT',
            'q'],
        '?': [
            'SHIFT',
            '/'],
        '>': [
            'SHIFT',
            '.'],
        '<': [
            'SHIFT',
            ','],
        '"': [
            'SHIFT',
            "'"],
        ':': [
            'SHIFT',
            ';'],
        '|': [
            'SHIFT',
            '\\'],
        '}': [
            'SHIFT',
            ']'],
        '{': [
            'SHIFT',
            '['],
        '+': [
            'SHIFT',
            '='],
        '_': [
            'SHIFT',
            '-'],
        '!': [
            'SHIFT',
            '1'],
        '@': [
            'SHIFT',
            '2'],
        '#': [
            'SHIFT',
            '3'],
        '$': [
            'SHIFT',
            '4'],
        '%': [
            'SHIFT',
            '5'],
        '^': [
            'SHIFT',
            '6'],
        '&': [
            'SHIFT',
            '7'],
        '*': [
            'SHIFT',
            '8'],
        '(': [
            'SHIFT',
            '9'],
        ')': [
            'SHIFT',
            '0'],
        'ALT-TAB': [
            'ALT',
            'TAB'],
        }
    BASE = {
        '0': 48,
        '1': 49,
        '2': 50,
        '3': 51,
        '4': 52,
        '5': 53,
        '6': 54,
        '7': 55,
        '8': 56,
        '9': 57,
        'a': 65,
        'b': 66,
        'c': 67,
        'd': 68,
        'e': 69,
        'f': 70,
        'g': 71,
        'h': 72,
        'i': 73,
        'j': 74,
        'k': 75,
        'l': 76,
        'm': 77,
        'n': 78,
        'o': 79,
        'p': 80,
        'q': 81,
        'r': 82,
        's': 83,
        't': 84,
        'u': 85,
        'v': 86,
        'w': 87,
        'x': 88,
        'y': 89,
        'z': 90,
        '.': 190,
        '-': 189,
        ',': 188,
        '=': 187,
        '/': 191,
        ';': 186,
        '[': 219,
        ']': 221,
        '\\': 220,
        "'": 222,
        'ALT': 18,
        'TAB': 9,
        'CAPSLOCK': 20,
        'ENTER': 13,
        'BS': 8,
        'CTRL': 17,
        'ESC': 27,
        ' ': 32,
        'END': 35,
        'DOWN': 40,
        'LEFT': 37,
        'UP': 38,
        'RIGHT': 39,
        'SELECT': 41,
        'PRINTSCR': 44,
        'INS': 45,
        'DEL': 46,
        'LWIN': 91,
        'RWIN': 92,
        'LSHIFT': 160,
        'SHIFT': 161,
        'LCTRL': 162,
        'RCTRL': 163,
        'VOLUP': 175,
        'DOLDOWN': 174,
        'NUMLOCK': 144,
        'SCROLL': 145,
        }

    @staticmethod
    def key_down(key_cd):
        win32api.keybd_event(key_cd, 0, win32con.KEYEVENTF_EXTENDEDKEY, 0)

    @staticmethod
    def key_up(key_cd):
        win32api.keybd_event(key_cd, 0, win32con.KEYEVENTF_EXTENDEDKEY | win32con.KEYEVENTF_KEYUP, 0)

    @staticmethod
    def key_press(c, press_interval=0.05):
        if c in Keyboard.BASE:
            Keyboard.key_down(Keyboard.BASE[c])
            time.sleep(press_interval)
            Keyboard.key_up(Keyboard.BASE[c])

        elif c in Keyboard.COMBS:
            Keyboard.key_down(Keyboard.BASE[Keyboard.COMBS[c][0]])
            time.sleep(press_interval)
            Keyboard.key_down(Keyboard.BASE[Keyboard.COMBS[c][1]])
            time.sleep(press_interval)
            Keyboard.key_up(Keyboard.BASE[Keyboard.COMBS[c][1]])
            time.sleep(press_interval)
            Keyboard.key_up(Keyboard.BASE[Keyboard.COMBS[c][0]])

    @staticmethod
    def type_msg(msg, press_interval=0.05):
        for c in msg:
            Keyboard.key_press(c, press_interval)
