from csv import QUOTE_MINIMAL
from xmlrpc.client import DateTime
from ib_insync import *
from matplotlib import pyplot as plt
import math
from spread_util import *
from numpy import double
from datetime import datetime
from importlib import reload
from termcolor import colored

#util.startLoop()

ib = IB()
BROKERAGE_PORT=8331
PAPER_PORT=7497
MARGIN_UTILIZATION=0.35

port_no=BROKERAGE_PORT
status = ib.connect(host='127.0.0.1', port=port_no, clientId=2, timeout=10)
print(status)
now = datetime.now()
print('Time = ' + str(now))

if port_no == PAPER_PORT:
    print("This is a PAPER TRADE account!!!!!")
elif port_no == BROKERAGE_PORT:
    print("This is a BROKERAGE TRADE account!!!!!")
    
account_val=ib.accountValues()
#print(account_val)
nav=double([v.value for v in account_val if v.tag == 'NetLiquidation'][0])
maintain_margin=double([v.value for v in account_val if v.tag == 'MaintMarginReq'][0])
margin_available=nav-maintain_margin
cash_balance=double([v.value for v in account_val if v.tag == 'CashBalance'][0])
buying_power=double([v.value for v in account_val if v.tag == 'BuyingPower'][0])
unrealizedPnL=double([v.value for v in account_val if v.tag == 'UnrealizedPnL' and v.currency == 'USD'][0])
print('-----------------------------------')
print('Cash Balance = $' + str(cash_balance))
print('Buying Power = $' + str(buying_power))
print('Opt/Fut Margin Available = $' + str(margin_available))
print('Unrealized PnL = $' + colored(str(unrealizedPnL), 'green'))
print(util.df(ib.positions()))
print('----------------------------------')
print('Retriving last trading day data...')
spx=Contract(symbol='SPX',secType='IND')
ib.qualifyContracts(spx)
ib.reqHeadTimeStamp(spx,whatToShow='TRADES', useRTH=True)
bars=ib.reqHistoricalData(
    contract=spx,
    endDateTime='',
    durationStr='60 S',
    barSizeSetting='1 secs',
    whatToShow='TRADES',
    useRTH=True,
    formatDate='1'
)

[ticker]=ib.reqTickers(spx)
spxVal=ticker.marketPrice()
if (math.isnan(spxVal)) | (now.hour >= 13 & now.hour <= 17):
    spxVal=bars[-1].close
    print('Market closed. Calculation based on ES future')
    es_future = Contract(symbol='ES', secType='FUT')
    ib.qualifyContracts(es_future)
print('Most recent SPX='+str(spxVal))

chains=ib.reqSecDefOptParams(spx.symbol,'',spx.secType, spx.conId)
#print('Chains='+str(chains))
chain=next(c for c in chains if c.tradingClass=='SPXW' and c.exchange=='SMART')
#print(chain)
strikes=[stk for stk in chain.strikes if stk%5==0 and spxVal-200<stk<spxVal]


if (now.hour >= 13 & now.hour <= 17): #after hours, choose next trading day
    expiration = [sorted(exp for exp in chain.expirations)[1]]
else:
    expiration=[sorted(exp for exp in chain.expirations)[0]]
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
margin = int(input('Max margin for this strat: '))
delta = float(input('delta for short leg (theo max = 1): '))
short_leg=[ticker for ticker in tickers if (ticker.lastGreeks.delta != None)\
           and(delta-0.01<=abs(ticker.lastGreeks.delta)<=delta+0.01)][0]

print('Margin Utilization = '+colored(str(margin/margin_available*100)+"%", 'light_blue'))
long_contract, quantity=calc_optimized_long_leg(ib,SpreadType.BULLPUT,short_leg.contract,*tickers,margin=margin,max_gap=50)
long_leg=ib.reqTickers(long_contract)[0]

spread_price,stop_price=calc_spread_price(ib,SpreadType.BULLPUT,long_leg.contract,short_leg.contract,0,2)
spread_contract=create_vertical_spread(long_leg.contract,short_leg.contract)

print('Spread generated:\n')
print('Strategy = ' + str(SpreadType.BULLPUT))
print('Short Leg: Strike = '+str(short_leg.contract.strike)+' delta='+str(short_leg.lastGreeks.delta))
print('Long Leg: Stike = '+str(long_leg.contract.strike)+' delta='+str(long_leg.lastGreeks.delta))
print('S&P500 portfolio delta = '+str((long_leg.lastGreeks.delta - short_leg.lastGreeks.delta)*100*quantity))
print('Quantity = '+str(quantity))
print('Commision = $'+str(quantity * 2.4))
print('Margin required = $'+str(abs(short_leg.contract.strike-long_leg.contract.strike)*100*quantity))
print('Estimated per spread fill price = $'+str(spread_price)\
    +'\nTotal Premium = '+colored(str(((spread_price * -100)-2.4)*quantity), 'green')\
    +'\nMax loss = $'+colored(str(((stop_price-spread_price)*100-2.4)*quantity), 'red')+' @ STP = $'+str(stop_price)+'\n')

print('\n---------------')
print(spread_contract)
print('---------------\n')


orders=ib.bracketOrder('BUY',quantity,spread_price,SELL_SIDE_TAKE_PROFIT_THRESHOLD,stop_price)
for order in orders:
    #trade=ib.placeOrder(spread_contract,order)
    ib.sleep(0.5)
    #print(trade.log)

ib.disconnect()

