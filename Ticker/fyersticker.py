from Ticker.baseticker import BaseTicker

class FyersTicker(BaseTicker):
    __instance = None

    @staticmethod
    def get_instance():
        if FyersTicker.__instance is None:
            FyersTicker()
        return FyersTicker.__instance
    
    def __init__(self):
        if FyersTicker.__instance is not None:
            raise Exception('This class is a singleton!')
        else:
            FyersTicker.__instance = self
        super().__init__('FyersTicker')
