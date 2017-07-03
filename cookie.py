# This comes from: https://github.com/sjev/trading-with-python/blob/master/scratch/get_yahoo_data.ipynb

import requests # interaction with the web
import os  #  file system operations
import yaml # human-friendly data format
import re  # regular expressions
# import pandas as pd # pandas... the best time series library out there
import datetime as dt # date and time functions
import io

# search with regular expressions

# "CrumbStore":\{"crumb":"(?<crumb>[^"]+)"\}

url = 'https://uk.finance.yahoo.com/quote/AAPL/history' # url for a ticker symbol, with a download link
r = requests.get(url)  # download page

txt = r.text # extract html


cookie = r.cookies['B'] # the cooke we're looking for is named 'B'
print('Cookie: ', cookie)

# Now we need to extract the token from html. 
# the string we need looks like this: "CrumbStore":{"crumb":"lQHxbbYOBCq"}
# regular expressions will do the trick!

pattern = re.compile('.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}')

for line in txt.splitlines():
    m = pattern.match(line)
    if m is not None:
        crumb = m.groupdict()['crumb']
        
        
print('Crumb=',crumb)

# create data directory in the user folder
dataDir = os.path.expanduser('.')

if not os.path.exists(dataDir):
    os.mkdir(dataDir)

# save data to YAML file
data = {'cookie':cookie,'crumb':crumb}

dataFile = os.path.join(dataDir,'yahoo_cookie.yml')

with open(dataFile,'w') as fid:
    yaml.dump(data,fid)

# Grab APL history as a test.
start=1230786000
end=1495252800
symbol="GOOG"

history_url = ( 'https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1={start}&period2={end}&interval=1d&events=history&crumb={crumb}'
                .format(**locals()) )
# history_url = ( 'https://query1.finance.yahoo.com/v7/finance/download/APL?period1={start}&period2={end}&interval=1d&events=history&crumb={crumb}'
#                 .format(**locals()) )

print('history_url', history_url)
r = requests.get(history_url, cookies={ 'B': cookie})
print('text: ', r.text, '\n')
