import datetime
import decimal
import priceHistory

class portfolio:

    def __init__ (self, equities, cash = 0.0):
        "equities must be a list of tuples of (symbol, quantity)"
        self.symbols = [e[0] for e in equities]
        self.equities = equities
        self.cash = decimal.Decimal(cash)
        self.quantities = {}
        for e in equities:
            self.quantities[e[0]] = e[1]
        self.groupHistory = None

    def __repr__ (self):
        return 'portfolio(%s, %g)' % (self.equities, self.cash)

    def load_to_date(self, connection, number, end_date=datetime.date.today()):
        self.groupHistory = priceHistory.groupHistory(self.symbols)
        self.groupHistory.load_to_date(connection, number, end_date)
        
    def value(self, connection):
        if self.groupHistory == None or self.groupHistory.history_days < 1:
            self.groupHistory = priceHistory.groupHistory(self.symbols)
            self.groupHistory.load_to_date(connection, 1)
        
        result = self.cash
        for s in self.groupHistory.symbols:
            result += self.groupHistory[s].last_price() * decimal.Decimal(self.quantities[s])
        return result
            
            

        
        

        


