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

    def __repr__ (self):
        return 'portfolio(%s, %s)' % ([(s,self.quantities[s]) for s in sorted(self.quantities.keys())], self.cash)

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

    def values(self, connection):
        gh = priceHistory.groupHistory(self.quantities.keys())
        gh.load_to_date(connection, 1)
        result = {}
        for s in sorted(gh.symbols):
            result[s] = self.quantities[s]*gh[s].last_price()
        return result

    def value(self, connection):
        result = self.cash
        values = self.values(connection)
        for s in values.keys():
            print("%5s: %10.2f" % (s,values[s]))
            result += values[s]
        print(" cash: %10.2f" % (self.cash))
        print("total: %10.2f" % (result))
        return result

    def allocation(self, connection):
        "Return a list of tuples of (symbol, percent_of_portfolio_value)"
        v = float(self.value(connection))
        values = self.values(connection)
        return [(s,float(values[s]/v)) for s in self.quantities.keys()]

    @classmethod
    def from_allocation(cls, connection, allocation, cash_available):
        "Return a portfolio from an allocation"
        symbols = [a[0] for a in allocation]
        ph = priceHistory.groupHistory(symbols)
        ph.load_to_date(connection, 1)
        percent_allocated = sum([a[1] for a in allocation])
        equities = []
        cash_left = decimal.Decimal(cash_available)
        for a in allocation:
            quantity = int(round(a[1]*float(cash_available)/float(ph[a[0]].last_price())))
            equities.append((a[0],quantity))
            cash_left -= quantity * ph[a[0]].last_price()
        return portfolio(equities, cash_left)

    def symbols(self):
        return sorted(self.quantities.keys())

