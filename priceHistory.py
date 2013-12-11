import numpy
import datetime

class symbolHistory:

    def __init__(self, symbol, history=[]):
        "history should be a list of tuples (date, price) with most recent date last"
    	self.symbol = symbol
        self.history = history
        
    def __repr__ (self):
        return 'symbolHistory("%s", %r)' % (self.symbol, self.history)

    def first_date (self):
        if len(self.history) > 0:
            return self.history[0][0]
        else:
            return None

    def last_date (self):
        if len(self.history) > 0:
            return self.history[-1][0]
        else:
            return None

    def first_price (self):
        return self.history[0][1]

    def last_price (self):
        return self.history[-1][1]

    def prices (self):
        return [element[1] for element in self.history]

    def returns (self):
        return [element[2] for element in self.history]

    def days (self):
        return len(self.history)

    def load_to_date (self, connection, number, end_date=datetime.date.today()):
        cursor = connection.cursor()
        cursor.execute("SELECT h.date,h.close,h.daily_return "
                        " FROM symbols s LEFT JOIN history h "
                          " ON (s.id = h.symbol_id) "
                       " WHERE s.symbol = %s "
                       "   AND h.date <= %s "
                       " ORDER by h.date DESC "
                       " LIMIT %s ",
                       (self.symbol, end_date, number))
        self.history = cursor.fetchall()
        self.history.reverse()
        return self

    def load_date_range (self, connection, start_date, end_date=datetime.date.today()):
        cursor = connection.cursor()
        cursor.execute("SELECT h.date,h.close,h.daily_return "
                        " FROM symbols s LEFT JOIN history h "
                          " ON (s.id = h.symbol_id) "
                       " WHERE s.symbol = %s "
                       "   AND h.date >= %s "
                       "   AND h.date <= %s "
                       " ORDER by h.date ",
                       (self.symbol, start_date, end_date))
        self.history = cursor.fetchall()
        return self

class groupHistory:

    def __init__ (self, symbols, history={}):
        self.symbols = history.keys()
        self.omitted_symbols = [s for s in symbols if s not in history.keys()]
        self.history = history
        self.history_days = 0

    def __repr__ (self):
        return 'groupHistory(%r, %r)' % (self.symbols+self.omitted_symbols, self.history)

    def __getitem__ (self, item):
        return self.history[item]

    def load_to_date(self, connection, number, end_date=datetime.date.today()):
        histories = []
        for x in map(symbolHistory, self.symbols+self.omitted_symbols):
        	x.load_to_date(connection, number, end_date)
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
            print "Removing symbols with missing or outdated data: " + ", ".join(self.omitted_symbols)
            
        # Add "good" histories to dictionary (efficient only if "omitted_symbols" is short)
        self.history = {}
        for x in histories:
            if x.symbol not in self.omitted_symbols:
                self.history[x.symbol] = x

        self.symbols = [x.symbol for x in histories if x.symbol not in self.omitted_symbols]
                
    def matrix_of_returns(self):
        result = numpy.empty([len(self.symbols), self.history_days])
        for i in range(len(self.symbols)):
            result[i] = self.history[self.symbols[i]].returns()
        return result


class watchList:
    def __init__(self, list=[]):
        self.list = list

    def load(self,connection):
        cursor = connection.cursor()
        cursor.execute("SELECT s.symbol,s.id " + 
                       " FROM watch_list w LEFT JOIN symbols s "
                       " ON (s.id = w.symbol_id) "
                       " ORDER by s.symbol")
        self.list = cursor.fetchall()

    def symbols(self):
        return [s[0] for s in self.list]

    def __repr__ (self):
        return 'watchList(%r)' % (self.list)
