import datetime

class StockDB:
    def __init__(self, connection):
        self.connection = connection

    def load_to_date(self, symbol, number, end_date=datetime.date.today()):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT h.date,h.close,h.daily_return "
                           " FROM symbols s LEFT JOIN history h "
                           " ON (s.id = h.symbol_id) "
                           " WHERE s.symbol = %s "
                           "   AND h.date <= %s "
                           " ORDER by h.date DESC "
                           " LIMIT %s ",
                           (symbol, end_date, number))
            result = tuple(reversed(cursor.fetchall()))
        return result
        
    def load_date_range(self, symbol, start_date, end_date=datetime.date.today()):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT h.date,h.close,h.daily_return "
                           " FROM symbols s LEFT JOIN history h "
                           " ON (s.id = h.symbol_id) "
                           " WHERE s.symbol = %s "
                           "   AND h.date >= %s "
                           "   AND h.date <= %s "
                           " ORDER by h.date ",
                           (symbol, start_date, end_date))
            result = cursor.fetchall()
        return result
