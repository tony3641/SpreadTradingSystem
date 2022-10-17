from ib_insync import *
import pandas as pd

ib=IB()
ib.connect('127.0.0.1',7497, clientId=0)

spx=Contract(symbol='SPX',secType='IND')
ib.qualifyContracts(spx)
ib.reqHeadTimeStamp(spx,whatToShow='TRADES', useRTH=True)
bars=ib.reqHistoricalData(
    contract=spx,
    endDateTime='',
    durationStr='10 D',
    barSizeSetting='2 mins',
    whatToShow='TRADES',
    useRTH=True,
    formatDate='1'
)
#ib.qualifyContracts(contract)
df=util.df(bars)
print(df)
df.to_csv('./spx_10d.csv')