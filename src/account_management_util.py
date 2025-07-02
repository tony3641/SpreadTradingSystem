from ib_insync import *
from numpy import double
import numpy as np
from datetime import datetime

class TradingClient:
    name = "Trading System"
    DiscordBot = None
    BotCommandChannel = None
    BotAlertChannel = None
    IBClient = None
    IBClientId = 0
    watchList = []


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
        barSizeSetting='5 secs',
        whatToShow='TRADES',
        useRTH=False,
        formatDate='1'
    )
    ndx_bars=ib.reqHistoricalData(
        contract=ndx,
        endDateTime='',
        durationStr='60 S',
        barSizeSetting='5 secs',
        whatToShow='TRADES',
        useRTH=False,
        formatDate='1'
    )
    output='S&P500 = '+str(spx_bars[0].close)+' NASDAQ = '+str(ndx_bars[0].close)+'\n'
    #print(output)
    return output

def get_spx_return_str(ib: IB):
    output=''
    spx = Contract(symbol='SPX',secType='IND')
    ib.qualifyContracts(spx)
    ib.reqHeadTimeStamp(spx, whatToShow='TRADES', useRTH=False)
    spx_bars=ib.reqHistoricalData(
        contract=spx,
        endDateTime='',
        durationStr='60 S',
        barSizeSetting='5 secs',
        whatToShow='TRADES',
        useRTH=False,
        formatDate='1'
    )
    output='S&P500 = '+str(spx_bars[0].close)
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
        output+=('\n-----Listing Account ID = '+str(account)+'-----\n')
        cash_balance = double([v.value for v in account_val if (v.tag == 'CashBalance' and v.account == account)][0])
        buying_power = double([v.value for v in account_val if (v.tag == 'BuyingPower' and v.account == account)][0])
        unrealized_PnL = double([v.value for v in account_val if (v.tag == 'UnrealizedPnL' and v.currency == 'USD' and v.account == account)][0])
        total_NAV = double([v.value for v in account_val if (v.tag == 'EquityWithLoanValue' and v.account == account)][0])
        maintain_margin = double([v.value for v in account_val if (v.tag == 'MaintMarginReq' and v.account == account)][0])
        output+=('NAV = $' + str(total_NAV)+'\n')
        output+=('Cash Balance = $' + str(cash_balance) + '\n')
        output+=('Buying Power = $' + str(buying_power) + '\n')
        output+=('Maintainance Margin = $' + str(maintain_margin) + '\n')
        output+=('Unrealized PnL = $' + str(unrealized_PnL) + '\n')
        positions = ib.positions(account)
        if positions:
            output+=('\nPosition(s) in this account:\n')
            for position in positions:
                if hasattr(position,'contract'):
                    contract = position.contract
                    contract.exchange='SMART'
                    market_data = ib.reqMktData(contract=contract, snapshot=True)
                    ib.sleep(0.24)
                    position_pnl = (position.position * market_data.last) - (position.position * position.avgCost)
                    output += f"{contract.localSymbol:<21} * {position.position:>5.1f} @ {position.avgCost:>8.2f}, PnL: {position_pnl:>8.2f}\n"
                    #output+=(str(position.contract.localSymbol)+' * '+str(position.position) + ' @ '+ str(round(position.avgCost, 2))+f' PnL = {position_pnl:.2f}'+'\n')
        else:
            output+=('No position yet.\n')
    return output, positions

