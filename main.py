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

locale.setlocale(locale.LC_ALL,'')

virtual_pf_20140112 = portfolio.portfolio ([('BZQ', 304),
                                   ('FXF', 159), 
                                   ('FXG', 752),
                                   ('LBND', 322),
                                   ('RXL', 583),
                                   ('TYD', 753),
                                   ('UGA', 210),
                                   ('UGE', 195),
                                   ('YCS', 292)])

ameritrade_pf_20140112 = portfolio.portfolio ([('EDV', 227),
                                               ('EUO', 667),
                                               ('FXH', 1494),
                                               ('QLD', 220),
                                               ('TYD', 1428),
                                               ('XLP', 1749)],
                                              10993.81)

ameritrade_pf_20140113 = portfolio.portfolio ([('BZQ', 305),
                                      ('FXF', 149),
                                      ('FXG', 731),
                                      ('RXL', 556),
                                      ('TYD', 767),
                                      ('UGA', 186),
                                      ('UGE', 185),
                                      ('YCS', 306)],
                                     64734.48+10933.81)

ameritrade_pf_20140114 = portfolio.portfolio ([('BZQ', 395),
                                      ('FXF', 189),
                                      ('FXG', 731),
                                      ('RXL', 556),
                                      ('TYD', 993),
                                      ('UGA', 237),
                                      ('UGE', 185),
                                      ('YCS', 306)],
                                     41250.50+10933.81)

ameritrade_pf_20140115 = portfolio.portfolio ([('BZQ', 395),
                                      ('FXF', 189),
                                      ('FXG', 958),
                                      ('LBND', 441),
                                      ('RXL', 754),
                                      ('TYD', 993),
                                      ('UGA', 237),
                                      ('UGE', 240),
                                      ('YCS', 306)],
                                     10993.81-2354.15)

ameritrade_pf_20140116 = portfolio.portfolio ([('BZQ', 395),
                                      ('FXF', 189),
                                      ('FXG', 958),
                                      ('LBND', 441),
                                      ('RXL', 754),
                                      ('TYD', 993),
                                      ('UGA', 237),
                                      ('UGE', 240),
                                      ('YCS', 414)],
                                     10993.82-9856.10)

ameritrade_pf_20140201 = portfolio.portfolio ([('BZQ', 340),
                                      ('FXF', 189),
                                      ('FXG', 958),
                                      ('LBND', 441),
                                      ('RXL', 754),
                                      ('TYD', 1171),
                                      ('UGA', 237),
                                      ('UGE', 240),
                                      ('YCS', 414)],
                                     1137.80-1107.67)

ameritrade_pf_20140204 = portfolio.portfolio ([('BZQ', 340),
                                      ('FXF', 189),
                                      ('FXG', 815),
                                      ('LBND', 370),
                                      ('RXL', 846),
                                      ('TYD', 1171),
                                      ('UGA', 237),
                                      ('UGE', 240),
                                      ('YCS', 414)],
                                     1137.80-1368.03)

ameritrade_pf_20140212 = portfolio.portfolio ([('BZQ', 373),
                                      ('FXF', 189),
                                      ('FXG', 815),
                                      ('LBND', 370),
                                      ('RXL', 787),
                                      ('TYD', 1171),
                                      ('UGA', 237),
                                      ('UGE', 240),
                                      ('YCS', 414)],
                                     1887.64-0.0)

current_pf = ameritrade_pf_20140212
with open("ameritrade-after-tax.pf", "w") as file:
    current_pf.dump(json.dump, file)

db_connection=psycopg2.connect(host="nas.wicksnet.us",dbname="stocks",user="mwicks")
price_source=pricesource.StockDB(db_connection)

print("Current portfolio value = {0:10n}".format(current_pf.value(price_source)))

watch_list = pricehistory.watchList()
watch_list.load(db_connection)

current_pf_symbols = current_pf.symbols()

slope=15
iters=10000
print("Optimizing over all watch list symbols...")
# (allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
#                                                                                               watch_list.symbols(),
#                                                                                               slope=slope,
#                                                                                               days=750,
#                                                                                               end_date=datetime.date(2099,1,1),
#                                                                                               iters=iters)
#sorted_allocation = sorted(allocation,key=lambda s: s[1], reverse=True)

#best_symbols = sorted([s[0] for s in sorted_allocation[0:10]])
#print ("best_symbols = ", best_symbols)

# CHANGE ME
# CHANGE ME
# CHANGE ME
kept_symbols = current_pf_symbols
print ("using symbols = ", kept_symbols)

print("Optimizing over top 10 symbols...")
(allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
                                                                                               kept_symbols,
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
print(sorted_allocation[0:10])

pf = portfolio.portfolio.from_allocation(price_source, sorted_allocation, current_pf.value(price_source))

print(" Current portfolio: {0!r}".format(current_pf))
print("Proposed portfolio: {0!r}".format(pf))
print("    Buy/Sell order: {0!r}".format((pf-current_pf)))
print("   Buy/Sell values: {0!r}".format((pf-current_pf).values(price_source)))
