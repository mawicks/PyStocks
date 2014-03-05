import argparse
from cvxopt import matrix
import datetime
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

parser = argparse.ArgumentParser(description='Optimize a portfolio.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument ('-c', '--use_current_symbols', action='store_true', help='optimize over current portfolio symbols')
parser.add_argument ('-s', '--slope', default=15, help="slope of line in variance-return plane having constant optimization penalty (smaller slope means greater return")
parser.add_argument ('-i', '--iterations', default=10000, help="number of sampling iterations")
parser.add_argument ('portfolio', help='portfolio file name')
args = parser.parse_args()

# with open("ameritrade-ira.pf", "w") as file:
#    current_pf.dump(json.dump, file)

current_pf = portfolio.portfolio()
with open(args.portfolio, "r") as file:
    current_pf.load(json.load, file)

db_connection=psycopg2.connect(host="nas.wicksnet.us",dbname="stocks",user="mwicks")
price_source=pricesource.StockDB(db_connection)
print("Current portfolio value = {0:10n}".format(current_pf.value(price_source)))

if args.use_current_symbols:
    used_symbols = current_pf.symbols()
else:
    watch_list = pricehistory.watchList()
    watch_list.load(db_connection)

    print("Optimizing over all watch list symbols...")
    (allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                                   watch_list.symbols(),
                                                                                                   slope=args.slope,
                                                                                                   days=750,
                                                                                                   end_date=datetime.date(2099,1,1),
                                                                                                   iters=args.iterations)

    sorted_allocation = sorted(allocation,key=lambda s: s[1], reverse=True)
    best_symbols = sorted([s[0] for s in sorted_allocation[0:10]])
    print ("best_symbols = ", best_symbols)

    used_symbols = best_symbols

print ("Portfolio optimization over following symbols: {0}".format(used_symbols))

(allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                               used_symbols,
                                                                                               slope=args.slope,
                                                                                               days=750,
                                                                                               end_date=datetime.date(2099,1,1),
                                                                                               iters=args.iterations)

print("Done.")

print("slope={0}; iters={1}".format(args.slope,args.iterations))
print("Mean/Std of optimal returns = {0}/{1}".format(numpy.mean(opt_returns),
                                                   numpy.std(opt_returns)))
print("Mean/Std of optimal volatilities = {0}/{1}".format(numpy.mean(opt_vols),
                                                          numpy.std(opt_vols)))
print("Mean/Std of cross-returns = {0}/{1}".format(numpy.mean(cross_val_returns),
                                                   numpy.std(cross_val_returns)))

sorted_allocation = sorted(allocation,key=lambda s: s[1], reverse=True)
print(sorted_allocation)

pf = portfolio.portfolio.from_allocation(price_source, sorted_allocation, current_pf.value(price_source))

print("\n Current portfolio: {0}".format(current_pf))
print("\nProposed portfolio: {0}".format(pf))
print("\n    Buy/Sell order: {0}".format(pf-current_pf))
print("\n   Buy/Sell values: {0}".format(sorted((pf-current_pf).values(price_source).items(), key=lambda s: s[1])))
