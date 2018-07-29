import argparse
from cvxopt import matrix
from sklearn import cross_validation
import datetime as dt
import json
import locale
import numpy
import portfolio
import pricehistory
import pricesource
import psycopg2
import optimal_allocation
import specialsampling
import sys

locale.setlocale(locale.LC_ALL,'')
today = dt.date.today()

parser = argparse.ArgumentParser(description='Optimize a portfolio.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument ('-c', '--use_current_symbols', action='store_true', help='optimize over current portfolio symbols')
parser.add_argument ('-s', '--slope', type=float, default=15, help="slope of line in variance-return plane having constant optimization penalty (smaller slope means greater return")
parser.add_argument ('portfolio', help='portfolio file name')

# Add a mutually exclusive group for the window
group = parser.add_mutually_exclusive_group()
group.add_argument ('-b', '--bootstrap', action='store_true', help='Use bootstrap samples instead of random splits')
group.add_argument ('-t', '--triangular', action='store_true', help='Use bootstrap samples from a triangular distribution.')

parser.add_argument ('-B', '--backtest', type=int, default=0, help='Pretend that now() is this many days ago')
parser.add_argument ('-m', '--max', type=float, default=1.0, help='Maximum allocation for any single equity.')
parser.add_argument ('-i', '--iterations', type=int, default=10000, help="number of sampling iterations")
parser.add_argument ('-d', '--days', type=int, default=756, help="number of days of history to use in training")
parser.add_argument ('-p', '--portfolio-size', type=int, default=10, help="number of symbols to keep in the portfolio")
parser.add_argument ('-o', '--output', type=argparse.FileType("w"), help="output portfolio file.")
args = parser.parse_args()

# with open("ameritrade-ira.pf", "w") as file:
#    current_pf.dump(json.dump, file)

end_date = today - dt.timedelta(days=args.backtest)

current_pf = portfolio.portfolio()
with open(args.portfolio, "r") as file:
    current_pf.load(json.load, file)

db_connection=psycopg2.connect(host="localhost",dbname="stocks",user="mwicks")
price_source=pricesource.StockDB(db_connection)
print("\nCurrent portfolio value = {0:10n}".format(current_pf.value(price_source, end_date)))

if args.bootstrap:
    sampler = cross_validation.Bootstrap
elif args.triangular:
    sampler = specialsampling.triangular
else:
    sampler = cross_validation.ShuffleSplit

if args.use_current_symbols:
    used_symbols = current_pf.symbols()
else:
    watch_list = pricehistory.watchList()
    watch_list.load(db_connection)

    print("Optimizing over all watch list symbols...")
    (allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                                   watch_list.symbols(),
                                                                                                   slope=args.slope,
                                                                                                   days=args.days,
                                                                                                   end_date=end_date,
                                                                                                   max_allocation=args.max,
                                                                                                   iters=args.iterations,
                                                                                                   sampler=sampler
                                                                                                   )
    print ('allocation:', allocation)
    sorted_allocation = sorted(allocation,key=lambda s: s[1], reverse=True)
    best_symbols = sorted([s[0] for s in sorted_allocation[0:args.portfolio_size]])
    print ("best_symbols = ", best_symbols)
    used_symbols = best_symbols

print ("Portfolio optimization over following symbols: {0}".format(used_symbols))

(allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                               used_symbols,
                                                                                               slope=args.slope,
                                                                                               days=args.days,
                                                                                               end_date=end_date,
                                                                                               iters=args.iterations,
                                                                                               max_allocation=args.max,
                                                                                               sampler=sampler
                                                                                               )

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

pf = portfolio.portfolio.from_allocation(price_source, sorted_allocation, current_pf.value(price_source, end_date), end_date)

print("\n Current portfolio: {0}".format(current_pf))
print("\nProposed portfolio: {0}".format(pf))
print("\n    Buy/Sell order: {0}".format(pf-current_pf))
print("\n   Buy/Sell values: {0}".format(sorted((pf-current_pf).values(price_source).items(), key=lambda s: s[1])))

if args.output:
    pf.dump(json.dump, args.output)
    
