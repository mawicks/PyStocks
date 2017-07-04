from collections import namedtuple

import requests # interaction with the web
import os  #  file system operations
import datetime
from math import log, exp, copysign
import time
import io
import psycopg2

# Google adjusts all of the prices for splits, but
# some web reports say they don't adjust for dividends.
# Examining stock prices on dividend dates seems to confirm this.
# Yahoo's adjusted price and Google's adjusted
# prices do not agree and Yahoo clearly claims to adjust both for stock splits
# and dividends. 
#
# Google doesn't explain what they do, and not having actual prices
# and not having dividend adjustments makes Google's historical data
# less useful than Yahoo's.  Yahoo's updates their data later in the 
# evening than Google.
#
# Note: Because of stock splits and dividends, prices must be back adjusted.
# In other words, "historical" prices downloaded today will change because
# of future dividends.  Yahoo provides raw data, so user adjustment is possible.
# Yahoo's data also makes it possible to determine the dates of dividends
# and stock splits.

# For the time being, Yahoo is preferable.  However, here is how the Google
# URLs are formed:

#url_base = "http://finance.google.com/finance/historical";
#url_symbol_query = "q=Goog";
#url_date_range = "startdate=2011-01-01";
#url = "{url_base}?{url_symbol_query}&{url_date_range}&output=csv";

cookie = 'chjcoh1cl38jp&b=3&s=dv'
cookies = {'B': cookie}
crumb = 'b3OtsEsShyY'
    
def historyURL(symbol, startdate = None, enddate = datetime.date.today()):
    '''
    Generates a url to download stock history from Yahoo
    from startDate to endDate inclusive.
    '''
    start = int(time.mktime(startdate.timetuple())) if startdate != None else 0
    end = int(time.mktime(enddate.timetuple()))
    
    result = ( 'https://query1.finance.yahoo.com/v7/finance/download/{symbol}?'
               'period1={start}&period2={end}&interval=1d&events=history&crumb={local_crumb}'
               .format(symbol=symbol, start=start, end=end, local_crumb=crumb) )

    return result


def getSymbolID(symbol):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT id FROM symbols WHERE symbol = %s LIMIT 1", (symbol,))
        result = cursor.fetchone()

    if result == None:
        print('Symbol {0} not in table.'.format(symbol))
        return None
    else:
        print('getSymbolID returning: {0}'.format(result[0]))
        return result[0]

deleteHistoryTemplate = ( "DELETE FROM history WHERE symbol_id = %s AND date = %s" )
insertHistoryTemplate = ( "INSERT INTO history "
                          "(symbol_id,date,high,low,open,close,volume,adjusted_close,daily_return,source)"
                          " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'Yahoo!')" );

def updateHistoryRecord(symbol_id, history_record, daily_return, overwrite=False):
    if abs(history_record.AdjClose) > 99999.99:
        adjusted_close = copysign(99999.99, history_record.AdjClose)
        print('Adjusted close value {0} for symbol_id {1} is out of range. Set to {2}'
              .format(history_record.AdjClose, symbol_id, adjusted_close))
    else:
        adjusted_close = history_record.AdjClose

    with db_connection.cursor() as cursor:
        if overwrite:
            cursor.execute(deleteHistoryTemplate, (symbol_id, history_record.Date))
        cursor.execute(insertHistoryTemplate, (symbol_id,
                                               history_record.Date,
                                               history_record.High,
                                               history_record.Low,
                                               history_record.Open,
                                               history_record.Close,
                                               history_record.Volume,
                                               adjusted_close,
                                               daily_return))
        
updateLatestHistoryDateTemplate = "UPDATE symbols SET latest_history_date=%s WHERE id=%s"
updateEarliestHistoryDateTemplate = "UPDATE symbols SET earliest_history_date=%s WHERE id=%s"
getHistoryRangeTemplate = "SELECT earliest_history_date, latest_history_date FROM symbols WHERE id=%s LIMIT 1"

def as_float(s):
    result = s
    try:
        result = float(s)
    except:
        pass
    return result

def getHistoryRange(symbolID):
#    print('getHistoryRange({0})'.format(symbolID))
    with db_connection.cursor() as cursor:
        cursor.execute(getHistoryRangeTemplate, (symbolID,))
        result = cursor.fetchone()
#    print('\treturning: {0}'.format(result))or
    return result

