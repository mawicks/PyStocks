import numpy
import datetime

class SymbolHistory:

    def __init__(self, symbol, history=[]):
        "history should be an iterator returning tuples (date, price, daily_return) with most recent date last"
        self.symbol = symbol
        self.history = [ t for t in history]
        
    def __repr__(self):
        return 'SymbolHistory({0}, {1!r})'.format(self.symbol, self.history)

    def first_date(self):
        "Returns the first date in the history"
        if len(self.history) > 0:
            return self.history[0][0]
        else:
            return None

    def last_date(self):
        "Returns the last date in the history"
        if len(self.history) > 0:
            return self.history[-1][0]
        else:
            return None

    def first_price(self):
        "Returns the first price in the history"
        if len(self.history) > 0:
            return self.history[0][1]
        else:
            return None

    def last_price(self):
        "Returns the last price in the history"
        if len(self.history) > 0:
            return self.history[-1][1]
        else:
            return None

    def prices(self):
        "Returns an iterator over all prices in the history"
        return map(lambda s: s[1], self.history)

    def returns(self):
        "Returns an iterator over all daily returns in the history"
        return map(lambda s: s[2], self.history)

    def days(self):
        "Returns the number of days in the history"
        return len(self.history)

    def load_to_date(self, price_source, number, end_date=datetime.date.today()):
        self.history = [tuple for tuple in price_source.load_to_date(self.symbol, number, end_date=end_date)]

    def load_date_range(self, price_source, connection, start_date, end_date=datetime.date.today()):
        self.history = [tuple for tuple in price_source.load_date_range(self.symbol, start_date, end_date=end_date)]


class GroupHistory:

    def __init__ (self, symbols, history={}):
        self.symbols = list(history.keys())
        self.omitted_symbols = [s for s in symbols if s not in history.keys()]
        self.history = history
        self.history_days = 0

    def __repr__ (self):
        return 'GroupHistory(%r, %r)' % (self.symbols+self.omitted_symbols, self.history)

    def __getitem__ (self, item):
        return self.history[item]

    def load_to_date(self, price_source, number, end_date=datetime.date.today()):
        histories = []
        for x in map(SymbolHistory, self.symbols+self.omitted_symbols):
            x.load_to_date(price_source, number, end_date)
            histories.append(x)                

        if len(histories) > 0:
            first_date = max([x.first_date() for x in histories if x.days()==number])
            last_date = max([x.last_date() for x in histories if x.days()==number])
            self.history_days = number
        else:
            first_date = None
            last_date = None

        # Remove any symbol (and its history) if its first_date() doesn't match.
        self.omitted_symbols = [x.symbol for x in histories
                                if x.first_date()!=first_date or x.last_date()!=last_date]

        if len(self.omitted_symbols) > 0:
            print("Removing symbols with missing or outdated data: " + ", ".join(self.omitted_symbols))
            
        # Add "good" histories to dictionary (efficient only if "omitted_symbols" is short)
        self.history = {}
        for x in histories:
            if x.symbol not in self.omitted_symbols:
                self.history[x.symbol] = x

        self.symbols = [x.symbol for x in histories if x.symbol not in self.omitted_symbols]
                
    def matrix_of_returns(self):
        result = numpy.empty([len(self.symbols), self.history_days])
        for i in range(len(self.symbols)):
            result[i] = list(self.history[self.symbols[i]].returns())
        return result


class watchList:
    def __init__(self, list=[]):
        self.list = list

    def load(self,connection):
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.symbol,s.id " + 
                           " FROM watch_list w LEFT JOIN symbols s "
                           " ON (s.id = w.symbol_id) "
                           " ORDER by s.symbol")
            self.list = cursor.fetchall()

    def symbols(self):
        return [s[0] for s in self.list]

    def __repr__ (self):
        return 'watchList(%r)' % (self.list)
