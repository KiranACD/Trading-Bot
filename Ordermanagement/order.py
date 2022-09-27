class Order:
    def __init__(self, orderinputparams=None):
        self.trading_symbol = orderinputparams.trading_symbol if orderinputparams else ''
        self.exchange = orderinputparams.exchange if orderinputparams else ''
        self.uid = orderinputparams.uid if orderinputparams else ''
        self.product_type = orderinputparams.product_type if orderinputparams else ''
        self.order_type = orderinputparams.order_type if orderinputparams else ''
        self.price = orderinputparams.price if orderinputparams else ''
        self.trigger_price = orderinputparams.trigger_price if orderinputparams else ''
        self.quantity = orderinputparams.quantity if orderinputparams else ''
        self.direction = orderinputparams.direction if orderinputparams else ''
        self.order_id = None # Order id received from broker after placing order
        self.order_status = None # One of the status defined in order status
        self.average_price = 0 # Average price at which the order is filled
        self.filled_quantity = 0 # Filled quantity
        self.pending_quantity = 0 # quantity - Filled quantity
        self.orderplacetimestamp = None # Timestamp when the order is placed
        self.lastorderupdatetimestamp = None # applicable if you modiy the order
        self.message = None # In case of you want to save response message
        self.order_ = orderinputparams.order_ if orderinputparams else ''
    
    def __str__(self):
        return 'order id: ' + str(self.order_id) + ', order_status: ' + str(self.order_status) + \
               ', symbol: ' + str(self.trading_symbol) + ', product_type: ' + str(self.product_type) + \
               ', order_type: ' + str(self.order_type) + ', price: ' + str(self.price) + \
               ', trigger_price: ' + str(self.trigger_price) + ', qty: ' + str(self.quantity) + \
               ', filled_qty: ' + str(self.filled_quantity) + ', pending_quantity: ' + str(self.pending_quantity) + \
               ', average_price: ' + str(self.average_price)
    
