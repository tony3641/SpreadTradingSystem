from ib_insync import *
from numpy import double
import numpy as np
from datetime import datetime

def get_index_quote_return_str(ib : IB):
    output=''
    spx = Contract(symbol='SPX',secType='IND')
    ndx = Contract(symbol='NDX',secType='IND')
    ib.qualifyContracts(spx)
    ib.reqHeadTimeStamp(spx, whatToShow='TRADES', useRTH=False)
    ib.qualifyContracts(ndx)
    ib.reqHeadTimeStamp(ndx,whatToShow='TRADES', useRTH=True)
    spx_bars=ib.reqHistoricalData(
        contract=spx,
        endDateTime='',
        durationStr='60 S',
        barSizeSetting='1 secs',
        whatToShow='TRADES',
        useRTH=False,
        formatDate='1'
    )
    ndx_bars=ib.reqHistoricalData(
        contract=ndx,
        endDateTime='',
        durationStr='60 S',
        barSizeSetting='1 secs',
        whatToShow='TRADES',
        useRTH=False,
        formatDate='1'
    )
    now = datetime.now()
    output='S&P500 = '+str(spx_bars[0].close)+' NASDAQ = '+str(ndx_bars[0].close)+'\n'
    #print(output)
    return output


def query_account_info_return_str(ib : IB):
    accounts=[]
    output=''
    account_val=ib.accountValues('')
    for val in account_val:
        if not (val.account in accounts):
            accounts.append(val.account) 
    output+='Avaliable accounts='+str(accounts)+'\n'
    for account in accounts:
        output+=('-----Listing Account ID = '+str(account)+'-----\n')
        cash_balance=double([v.value for v in account_val if (v.tag == 'CashBalance' and v.account == account)][0])
        buying_power=double([v.value for v in account_val if (v.tag == 'BuyingPower' and v.account == account)][0])
        unrealizedPnL=double([v.value for v in account_val if (v.tag == 'UnrealizedPnL' and v.currency == 'USD' and v.account == account)][0])
        output+=('Cash Balance = $' + str(cash_balance)+'\n')
        output+=('Buying Power = $' + str(buying_power)+'\n')
        output+=('Unrealized PnL = $' + str(unrealizedPnL)+'\n')
        positions = ib.positions(account)
        if positions:
            output+=('Position(s) in this account:\n')
            for position in positions:
                if hasattr(position,'contract'):
                    output+=(str(position.contract.localSymbol)+' * '+str(position.position) + ' @ '+ str(position.avgCost)+'\n')
        else:
            output+=('No position yet.\n')
        output+=('\n')
    return output

ib = IB()
ib.connect('127.0.0.1', 4001, clientId=0)

accounts=[]
account_val=ib.accountValues('')
for val in account_val:
    if not (val.account in accounts):
        accounts.append(val.account)
        
print('Avaliable accounts='+str(accounts))

for account in accounts:
    print('-----Listing Account ID = '+str(account)+'-----')
    cash_balance=double([v.value for v in account_val if (v.tag == 'CashBalance' and v.account == account)][0])
    buying_power=double([v.value for v in account_val if (v.tag == 'BuyingPower' and v.account == account)][0])
    unrealizedPnL=double([v.value for v in account_val if (v.tag == 'UnrealizedPnL' and v.currency == 'USD' and v.account == account)][0])
    print('Cash Balance = $' + str(cash_balance))
    print('Buying Power = $' + str(buying_power))
    print('Unrealized PnL = $' + str(unrealizedPnL))
    positions = ib.positions(account)
    if positions:
        print('Position(s) in this account:\n')
        for position in positions:
            if hasattr(position,'contract'):
                print(str(position.contract.localSymbol)+' * '+str(position.position) + ' @ '+ str(position.avgCost))
    else:
        print('No position yet.')
    print('\n')
    

'''stock = Stock('SPY', 'SMART', 'USD')
ib.qualifyContracts(stock)
print(stock)
order = MarketOrder('BUY', 10)
trade = ib.placeOrder(stock, order)'''


#spy_option_chain=ib.reqSecDefOptParams(stock.symbol,'SMART', stock.secType, stock.conId)
#df = util.df(spy_option_chain)

ib.disconnect()