import argparse
from cvxopt import matrix
from sklearn import cross_validation
import datetime
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
today = datetime.date.today()

parser = argparse.ArgumentParser(description='Optimize a portfolio.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument ('-c', '--use_current_symbols', action='store_true', help='optimize over current portfolio symbols')
parser.add_argument ('-s', '--slope', type=int, default=15, help="slope of line in variance-return plane having constant optimization penalty (smaller slope means greater return")
parser.add_argument ('portfolio', help='portfolio file name')
group = parser.add_mutually_exclusive_group()
group.add_argument ('-b', '--bootstrap', action='store_true', help='Use bootstrap samples instead of random splits')
group.add_argument ('-t', '--triangular', action='store_true', help='Use bootstrap samples from a triangular distribution.')

parser.add_argument ('-i', '--iterations', type=int, default=500, help="number of sampling iterations")
parser.add_argument ('-d', '--days', type=int, default=756, help="number of days of history to use in training")
parser.add_argument ('-p', '--portfolio-size', type=int, default=10, help="number of symbols to use in portfolio")
args = parser.parse_args()

# with open("ameritrade-ira.pf", "w") as file:
#    current_pf.dump(json.dump, file)

current_pf = portfolio.portfolio()
with open(args.portfolio, "r") as file:
    current_pf.load(json.load, file)

db_connection=psycopg2.connect(host="nas.wicksnet.us",dbname="stocks",user="mwicks")
price_source=pricesource.StockDB(db_connection)
print("Current portfolio value = {0:10n}".format(current_pf.value(price_source)))

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

    n = 0
    cumulative_return = 0

    for days_ago in reversed(range(0,4*365)):
        history = pricehistory.GroupHistory(watch_list.symbols())
        end_date = today-datetime.timedelta(days_ago)
        history.load_to_date(price_source, 1, end_date)

        if history.last_date == end_date:
            print("Optimizing over all watch list symbols...")
            (allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                                           watch_list.symbols(),
                                                                                                           slope=args.slope,
                                                                                                           days=args.days,
                                                                                                           end_date=end_date-datetime.timedelta(1),
                                                                                                           iters=100,
                                                                                                           sampler=sampler)
            sorted_allocation = sorted(allocation,key=lambda s: s[1], reverse=True)
            best_symbols = sorted([s[0] for s in sorted_allocation[0:args.portfolio_size]])
            print ("best_symbols = ", best_symbols)
        
            used_symbols = best_symbols

            print ("Portfolio optimization over following symbols: {0}".format(used_symbols))

            history = pricehistory.GroupHistory(used_symbols)
            (allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                                           used_symbols,
                                                                                                           slope=args.slope,
                                                                                                           days=args.days,
                                                                                                           end_date=end_date-datetime.timedelta(1),
                                                                                                           iters=args.iterations,
                                                                                                           sampler=sampler)
            history.load_to_date(price_source, 1, end_date)
            # Return row vector of returns
            all_returns = history.matrix_of_returns().T

            print("All returns: {0}".format(all_returns))

            print("allocation: {0}".format(numpy.matrix([x[1] for x in allocation]).T))
            actual_return = all_returns * numpy.matrix([x[1] for x in allocation]).T

            cumulative_return = cumulative_return + float(actual_return)
            n += 1

            print("*******Day {0} is {1} --- Return: {2}".format(n, end_date, 252*float(actual_return)))
            print("*******Avg return: {0}".format(252*cumulative_return/n))
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
    
