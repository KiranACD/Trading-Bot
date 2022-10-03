import logging
import threading

class BaseTicker:

    def __init__(self, tickername):
        self.tickername = tickername
        self.ticker = None
        self.tick_listeners = []
    
    def start_ticker(self, uid):
        pass

    def stop_ticker(self):
        pass

    def register_listener(self, listener):
        self.tick_listeners.append(listener)
    
    def register_symbols(self, symbols):
        pass

    def unregister_symbols(self, symbols):
        pass

    def on_new_ticks(self, ticks):
        for tick in ticks:
            for listener in self.tick_listeners:
                try:
                    tl = threading.Thread(target=listener, args=(tick,))
                    tl.start()
                    # listener(tick)
                except Exception as e:
                    print('Error')
                    logging.error('BaseTicker: Exception from listener callback function. Error => %s', str(e))
    
    def onConnect(self):
        logging.info('Ticker connection successful.')
    
    def onDisconnect(self, code, reason):
        logging.error('Ticker got disconnected. code = %d, reason = %s', code, reason)
    
    def onError(self, code, reason):
        logging.error('Ticker errored out. code = %d, reason = %s', code, reason)

    def onReconnect(self, attempts_count):
        logging.warn('Ticker reconnecting.. attemptscount = %d', attempts_count)
    
    def on_max_reconnects_attempt(self):
        logging.error('Ticker max auto reconnects attempted and giving up...')
    
    def onOrderUpdate(self, data):
        pass

        