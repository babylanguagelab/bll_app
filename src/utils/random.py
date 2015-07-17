import random


class RandomGenerater():
    def __init__(self):
        self.seed = random.seed()

    def genRangeInt(self, size):
        tmp = [str(random.randint(1, 9)) for x in range(size)]
        return ''.join(tmp)
