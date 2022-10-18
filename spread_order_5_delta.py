from csv import QUOTE_MINIMAL
from xmlrpc.client import DateTime
from ib_insync import *
from matplotlib import pyplot as plt
import math
from spread_util import *
from numpy import double
from datetime import datetime
from importlib import reload

#util.startLoop()

ib = IB()
BROKERAGE_PORT=7496
PAPER_PORT=7497

port_no=7497
status = ib.connect('127.0.0.1', port_no, clientId=2)
print(status)
now = datetime.now()
print('Time = ' + str(now))

if port_no == PAPER_PORT:
    print("This is a PAPER TRADE account!!!!!")
elif port_no == BROKERAGE_PORT:
    print("This is a BROKERAGE TRADE account!!!!!")
    
account_val=ib.accountValues()
#print(account_val)
cash_balance=double([v.value for v in account_val if v.tag == 'CashBalance'][0])
buying_power=double([v.value for v in account_val if v.tag == 'BuyingPower'][0])
unrealizedPnL=double([v.value for v in account_val if v.tag == 'UnrealizedPnL' and v.currency == 'USD'][0])
print('-----------------------------------')
print('Cash Balance = $' + str(cash_balance))
print('Buying Power = $' + str(buying_power))
print('Unrealized PnL = $' + str(unrealizedPnL))
print(util.df(ib.positions()))
print('----------------------------------')
print('Retriving last trading day data...')
spx=Contract(symbol='SPX',secType='IND')
ib.qualifyContracts(spx)
ib.reqHeadTimeStamp(spx,whatToShow='TRADES', useRTH=True)
bars=ib.reqHistoricalData(
    contract=spx,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='2 mins',
    whatToShow='TRADES',
    useRTH=True,
    formatDate='1'
)

df=util.df(bars)

[ticker]=ib.reqTickers(spx)
spxVal=ticker.marketPrice()
if math.isnan(spxVal):
    spxVal=bars[-1].close
print('Most recent SPX='+str(spxVal))

chains=ib.reqSecDefOptParams(spx.symbol,'',spx.secType, spx.conId)
#print('Chains='+str(chains))
chain=next(c for c in chains if c.tradingClass=='SPXW' and c.exchange=='SMART')
#print(chain)
strikes=[stk for stk in chain.strikes if stk%5==0 and spxVal-150<stk<spxVal-50]
expiration=[sorted(exp for exp in chain.expirations)[:1][0]]
#

print('Expiration date='+expiration[0])

print('Fetching option chain...')
rights=['P']
contracts=[Option('SPX',exp,stk,right,'SMART')
           for right in rights
           for exp in expiration
           for stk in strikes]

contracts=ib.qualifyContracts(*contracts)
#print(contracts)
tickers=ib.reqTickers(*contracts)
#print(tickers)
quantity=0
short_leg=[ticker for ticker in tickers if (ticker.lastGreeks.delta != None)\
           and(0.04<=abs(ticker.lastGreeks.delta)<=0.06)][0]

long_contract, quantity=calc_optimized_long_leg(ib,SpreadType.BULLPUT,short_leg.contract,*tickers,margin=10000,max_gap=30)
long_leg=ib.reqTickers(long_contract)[0]

spread_price,stop_price=calc_spread_price(ib,SpreadType.BULLPUT,long_leg.contract,short_leg.contract,1,2)
spread_contract=create_vertical_spread(long_leg.contract,short_leg.contract)

print('Spread generated:\n')
print('Strategy = ' + str(SpreadType.BULLPUT))
print('Short Leg: Strike = '+str(short_leg.contract.strike)+' delta='+str(short_leg.lastGreeks.delta))
print('Long Leg: Stike = '+str(long_leg.contract.strike)+' delta='+str(long_leg.lastGreeks.delta))
print('Quantity = '+str(quantity))
print('Margin required = '+str(abs(short_leg.contract.strike-long_leg.contract.strike)*100*quantity)+' USD')
print('Estimated premium = '+str(spread_price)\
    +'\nTake profit @ expire '              \
    +'\nStop loss @ '+str(stop_price)+'\n')

print('\n---------------')
print(spread_contract)
print('---------------\n')

orders=ib.bracketOrder('BUY',quantity,spread_price,0,stop_price)
for order in orders:
    trade=ib.placeOrder(spread_contract,order)
    ib.sleep(0.5)
    print(trade.log)

ib.disconnect()

