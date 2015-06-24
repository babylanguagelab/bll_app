from debug import myDebug


class ConfigInfo:
    def __init__(self, xpath, key, config, description):
        self.xpath = xpath
        self.key = key
        # [FixMe]use enum in future
        self.config = config  # 0-keep, 1-delete, 2-change
        self.description = description

    def getDummy(self):
        if (self.key == 'childkey'):
            return '000000'
        else:
            myDebug('None defined key!', self.key)
            return '000000'
