class TickData:
    def __init__(self, tradingSymbol):
        self.timestamp = 0
        self.trading_symbol = tradingSymbol
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
    
    def add_fyers_data(self, data):
        self.timestamp = data['last_traded_time']
        self.last_traded_price = data['ltp']
        self.last_traded_quantity = data['last_traded_qty']
        self.average_traded_price = data['avg_trade_price']
        self.total_buy_quantity = data['tot_buy_qty']
        self.total_sell_quantity = data['tot_sell_qty']
        self.open = data['min_open_price']
        self.high = data['min_high_price']
        self.low = data['min_low_price']
        self.close = data['min_close_price']

    def __str__(self):
        return 'Trading Symbol: ' + self.trading_symbol + ', LTP: ' + str(self.last_traded_price)