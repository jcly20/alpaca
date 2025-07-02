

class Candle:

    def __init__(self, open, high, low, close, lastPrice):
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.lastPrice = lastPrice

        if close > open:
            self.side = 'bull'
        elif close < open:
            self.side = 'bear'
        else:
            self.side = 'neutral'
