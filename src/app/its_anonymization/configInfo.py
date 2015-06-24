class ConfigInfo:
    def __init__(self, xpath, key, config, description):
        self.xpath = xpath
        self.key = key
        # [FixMe]use enum in future
        self.config = config  # 0-keep, 1-delete, 2-change
        self.description = description

    def get_dummy(self):
        return '0000'
