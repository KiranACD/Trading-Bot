class ProductType:
    INTRADAY = "INTRADAY"
    DERIVATIVE_POSITIONAL = "DERIVATIVE_POSITIONAL"
    EQUITY_POSITIONAL = "EQUITY_POSITIONAL"

    @staticmethod
    def get_product_type(product_type):
        if product_type.upper() == 'INTRADAY':
            return ProductType.INTRADAY
        elif product_type.upper() == "DERIVATIVE_POSITIONAL":
            return ProductType.DERIVATIVE_POSITIONAL
        elif product_type.upper() == "EQUITY_POSITIONAL":
            return ProductType.EQUITY_POSITIONAL
        return None