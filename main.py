import datetime
from cvxopt import matrix
from cvxopt.solvers import qp
import psycopg2
import priceHistory
import numpy

conn=psycopg2.connect(host="nas.wicksnet.us",dbname="stocks",user="mwicks")

watch_list = priceHistory.watchList()
watch_list.load(conn)

history = priceHistory.groupHistory(watch_list.symbols())
#history = priceHistory.groupHistory(['FXF', 'FXH', 'GLD', 'QLD' ])
#history = priceHistory.groupHistory(['DDM', 'EDV', 'EUO', 'FXF', 'FXG', 'FXH', 'GLD', 'QLD', 'SIVR', 'SMB', 'SPY', 'TYD', 'XLP' ])

history.load_to_date(conn, datetime.date(2013,11,1), 900)

train_returns0 = history.matrix_of_returns()[:,5::6]
train_returns1 = history.matrix_of_returns()[:,1::6]
train_returns2 = history.matrix_of_returns()[:,2::6]
train_returns3 = history.matrix_of_returns()[:,3::6]
train_returns4 = history.matrix_of_returns()[:,4::6]

mean_train_returns0 = numpy.mean(train_returns0,1)
mean_train_returns1 = numpy.mean(train_returns1,1)
mean_train_returns2 = numpy.mean(train_returns2,1)
mean_train_returns3 = numpy.mean(train_returns3,1)
mean_train_returns4 = numpy.mean(train_returns4,1)

train_returns  = numpy.concatenate((train_returns0,train_returns1,train_returns2,train_returns3,train_returns4),1)
mean_train_returns  = numpy.mean(train_returns,1)
cov_train_returns = numpy.cov(train_returns)

test_returns = history.matrix_of_returns()[:,0::6]
cov_test_returns = numpy.cov(test_returns)
mean_test_returns = numpy.mean(test_returns,1)

n = len(history.symbols)
maxalloc = 0.99

mu = 0.01 # 36.8% return/29% vol/7%
mu = 10.5 # 19.4% return/8.2% vol/11.2%
mu = 15   # 16.0% return/6.3% vol/9.6%
mu = 16.5 # 15.0% return/5.8% vol/9.2%
mu = 20   # 13.4% return/5.0% vol/8.35%
mu = 9    # 20.3% return/8.8% vol/11.6%
mu = 8    # 21.1% return/9.3% vol/11.8%
mu = 7    # 22.1% return/9.9% vol/12.1%
mu = 6    # 23.5% return/11.0% vol/12.5%
mu = 5    # 25.1% return/12.3% vol/12.8%
mu = 4    # 26.4% return/13.4% vol/13.0%
mu = 3    # 28.0% return/15.4% vol/13.0%
mu = 2    # 29.9% return/17.4% vol/12.48%
mu = 15   # 16.0% return/6.3% vol/9.6%
mu = 8

P = 2 * mu * matrix(cov_train_returns)
Px = matrix(0.0,(n+1,n+1))
Px[0:n,0:n] = P

q = -matrix(mean_train_returns)
qx = matrix(0.0, (n+1,1))
qx[n] = -1.0

G = -matrix(numpy.identity(n))
Gx = matrix(0.0,(2*n+5,n+1))
Gx[0,0:n] = - matrix(mean_train_returns0).T
Gx[1,0:n] = - matrix(mean_train_returns1).T
Gx[2,0:n] = - matrix(mean_train_returns2).T
Gx[3,0:n] = - matrix(mean_train_returns3).T
Gx[4,0:n] = - matrix(mean_train_returns4).T
Gx[0:5,n] = 1.0

Gx[5:n+5,0:n] = - matrix(numpy.identity(n))
Gx[n+5:2*n+5,0:n] =  matrix(numpy.identity(n))

h = matrix(0.0, (n,1))
hx = matrix(0.0, (2*n+5,1))
hx[n+5:2*n+5] = maxalloc

A = matrix(1.0, (1,n))
Ax = matrix(0.0, (1,n+1))
Ax[0,0:n] = 1.0

b = matrix(1.0, (1,1))
bx = matrix(1.0, (1,1))

result = qp(P,q,G,h,A,b)
resultx = qp(Px,qx,Gx,hx,Ax,bx)

x = result['x']
print [ (history.symbols[i],x[i]) for i in range(n) if x[i] > .005]
print "vol = ",numpy.sqrt(250*x.T*matrix(cov_train_returns)*x)[:]
print "ret = ",-x.T*q*250
# print "ret-vol = ", -x.T*q*250-numpy.sqrt(250*x.T*matrix(cov_train_returns)*x)

crossq = - matrix(mean_test_returns)
print "cross-val-vol = ",numpy.sqrt(250*x.T*matrix(cov_test_returns)*x)[:]
print "cross-val-ret = ",-x.T*crossq*250
# print "cross-val-ret-vol = ", -x.T*crossq*250-numpy.sqrt(250*x.T*matrix(cov_test_returns)*x)

xx = resultx['x'][0:n]
print "p=", resultx['x'][n]*250
print [ (history.symbols[i],xx[i]) for i in range(n) if xx[i] > .005]
print "vol = ",numpy.sqrt(250*xx.T*matrix(cov_train_returns)*xx)[:]
print "ret = ",-xx.T*q*250
# print "ret-vol = ", -xx.T*q*250-numpy.sqrt(250*xx.T*matrix(cov_train_returns)*xx)

crossq = - matrix(mean_test_returns)
print "cross-val-vol = ",numpy.sqrt(250*xx.T*matrix(cov_test_returns)*xx)[:]
print "cross-val-ret = ",-xx.T*crossq*250
# print "cross-val-ret-vol = ", -xx.T*crossq*250-numpy.sqrt(250*xx.T*matrix(cov_test_returns)*xx)

