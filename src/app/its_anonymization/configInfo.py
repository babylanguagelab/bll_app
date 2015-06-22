class ConfigInfo:
    def __init__(self, xpath, key, value, config, description):
        self._xpath = xpath
        self._key = key
        self._value = value
        self._config = config # 0-keep, 1-delete, 2-change
        self._description = description

    def getConfig(self):
        return int(self._config)

    def setConfig(self, change):
        self._config = str(change)
        if (self._config is '2'):
            self._value = self.genDummy(self._key)

    def genDummy(self, key):
        if (key is 'childkey'):
            return '000000'
        else:
            print 'None defined key!'
            return '000000'
