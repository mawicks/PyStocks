import datetime
import decimal
import pricehistory

class portfolio:

    def __init__ (self, equities=[], cash = 0.0):
        "equities must be a list of tuples of (symbol, quantity)"
        self.cash = decimal.Decimal(cash).quantize(decimal.Decimal('0.01'))
        self.quantities = {}
        for e in equities:
            if e[1] != 0:
                self.quantities[e[0]] = e[1]

    def __repr__ (self):
        return 'portfolio(%s, %s)' % ([(s,self.quantities[s]) for s in sorted(self.quantities.keys())], self.cash)

    def dump (self, dumper, writer):
        dumper(dict(equities=self.quantities, cash=str(self.cash)), writer, indent=5, sort_keys=True)

    def load (self, loader, reader):
        d = loader(reader)
        if 'cash' in d:
            self.cash = decimal.Decimal(d['cash'])
        else:
            self.cash = decimal.Decimal('0.00')
        if 'equities' in d:
            self.quantities = d['equities']
            for symbol,quantity in self.quantities.items():
                if not isinstance(quantity, int):
                    raise TypeError('Non-integer equity quantity in portfolio serialization')
        else:
            self.quantities = {}

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

    def values(self, price_source):
        gh = pricehistory.GroupHistory(self.quantities.keys())
        gh.load_to_date(price_source, 1)
        result = {}
        for s in sorted(gh.symbols):
            result[s] = self.quantities[s]*gh[s].last_price()
        return result

    def value(self, price_source):
        result = self.cash
        values = self.values(price_source)
        for s in sorted(values.keys()):
            print("{0:>5s}: {1:10n}".format(s,values[s]))
            result += values[s]
        print(" cash: {0:10n}".format(self.cash))
        print("total: {0:10n}".format(result))
        return result

    def allocation(self, price_source):
        "Return a list of tuples of (symbol, percent_of_portfolio_value)"
        v = float(self.value(price_source))
        values = self.values(price_source)
        return [(s,float(values[s]/v)) for s in self.quantities.keys()]

    @classmethod
    def from_allocation(cls, price_source, allocation, cash_available):
        "Return a portfolio from an allocation"
        symbols = [a[0] for a in allocation]
        ph = pricehistory.GroupHistory(symbols)
        ph.load_to_date(price_source, 1)
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

