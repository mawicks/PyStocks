import numpy
import datetime

class SymbolHistory:

    def __init__(self, symbol, history=[]):
        "history should be an iterator returning tuples (date, price, daily_return) with most recent date last"
        self._symbol = symbol
        self._history = [ t for t in history]
        
    def __repr__(self):
        return 'SymbolHistory({0}, {1!r})'.format(self._symbol, self._history)

    def all_dates(self):
        "Returns set of all dates in the history"
        return set(h[0] for h in self._history)

    def keep_only(self, dates):
        self._history = [ t for t in self._history if t[0] in dates ]

    def first_date(self):
        "Returns the first date in the history"
        if len(self._history) > 0:
            return self._history[0][0]
        else:
            return None

    def last_date(self):
        "Returns the last date in the history"
        if len(self._history) > 0:
            return self._history[-1][0]
        else:
            return None

    def first_price(self):
        "Returns the first price in the history"
        if len(self._history) > 0:
            return self._history[0][1]
        else:
            return None

    def last_price(self):
        "Returns the last price in the history"
        if len(self._history) > 0:
            return self._history[-1][1]
        else:
            return None

    def prices(self):
        "Returns an iterator over all prices in the history"
        return map(lambda s: s[1], self._history)

    def returns(self):
        "Returns an iterator over all daily returns in the history"
        return map(lambda s: s[2], self._history)

    def symbol(self):
        return self._symbol

    def days(self):
        "Returns the number of days in the history"
        return len(self._history)

    def load_to_date(self, price_source, number, end_date=datetime.date.today()):
        self._history = [tuple for tuple in price_source.load_to_date(self._symbol, number, end_date=end_date)]

    def load_date_range(self, price_source, connection, start_date, end_date=datetime.date.today()):
        self._history = [tuple for tuple in price_source.load_date_range(self._symbol, start_date, end_date=end_date)]


class GroupHistory:

    def __init__ (self, symbols, history={}):
        self.symbols = list(history.keys())
        self.omitted_symbols = [s for s in symbols if s not in history.keys()]
        self.history = history
        self.history_days = 0
        self.first_date = None
        self.last_date = None
        self.common_dates = set()

    def common_dates(self):
        return self.common_dates

    def __repr__ (self):
        return 'GroupHistory(%r, %r)' % (self.symbols+self.omitted_symbols, self.history)

    def __getitem__ (self, item):
        return self.history[item]

    def load_to_date(self, price_source, number, end_date=datetime.date.today()):
        histories = []
        all_symbols = self.symbols+self.omitted_symbols
        self.symbols = []
        self.omitted_symbols = []
        self.common_dates = None
        
        for count, s in enumerate(all_symbols):
            x = SymbolHistory(s)
            x.load_to_date(price_source, max(number+7, int(1.3*number)), end_date)
            print("{0}: date range: {1} - {2}".format(s, x.first_date(), x.last_date()))
            
            if x.days() < number:
                print('*** Symbol {0} has only {1} days of history'.format(s, x.days()))
                self.omitted_symbols.append(s)
                
            elif x.last_date() == None or (end_date - x.last_date()).days > 7:
                print('*** Symbol {0} not up to date. Last date is {1}.'.format(s, x.last_date()))
                self.omitted_symbols.append(s)
                
            elif self.common_dates == None:
                self.common_dates = x.all_dates()
                self.symbols.append(s)
                histories.append(x)
            else:
                test = self.common_dates.intersection(x.all_dates())
                print("New range: {0} - {1}".format(min(test), max(test)))
                if len(test) < number:
                    print('*** Omitting symbol {0}: Only {1}/{2} overlapping dates.'.format(s, len(test), number))
                    print('*** Dates are {0}'.format(sorted(x.all_dates())))
                    self.omitted_symbols.append(s)
                else:
                    self.common_dates = test
                    self.symbols.append(s)
                    histories.append(x)

        self.common_dates = set(sorted(self.common_dates, reverse=True)[:number])
        print('Using selected dates from {0} to {1}'.format(min(self.common_dates), max(self.common_dates)))

        for h in histories:
            h.keep_only(self.common_dates)
            
        last_dates = [x.last_date() for x in histories if x.days()==number]
        if last_dates != []:
            self.last_date = max(last_dates)
            date_counts = {}
            for x in histories:
                if x.last_date() == self.last_date and x.days() == number:
                    date_counts[x.first_date()] = date_counts.get(x.first_date(), 0) + 1
            self.first_date = max(date_counts, key=lambda date: date_counts[date])
            self.history_days = number

            for x in histories:
                if x.days() == number and (x.first_date() != self.first_date or x.last_date() != self.last_date):
                    print ("Problem? symbol:{0} has {1} days, but first_date {2} != {3} or last_date {4} != {5}".format(x.symbol(), self.history_days, x.first_date(), self.first_date, x.last_date(), self.last_date, x.last_date()))
                    print(x)
        else:
            self.first_date = None
            self.last_date = None

        # Remove any symbol (and its history) if its first_date() doesn't match.
        self.omitted_symbols = [x.symbol() for x in histories
                                if x.first_date()!=self.first_date or x.last_date()!=self.last_date or x.days() != number]

        if len(self.omitted_symbols) > 0:
            print("Removing symbols with missing or outdated data: " + ", ".join(self.omitted_symbols))
            
        # Add "good" histories to dictionary (efficient only if "omitted_symbols" is short)
        self.history = {}
        for x in histories:
            if x.symbol() not in self.omitted_symbols:
                self.history[x.symbol()] = x

        self.symbols = [x.symbol() for x in histories if x.symbol() not in self.omitted_symbols]

    def last_date():
        return self.last_date

    def first_date():
        return self.first_date
                
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
