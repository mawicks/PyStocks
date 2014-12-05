import datetime
from cvxopt import matrix
from cvxopt.solvers import qp
from cvxopt.solvers import options as solver_options
from sklearn import cross_validation
import psycopg2
import pricehistory
import numpy
import portfolio

solver_options['show_progress'] = False

def optimal_allocation(db_connection, 
                       symbols,
                       slope=15, 
                       days=750,
                       end_date=datetime.date(2099,1,1),
                       iters=1000, 
                       max_allocation=1.0,
                       sampler=cross_validation.ShuffleSplit):
    history = pricehistory.GroupHistory(symbols)

    print("symbols=", symbols)

    history.load_to_date(db_connection, days, end_date)

    all_returns = history.matrix_of_returns().T

    opt_returns = []
    cross_val_returns = []
    opt_vols = []

    cum_allocations = {}

    boot_strap = sampler(days, iters, train_size=0.5)
    for train_index,test_index in boot_strap:
        train_returns = all_returns[train_index,:].T
        test_returns = all_returns[test_index,:].T

        mean_train_returns = numpy.mean(train_returns,1)
        cov_train_returns = numpy.cov(train_returns)

        mean_test_returns = numpy.mean(test_returns,1)
        cov_test_returns = numpy.cov(test_returns)
        
        n = len(history.symbols)
        maxalloc = 0.99

# Following parameters maximize mu - slope*sigma^2
        P = 2 * slope * matrix(cov_train_returns)
        q = -matrix(mean_train_returns)
        G = matrix(numpy.vstack((-numpy.identity(n),
                                 numpy.identity(n))))
        h = matrix(n*[0.0] + n*[max_allocation], (2*n,1))
        A = matrix(1.0, (1,n))
        b = matrix(1.0, (1,1))

        qp_result = qp(P,q,G,h,A,b)
        if qp_result['status'] != "optimal":
            raise Exception("Quadratic solver failed" + result['status'])

        x = qp_result['x']
        
        for i in range(n):
            if history.symbols[i] in cum_allocations:
                cum_allocations[history.symbols[i]] += x[i]
            else:
                cum_allocations[history.symbols[i]] = x[i]
                
        opt_vols.append(numpy.sqrt(250*(x.T*matrix(cov_train_returns)*x)[0]))
        opt_returns.append( (-x.T*q*250)[0] )
                
        crossq = - matrix(mean_test_returns)
        cross_val_returns.append( (-x.T*crossq*250)[0] )

    total = sum([cum_allocations[s] for s in history.symbols])
    allocation  = [ (s,cum_allocations[s]/total) for s in history.symbols ]
    return (allocation, opt_returns, opt_vols, cross_val_returns)
