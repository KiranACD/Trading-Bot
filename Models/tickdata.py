class TickData:
    def __init__(self, tradingSymbol):
        self.tradingSymbol = tradingSymbol
        self.last_traded_price = 0
        self.last_traded_quantity = 0
        self.average_traded_price = 0
        self.volume = 0
        self.total_buy_quantity = 0
        self.total_sell_quantity = 0
        self.open = 0
        self.high = 0
        self.low = 0
        self.close = 0
        self.change = 0
    
    def add_zerodha_data(self, data):

        # self.timestamp = data['timestamp']
        self.last_traded_price = data['last_price']
        self.last_traded_quantity = data['last_traded_quantity']
        self.average_traded_price = data['average_traded_price']
        self.volume = data['volume_traded']
        self.total_buy_quantity = data['total_buy_quantity']
        self.total_sell_quantity = data['total_sell_quantity']
        self.open = data['ohlc']['open']
        self.high = data['ohlc']['high']
        self.low = data['ohlc']['low']
        self.close = data['ohlc']['close']
        self.change = data['change']