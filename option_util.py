from ib_insync import *
from enum import Enum
from math import floor
import ib_insync
import numpy as np
from scipy.stats import norm

class SpreadType(Enum):
    BULLPUT = 1
    BEARPUT = 2
    BULLCALL = 3
    BEARCALL = 4

class OptionType(Enum):
    CALL = 1
    PUT = 2
    
PUT = 'P'
CALL = 'C'

'''
This function creates a vertical spread, 
simply pass long side contract and short
side contract, and a combo contract will
be returned.
'''
def create_vertical_spread(long_contract : Contract, short_contract : Contract):
    assert long_contract.symbol == short_contract.symbol, 'symbol for both legs must be the same!'
    contract = Contract()
    contract.symbol = long_contract.symbol
    contract.secType = 'BAG'
    contract.currency = long_contract.currency
    contract.exchange = long_contract.exchange
    
    short_leg = ComboLeg()
    short_leg.conId = short_contract.conId
    short_leg.ratio = 1
    short_leg.action = 'SELL'
    short_leg.exchange = short_contract.exchange
    
    long_leg = ComboLeg()
    long_leg.conId = long_contract.conId
    long_leg.ratio = 1
    long_leg.action = 'BUY'
    long_leg.exchange = long_contract.exchange
    
    contract.comboLegs = []
    contract.comboLegs.append(short_leg)
    contract.comboLegs.append(long_leg)
    return contract

'''
This function calculate limit price for a
given spread. For priority 1=HIGH 0=LOW
'''
def calc_spread_price(ib : IB, spread_type : SpreadType, long_contract : Contract, short_contract : Contract, priority : int):
    long = ib.reqTickers(long_contract)[0]
    short = ib.reqTickers(short_contract)[0]
    if (spread_type == SpreadType.BULLPUT) or (spread_type == SpreadType.BEARCALL):
        price = long.ask - short.bid
    return price

'''
This function calculates best long leg to 
order for max premium by given max strike 
gap and total margin spending'''
def long_leg_optimizer(ib : IB, spread_type : SpreadType, \
    short_contract : Contract, *tickers : Ticker, margin: int, max_gap : int):
    short = ib.reqTickers(short_contract)[0]
    max_premium=0
    
    if spread_type == SpreadType.BULLPUT:
        for gap in range(1,(max_gap/5)+1):
            strike = short_contract.strike - gap * 5
            contract = [tick for tick in tickers if tick.contract.strike == strike][0]
            ticker = ib.reqTickers(contract)[0]
            quantity = floor(margin/((short_contract.strike-strike)*100))
            premium = quantity*(short.bid-ticker.ask)
            if premium > max_premium:
                long_contract = contract
        print('For max premium:')
        print('Short Leg = '+str(short_contract.strike))
        print('Long Leg = '+str(long_contract.strike))
        print('Premium = '+str(max_premium))
        
    elif spread_type == SpreadType.BEARCALL:
        pass 
    
    else:
        pass
    
    return long_contract

'''This function returns the furthest possible spread '''
def find_credit_spread_by_price(ib : IB, opt_type : OptionType, price : float):
    if price > 0: #order price should always be neg val for credit spread.
        price = -price


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