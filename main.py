import datetime
from cvxopt import matrix
from cvxopt.solvers import qp
from cvxopt.solvers import options as solver_options
import psycopg2
import priceHistory
import numpy

solver_options['show_progress'] = False

conn=psycopg2.connect(host="nas.wicksnet.us",dbname="stocks",user="mwicks")

watch_list = priceHistory.watchList()
watch_list.load(conn)

history = priceHistory.groupHistory(watch_list.symbols())
#history = priceHistory.groupHistory(['DDM', 'EDV', 'EUO', 'FXF', 'FXG', 'FXH', 'GLD', 'QLD', 'SIVR', 'SMB', 'SPY', 'TYD', 'XLP' ])
history = priceHistory.groupHistory(['FXF', 'FXH', 'GLD', 'QLD' ])
history = priceHistory.groupHistory(['RXL', 'GLD', 'QLD', 'SPXL', 'TYD', 'TMF', 'UST'])
history = priceHistory.groupHistory(watch_list.symbols())
history = priceHistory.groupHistory(['TYD', 'UGE', 'RXL', 'BZQ', 'UST', 'FXG', 'EDV', 'UGA', 'QLD']) # Derived from larger list

history.load_to_date(conn, datetime.date(2013,11,1), 900)

all_returns = history.matrix_of_returns().T

return_results = []
cross_val_return_results = []
vol_results = []

allocations = {}

for trial in range(1000):
    numpy.random.shuffle(all_returns)

    train_returns = all_returns[0::2,:].T
    test_returns = all_returns[1::2,:].T

    mean_train_returns = numpy.mean(train_returns,1)
    cov_train_returns = numpy.cov(train_returns)

    mean_test_returns = numpy.mean(test_returns,1)
    cov_test_returns = numpy.cov(test_returns)

    n = len(history.symbols)
    maxalloc = 0.99

    mu = 15

    P = 2 * mu * matrix(cov_train_returns)
    q = -matrix(mean_train_returns)
    G = -matrix(numpy.identity(n))
    h = matrix(0.0, (n,1))
    A = matrix(1.0, (1,n))
    b = matrix(1.0, (1,1))
    result = qp(P,q,G,h,A,b)
    if result['status'] != "optimal":
        raise Exception("Quadratic solver failed" + result['status'])

    x = result['x']

    for i in range(n):
        if history.symbols[i] in allocations:
            allocations[history.symbols[i]] += x[i]
        else:
            allocations[history.symbols[i]] = x[i]

    vol_results.append(numpy.sqrt(250*(x.T*matrix(cov_train_returns)*x)[0]))
    return_results.append( (-x.T*q*250)[0] )

    crossq = - matrix(mean_test_returns)
    cross_val_return_results.append( (-x.T*crossq*250)[0] )

print "mu is ", mu
print "Mean/Std of optimal returns = %g/%g" % (numpy.mean(return_results),
                                               numpy.std(return_results))
print "Mean/Std of optimal volatilities = %g/%g" % (numpy.mean(vol_results),
                                                    numpy.std(vol_results))
print "Mean/Std of cross-returns = %g/%g" % (numpy.mean(cross_val_return_results),
                                             numpy.std(cross_val_return_results))

total = sum([allocations[s] for s in history.symbols])
result  = [ (s,allocations[s]/total) for s in history.symbols ]
sortedresult = sorted(result,key=lambda s: s[1], reverse=True)
print sortedresult[0:10]



