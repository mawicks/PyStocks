import datetime
import decimal
import priceHistory

class portfolio:

    def __init__ (self, equities, cash = 0.0):
        "equities must be a list of tuples of (symbol, quantity)"
        self.cash = decimal.Decimal(cash)
        self.quantities = {}
        for e in equities:
            if e[1] != 0:
                self.quantities[e[0]] = e[1]
        self.groupHistory = None

    def __repr__ (self):
        return 'portfolio(%s, %s)' % ([(s,self.quantities[s]) for s in self.quantities], self.cash)

    def __add__ (self, other):
        result = {}

        for symbol in self.quantities:
            result[symbol] = self.quantities[symbol]

        for symbol in other.quantities:
            if symbol in result:
                result[symbol] += other.quantities[symbol]
            else:
                result[symbol] = other.quantities[symbol]
            if result[symbol] == 0:
                del result[symbol]

        return portfolio([(s,result[s]) for s in result], self.cash+other.cash)

    def __sub__ (self, other):
        result = {}

        for symbol in self.quantities:
            result[symbol] = self.quantities[symbol]

        for symbol in other.quantities:
            if symbol in result:
                result[symbol] -= other.quantities[symbol]
            else:
                result[symbol] = - other.quantities[symbol]
            if result[symbol] == 0:
                    del result[symbol]

        return portfolio([(s,result[s]) for s in result], self.cash-other.cash)

    def load_to_date(self, connection, number, end_date=datetime.date.today()):
        self.groupHistory = priceHistory.groupHistory(self.quantities.keys())
        self.groupHistory.load_to_date(connection, number, end_date)
        
    def value(self, connection):
        if self.groupHistory == None or self.groupHistory.history_days < 1:
            self.groupHistory = priceHistory.groupHistory(self.quantities.keys())
            self.groupHistory.load_to_date(connection, 1)
        
        result = self.cash
        for s in self.groupHistory.symbols:
            result += self.groupHistory[s].last_price() * decimal.Decimal(self.quantities[s])
        return result

    def allocation(self, connection):
        "Return a list of tuples of (symbol, percent_of_portfolio_value)"
        v = float(self.value(connection))
        return [(s,float(self.groupHistory[s].last_price()) * (self.quantities[s])/v) for s in self.groupHistory.symbols]


    @classmethod
    def from_allocation(cls, allocation, cash_available, connection):
    	"Return a portfolio from an allocation"
        symbols = [a[0] for a in allocation]
        ph = priceHistory.groupHistory(symbols)
        ph.load_to_date(connection, 1)
        percent_allocated = sum([a[1] for a in allocation])
        equities = []
        cash_left = decimal.Decimal(cash_available,2)
        print cash_left
        for a in allocation:
            quantity = int(round(a[1]*cash_available/float(ph[a[0]].last_price())))
            equities.append((a[0],quantity))
            cash_left -= quantity * ph[a[0]].last_price()
            print cash_left
        return portfolio(equities, cash_left)



