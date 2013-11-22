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
history = priceHistory.groupHistory(['EUO', 'FXH', 'SPY', 'TYD', 'EDV' ])

history.load_to_date(conn, datetime.date(2013,11,1), 900)

even_returns = history.matrix_of_returns()[:,2::3]
cov_even_returns = numpy.cov(even_returns)
mean_even_returns = numpy.mean(even_returns,1)

odd_returns = history.matrix_of_returns()[:,1::3]
cov_odd_returns = numpy.cov(odd_returns)
mean_odd_returns = numpy.mean(odd_returns,1)

n = len(history.symbols)

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

P = 2 * mu * matrix(cov_even_returns)
Px = matrix(0.0,(n+1,n+1))
Px[0:n,0:n] = P

q = -matrix(mean_even_returns)
qx = matrix(0.0, (n+1,1))
qx[n] = -1.0

G = -matrix(numpy.identity(n))
Gx = matrix(0.0,(n+3,n+1))
Gx[0,0:n] = - matrix(mean_even_returns).T
Gx[1,0:n] = - matrix(mean_even_returns).T
Gx[2,0:n] = - matrix(mean_even_returns).T
Gx[3:n+3,0:n] = - matrix(numpy.identity(n))
Gx[0:3,n] = 1.0

h = matrix(0.0, (n,1))
hx = matrix(0.0, (n+3,1))

A = matrix(1.0, (1,n))
Ax = matrix(0.0, (1,n+1))
Ax[0,0:n] = 1.0

b = matrix(1.0, (1,1))
bx = matrix(1.0, (1,1))

result = qp(P,q,G,h,A,b)
resultx = qp(Px,qx,Gx,hx,Ax,bx)

x = result['x']
print [ (history.symbols[i],x[i]) for i in range(n) if x[i] > .005]
print "vol = ",numpy.sqrt(250*x.T*matrix(cov_even_returns)*x)[:]
print "ret = ",-x.T*q*250
print "ret-vol = ", -x.T*q*250-numpy.sqrt(250*x.T*matrix(cov_even_returns)*x)

print

crossq = - matrix(mean_odd_returns)
print "cross-val-vol = ",numpy.sqrt(250*x.T*matrix(cov_odd_returns)*x)[:]
print "cross-val-ret = ",-x.T*crossq*250
print "cross-val-ret-vol = ", -x.T*crossq*250-numpy.sqrt(250*x.T*matrix(cov_odd_returns)*x)


x = resultx['x'][0:n]
print "p=", resultx['x'][n]*250
print [ (history.symbols[i],x[i]) for i in range(n) if x[i] > .005]
print "vol = ",numpy.sqrt(250*x.T*matrix(cov_even_returns)*x)[:]
print "ret = ",-x.T*q*250
print "ret-vol = ", -x.T*q*250-numpy.sqrt(250*x.T*matrix(cov_even_returns)*x)

print

crossq = - matrix(mean_odd_returns)
print "cross-val-vol = ",numpy.sqrt(250*x.T*matrix(cov_odd_returns)*x)[:]
print "cross-val-ret = ",-x.T*crossq*250
print "cross-val-ret-vol = ", -x.T*crossq*250-numpy.sqrt(250*x.T*matrix(cov_odd_returns)*x)

