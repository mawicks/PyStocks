import argparse
import datetime
from cvxopt import matrix
import json
import locale
import numpy
import portfolio
import pricehistory
import pricesource
import psycopg2
import optimal_allocation
import sys

locale.setlocale(locale.LC_ALL,'')

current_pf = portfolio.portfolio()

def usage():
    print ("{0} <portfolio_filename>".format(sys.argv[0]))
    sys.exit()

if len(sys.argv) < 2:
    usage()

parser = argparse.ArgumentParser(description='Optimize a portfolio.')
parser.add_argument ('-c', '--use_current_symbols', action='store_true', help='Optimize over current portfolio symbols')
parser.add_argument ('portfolio', help='Portfolio file name')
args = parser.parse_args()

# with open("ameritrade-ira.pf", "w") as file:
#    current_pf.dump(json.dump, file)

with open(args.portfolio, "r") as file:
    current_pf.load(json.load, file)

db_connection=psycopg2.connect(host="nas.wicksnet.us",dbname="stocks",user="mwicks")
price_source=pricesource.StockDB(db_connection)
print("Current portfolio value = {0:10n}".format(current_pf.value(price_source)))

slope=15
iters=10000

if args.use_current_symbols:
    used_symbols = current_pf.symbols()
else:
    watch_list = pricehistory.watchList()
    watch_list.load(db_connection)

    print("Optimizing over all watch list symbols...")
    (allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                                   watch_list.symbols(),
                                                                                                   slope=slope,
                                                                                                   days=750,
                                                                                                   end_date=datetime.date(2099,1,1),
                                                                                                   iters=iters)

    sorted_allocation = sorted(allocation,key=lambda s: s[1], reverse=True)
    best_symbols = sorted([s[0] for s in sorted_allocation[0:10]])
    print ("best_symbols = ", best_symbols)

    used_symbols = best_symbols

print ("Portfolio optimization over following symbols: {0}".format(used_symbols))

(allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                               used_symbols,
                                                                                               slope=slope,
                                                                                               days=750,
                                                                                               end_date=datetime.date(2099,1,1),
                                                                                               iters=iters)

print("Done.")

print("slope={0}; iters={1}".format(slope,iters))
print("Mean/Std of optimal returns = {0}/{1}".format(numpy.mean(opt_returns),
                                                   numpy.std(opt_returns)))
print("Mean/Std of optimal volatilities = {0}/{1}".format(numpy.mean(opt_vols),
                                                          numpy.std(opt_vols)))
print("Mean/Std of cross-returns = {0}/{1}".format(numpy.mean(cross_val_returns),
                                                   numpy.std(cross_val_returns)))

sorted_allocation = sorted(allocation,key=lambda s: s[1], reverse=True)
print(sorted_allocation)

pf = portfolio.portfolio.from_allocation(price_source, sorted_allocation, current_pf.value(price_source))

print(" Current portfolio: {0}".format(current_pf))
print("Proposed portfolio: {0}".format(pf))
print("    Buy/Sell order: {0}".format(pf-current_pf))
print("   Buy/Sell values: {0}".format((pf-current_pf).values(price_source)))
