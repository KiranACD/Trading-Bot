from Models.segment import Segment
from Models.producttype import ZerodhaProductType, FyersProductType

class ZerodhaOrderInputParams:
  def __init__(self, trading_symbol):
    self.exchange = "NSE" # default
    self.is_fno = False
    self.segment = Segment.EQUITY # default
    self.product_type = ZerodhaProductType.MIS # default
    self.trading_symbol = trading_symbol
    self.direction = ""
    self.order_type = "" # One of the values of ordermgmt.OrderType
    self.quantity = 0
    self.price = 0
    self.trigger_price = 0 # Applicable in case of SL order
    self.order_ = None
    self.uid = None

  def __str__(self):
    return "symbol=" + str(self.trading_symbol) + ", exchange=" + self.exchange \
      + ", productType=" + self.product_type + ", segment=" + self.segment \
      + ", direction=" + self.direction + ", orderType=" + self.order_type \
      + ", qty=" + str(self.quantity) + ", price=" + str(self.price) + ", triggerPrice=" + str(self.trigger_price) \
      + ", isFnO=" + str(self.is_fno)