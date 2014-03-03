import datetime
import math
import decimal
import numpy
import random

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)

class TestSource:
   def load_date_range(self, symbol, start_date, end_date=datetime.date.today()):
       """Generate deterministic test data using the three characters in the symbol as parameters for the generator

       The prices returned are always the same for the same symbol and
       the same start_date.  Do not expect the prices to be the same
       if an entire range is fetched at once and then fetched on day
       at a time.
       
       The first character of the symbol determines the price on
       'start_date'.  'A' has a price of 50, and the price increased
       by 5 for each subsequent letter of the alphabet.

       The second character of the symbol specifies the rate of return,
       'rate'. 'A' has a daily return of -0.001.  Each subsequent
       letter of the alphabet increased the daily return by 0.0002,
       i.e., 'B' has a daily return of -0.0008, etc.  'F' has a return
       of 0 and 'Z' has a return of .0040.
       

       The third character of the symbol sets the MAXIMUM variation
       in the daily return.  'A' has a variation of 0; 'B' has a max
       variation of 0.01; 'C' has a maximum variation of .02, etc.
       
       The fourth character of the symbol sets the frequency of
       variation in the daily return.  The variation is actually the
       sum of two sinusoids to provide some correlation between
       Adjacent characters.  Symbols with a third symbol of 'C' will
       be correlated with those having a third symbol of 'D'.  Symbols
       with a third symbol of 'D' will be correlated with those having
       a symbol of 'E', etc.  There is no way to generate uncorrelated
       symbols.  The frequency corresponding to 'A' is nonzero because
       a zero frequency would affect the average daily rate of return.
       Because of the sinusoid, there will be day-to-day correlations
       (unlike real stock prices)
       """

# Ensure there are at least three characters in the symbol.    

       symbol = symbol.upper() + 'AAAA'

       price = 50 + 5 * (ord(symbol[0])-ord('A'))
       rate = -0.001 + 0.0002 * (ord(symbol[1])-ord('A'))
       sigma = 0.010 * (ord(symbol[2])-ord('A'))
       freq = 1 + ord(symbol[2])-ord('A')

       d = range(int((end_date-start_date).days))

       returns = [0] + list(map(lambda r: rate + 0.5*sigma*(math.sin(freq*100*r) + math.sin((freq+1)*100*r)), d))
#       returns = [0] + list(map(lambda r: rate + sigma*random.normalvariate(0.0,1.0), d))
       cumreturns = numpy.cumsum(returns)

       prices = [ decimal.Decimal(price*math.exp(r)).quantize(decimal.Decimal('.01')) for r in cumreturns ]
       dates = [date for date in daterange(start_date, end_date)]
       return zip(dates, prices, returns)

   def load_to_date(self, symbol, number, end_date=datetime.date.today()):
       """See the documentation for load_date_range() because the implementation of load_to_date()
       
       load_to_date() will return the same prices for the same symbol for the same start date.
       However, the start date is not a parameter and is implied by number and end_date.

       Note that load_to_date() will not return the same prices for
       the same symbol and end_date for different values for 'number'
       """

       start_date = end_date - datetime.timedelta(number-1)
       return self.load_date_range(symbol, start_date, end_date)
       