def parseHistory(content, startdate):
    '''parseHistory converts the content retrieves from a web service into a sequence of named tuples.  Record order remains unchanged.'''
    for count, record in enumerate(content.split('\n')):
        if len(record) == 0:
            continue
        fields = record.strip().split(',')
        if count == 0:
            header = map(lambda s: s.replace(' ', ''), fields)
            history_type = namedtuple('History', header)
        else:
            history_record = history_type(*map(as_float, fields))
            if (not isinstance(history_record.Close, float) or
                not isinstance(history_record.AdjClose, float) or
                history_record.Close == 0.0 or
                history_record.AdjClose == 0.0):
                continue
            try:
                date = datetime.datetime.strptime(history_record.Date, "%Y-%m-%d").date()
            except Exception as e:
                print(e)
                print('Input record: {0}'.format(fields))
                raise(e)

            # Correct deficiences in Yahoo's API
            if startdate != None and date < startdate:
                continue
            
            yield history_record._replace(Date=date)
            
# Synopsis:  updateSymbolHistory symbol previousUpdateDate endDate
# Note: previousUpdateDate must precede endDate and should be a trading day.
# Closing prices for days after "previousUpdateDate" will be downloaded and stored,
# but prices on "previousUpdateDate" will not.  The values from "previousUpdateDate"
# are used to determine whether the closing price was adjusted on
# following trading day due to dividends or stock splits, but not saved in the
# database.  Presumably theses values were saved earlier.
def updateSymbolHistory(symbol, overwrite=False):
    symbolID = getSymbolID(symbol)
    if symbolID == None:
        print('Symbol {0} not found'.format(symbol))
        return

    if overwrite:
        previousEarliestDate, previousLatestDate = None, None
    else:
        previousEarliestDate, previousLatestDate = getHistoryRange(symbolID)

    print("downloading {0} from {1} to today...".format(symbol, previousLatestDate if previousLatestDate else "the beginning"))

    url = historyURL(symbol, previousLatestDate)
    print('trying url: {0}'.format(url))
    response = requests.get(url, cookies=cookies)
    
    if not response.ok:
        print("***History for symbol {0} not available ***".format(symbol))
        print('\thttp response code: {0}'.format (response.status_code))
        return

    # Sometimes Yahoo returns duplicate records for the same date.  Try to choose a sort order
    # that places the "right" record first
    history = sorted(parseHistory(response.text, previousLatestDate), key=lambda h: (h.Date, h.Volume, -h.Close))
    if len(history) == 0:
        print("No history")
        count = 0
        
    for count, current in enumerate(history):
        if count < 2:
            print(current)
            
        if count == 0:
            earliestDate = current.Date
        else:
            days = (current.Date - previous.Date).days
            # Sometimes Yahoo returns duplicate records for the same date.  Ignore subsequent records.
            if days == 0:
                continue
            try:
                # Yahoo sometimes returns incorrect adjusted close prices.  Try to detect
                # this and use the regular close price instead.
                if ( current.AdjClose <= 0.0 or
                     previous.AdjClose <= 0.0 or
                     current.AdjClose > 99999.99 or
                     previous.AdjClose > 99999.99 ):
                    daily_return = log(current.Close/previous.Close) / days
                else:
                    daily_return = log(current.AdjClose/previous.AdjClose) / days
                        
            except Exception as e:
                print(e)
                print('current: {0}, previous: {1}'.format(current, previous))
                raise(e)
                
            updateHistoryRecord(symbolID, current, daily_return, overwrite)

        previous = current
            
    if count > 0:
        print("Added {0} new record{1}".format(count, "s" if count > 1 else ""))
        print('Updating summary record for {0} to show history from {1} to {2}'
              .format(symbolID,
                      previousEarliestDate if previousEarliestDate != None else earliestDate,
                      current.Date))
        with db_connection.cursor() as cursor:
            cursor.execute(updateLatestHistoryDateTemplate, (current.Date, symbolID))
            if previousEarliestDate == None:
                cursor.execute(updateEarliestHistoryDateTemplate, (earliestDate, symbolID))
                
getWatchList = ( "SELECT symbol FROM symbols s,watch_list w "
                 " WHERE s.id = w.symbol_id "
		 "   AND (s.latest_history_date < (CURRENT_DATE-1) OR "
		 "     s.latest_history_date is null )" )

def updateWatchListHistory(overwrite=False):
    with db_connection.cursor() as cursor:
        cursor.execute(getWatchList)
        for (result,) in cursor.fetchall():
            updateSymbolHistory(result, overwrite)
            time.sleep(1)

overwrite = False
if __name__ == "__main__":
    with psycopg2.connect(host="localhost",dbname="stocks",user="mwicks") as db_connection:
        updateWatchListHistory(overwrite)
