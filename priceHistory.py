import numpy

class symbolHistory:

    def __init__(self, symbol, history=[]):
        "history should be a list of tuples (date, price)"
    	self.symbol = symbol
        self.history = history
        
    def __repr__ (self):
        return 'symbolHistory("%s", %r)' % (self.symbol, self.history)

    def first_date (self):
        if len(self.history) > 0:
            return min([element[0] for element in self.history])
        else:
            return None

    def last_date (self):
        if len(self.history) > 0:
            return max([element[0] for element in self.history])
        else:
            return None

    def prices (self):
        return [element[1] for element in sorted(self.history,key=lambda e: e[0])]

    def returns (self):
        return [element[2] for element in sorted(self.history,key=lambda e: e[0])]

    def days (self):
        return len(self.history)

    def load_to_date (self, connection, end_date, number):
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
        return self

    def load_date_range (self, connection, start_date, end_date):
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

    def __init__ (self, symbols, history=[]):
        self.symbols = symbols
        self.omitted_symbols = []
        self.history = history
        self.history_count = 0

        def __repr__ (self):
            return 'groupHistory(%r, %r)' % (self.symbols, self.history)

    def load_to_date(self, connection, end_date, number):
        histories = [x.load_to_date(connection, end_date, number) 
                     for x in map(symbolHistory, self.symbols+self.omitted_symbols)]

        if len(histories) > 0:
            first_date = max([x.first_date() for x in histories if x.days()==number])
            last_date = max([x.last_date() for x in histories if x.days()==number])
            self.history_count = number
        else:
            first_date = None
            last_date = None

        # Remove any symbol (and its history) if its first_date() doesn't match.
        self.omitted_symbols = [x.symbol for x in histories
                                if x.first_date()!=first_date or x.last_date()!=last_date]

        if len(self.omitted_symbols) > 0:
            print "Removing symbols with missing or outdated data: " + ", ".join(self.omitted_symbols)
            
        # Return good histories (efficient only if "missing" is short)
        self.history = [x for x in histories if x.symbol not in self.omitted_symbols]

        self.symbols = [x.symbol for x in self.history]
        return self.history

    def matrix_of_returns(self):
        result = numpy.empty([len(self.symbols), self.history_count])
        for i in range(len(self.symbols)):
            result[i] = self.history[i].returns()
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
