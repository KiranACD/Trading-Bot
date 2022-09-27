from json import JSONDecoder

class UserDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
    def object_hook(self, dct):
        for uid in dct:
            try:
                dct[uid]['paper_trade'] = int(dct[uid]['paper_trade'])
                dct[uid]['ticker'] = int(dct[uid]['ticker'])
                dct[uid]['historical_data'] = int(dct[uid]['historical_data'])
            except:
                continue
        return dct