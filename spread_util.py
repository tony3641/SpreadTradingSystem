from pickletools import optimize
from ib_insync import *
from enum import Enum
import math
import ib_insync

class SpreadType(Enum):
    BULLPUT=1
    BEARPUT=2
    BULLCALL=3
    BEARCALL=4

PUT = 'P'
CALL = 'C'
SELL_SIDE_TAKE_PROFIT_THRESHOLD=0.05 #take profit with a neg spread price
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
given spread. 
For priority:
    2=EXTREME 
    1=HIGH 
    0=LOW
credit risk: 
    3 = no stop loss
    2 = stop loss @ 5*premium
    1 = stop loss @ 3*premium
'''
def calc_spread_price(ib : IB, spread_type : SpreadType, long_contract : Contract, short_contract : Contract, priority : int, risk: int):
    long = ib.reqTickers(long_contract)[0]
    short = ib.reqTickers(short_contract)[0]
    if (spread_type == SpreadType.BULLPUT) or (spread_type == SpreadType.BEARCALL):
        if priority == 1:
            price = long.ask - short.bid
        elif priority == 0:
            price = long.ask - short.bid - 0.05 #WE LOVE MAGIC NUMBER!!
        elif priority == 2:
            price = long.ask - short.bid + 0.05
        
        if risk == 3:
            stop_price = None
        if risk == 2:
            stop_price = 5*price
        if risk == 1:
            stop_price = 3*price
            
    return price, stop_price


def calc_optimized_long_leg(ib: IB, spread_type : SpreadType, short_contract : Contract, \
    *tickers, margin : int, max_gap : int):
    max_premium = 0
    short_ticker = ib.reqTickers(short_contract)[0] #update price
    if spread_type == SpreadType.BULLPUT:
        print('Sweeping PUT chain to find best long leg...')
        for gap in range(1,int(max_gap/5)+1):
            long_strike = short_contract.strike - gap * 5
            long_contract = [ticker for ticker in tickers if ticker.contract.strike == long_strike][0].contract
            long_ticker = ib.reqTickers(long_contract)[0] #update price
            print('Checking:'+str(long_contract.strike)+' PUT:')
            quantity = math.floor(margin/((short_contract.strike-long_contract.strike)*100))
            print(str(quantity)+' spread for margin = $'+str(margin))
            premium = abs(long_ticker.ask - short_ticker.bid) * quantity * 100
            print('Possible premium = $'+str(premium)+'\n')
            if premium > max_premium:
                max_premium = premium
                optimized_contract = long_contract
                optimized_quantity = quantity
                
    elif spread_type == SpreadType.BEARCALL:
        pass
    else:
        pass
    print('Optimized long leg found: '+str(optimized_contract.strike)+' PUT\n')
    return optimized_contract, optimized_quantity



