from ib_insync import *
from enum import Enum
from math import floor
import ib_insync
import numpy as np
from scipy.stats import norm

class OptionType(Enum):
    CALL = 1
    PUT = 2
    
PUT = 'P'
CALL = 'C'


'''@In S: spot price
   @In K: strike price
   @In r: risk-free interest rate
   @In T: time to expire, in yr
   @In direct: call or put, in str'''
def black_scholes(S, K, r, T, vol, direction):
    d1=(np.log(S/K)+(r+vol**2/2)*T)/(vol*np.sqrt(T))
    d2=d1-vol*np.sqrt(T)
    if direction=='call':
        price=S*norm.cdf(d1,0,1)-K*np.exp(-r*T)*norm.cdf(d2,0,1)
    if direction=='put':
        price=K*np.exp(-r*T)*norm.cdf(-d2,0,1)-S*norm.cdf(-d1,0,1)
    return price

def calc_delta(S, K, r, T, sigma, type):
    d1=(np.log(S/K)+(r+sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2=d1-sigma*np.sqrt(T)
    if type=='call':
        delta=norm.cdf(d1,0,1)
    if type=='put':
        delta=-norm.cdf(-d1,0,1)
    return delta

def calc_gamma(S, K, r, T, sigma, type):
    d1=(np.log(S/K)+(r+sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2=d1-sigma*np.sqrt(T)
    gamma=norm.pdf(d1,0,1)/(S*sigma*np.sqrt(T))
    return gamma

def calc_theta(S, K, r, T, sigma, type):
    d1=(np.log(S/K)+(r+sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2=d1-sigma*np.sqrt(T)
    if type=='call':
        theta=-((S*norm.pdf(d1,0,1)*sigma)/(2*np.sqrt(T)))-r*K*np.exp(-r*T)*norm.cdf(d2,0,1)
    if type=='put':
        theta=-((S*norm.pdf(d1,0,1)*sigma)/(2*np.sqrt(T)))+r*K*np.exp(-r*T)*norm.cdf(-d2,0,1)
    return theta/365

def calc_vega(S, K, r, T, sigma):
    d1=(np.log(S/K)+(r+sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2=d1-sigma*np.sqrt(T)
    vega=S*np.sqrt(T)*norm.pdf(d1,0,1)*0.01
    return vega

"""calculate the historic volatility of a stock, needed for black scholes"""
"""@In: List a series of close price"""
def calc_volatility(period_close_price):
    r=[]
    for i in range(len(period_close_price)):
        if i>0:
            r.append(np.log(period_close_price[i]/period_close_price[i-1])) #daily log return
    r_avg=np.average(r)
    variance=0
    for i in range(len(r)):
        variance+=((r[i]-r_avg)**2)/(len(r)-1)
    std_dev=np.sqrt(252)*np.sqrt(variance) #annualized sd with 252 trading days per year
    return std_dev