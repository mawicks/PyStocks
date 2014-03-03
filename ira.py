import datetime
from cvxopt import matrix
import psycopg2
import locale
import numpy
import portfolio
import pricehistory
import pricesource
import optimal_allocation

locale.setlocale(locale.LC_ALL,'')

pf_2014_02_11 = portfolio.portfolio ([('RXL',731),
				   ('TYD',1619),
				   ('UGE',327)],
                                  229683)

pf_2014_02_12 = portfolio.portfolio ([('LBND', 578),
				      ('RXL',731),
				      ('TYD',1619),
				      ('UGA',459),
				      ('UGE',327)],
                                      377979.58-195004.77)

pf_2014_02_13 = portfolio.portfolio ([('BZQ',200),
				      ('LBND',578),
				      ('RXL',731),
				      ('TYD',1619),
				      ('UGA',459),
				      ('UGE',327),
				      ('XLV',750),
				      ('YCS',300)],
                                      229663.17-128999.79)

pf_2014_02_14 = portfolio.portfolio ([('BZQ',200),
				      ('EDV',269),
				      ('LBND',578),
				      ('RXL',731),
				      ('TYD',1619),
				      ('UGA',459),
				      ('UGE',327),
				      ('XLV',1456),
				      ('YCS',300)],
                                      100663.54-66548.05)

pf_2014_02_18 = portfolio.portfolio ([('BZQ',200),
				      ('EDV',269),
				      ('LBND',578),
				      ('QLD',147),
				      ('RXL',731),
				      ('TYD',1216),
				      ('UGA',459),
				      ('UGE',327),
				      ('XLV',1456),
				      ('YCS',300)],
                                      64313.55-40577.93)

pf_2014_02_19 = portfolio.portfolio ([('BZQ',600),
				      ('EDV',354),
				      ('LBND',423),
				      ('QLD',147),
				      ('RXL',731),
				      ('TYD',1494),
				      ('UGA',306),
				      ('UGE',419),
				      ('XLV',1809),
				      ('YCS',606)],
                                      972.99+2055.58)
current_pf = pf_2014_02_19
used_symbols = [ 'BZQ', 'EDV', 'LBND', 'RXL', 'TYD', 'UGA', 'UGE', 'XLV', 'YCS', 'QLD' ]

db_connection=psycopg2.connect(host="nas.wicksnet.us",dbname="stocks",user="mwicks")
price_source=pricesource.StockDB(db_connection)
print("Current portfolio value = {0:10n}".format(current_pf.value(price_source)))

watch_list = pricehistory.watchList()
watch_list.load(db_connection)

slope=15
iters=10000
#print("Optimizing over all watch list symbols...")
#(allocation, opt_returns, opt_vols, cross_val_returns) = optimal_allocation.optimal_allocation(price_source,
#                                                                                               watch_list.symbols(),
#                                                                                               slope=slope,
#                                                                                               days=750,
#                                                                                               end_date=datetime.date(2099,1,1),
#                                                                                               iters=iters)

#sorted_allocation = sorted(allocation,key=lambda s: s[1], reverse=True)
#best_symbols = sorted([s[0] for s in sorted_allocation[0:10]])
#print ("best_symbols = ", best_symbols)

print ("desired_symbols = ", used_symbols)

print("Optimizing over top 10 symbols...")
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

print(" Current portfolio: {0}".format(current_pf)
print("Proposed portfolio: {0}".format(pf)
print("    Buy/Sell order: {0}".format(pf-current_pf)
print("   Buy/Sell values: {0}".format((pf-current_pf).values(price_source))
