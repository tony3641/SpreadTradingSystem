from ib_insync import *
from option_util import *
import pandas_market_calendars as mcal
import datetime as dt
import sys
import os
from time import sleep
from account_management import *
import math
from threading import Thread

port_no = 4001
paper_trade_port_no = 4002

def future_next_expirary():
    month=math.ceil(dt.datetime.now().month/3)*3
    if month != 12:
        month_str = '0'+str(month)
    else:
        month_str = str(month)
    year=dt.datetime.now().year
    return str(year)+month_str

ib = IB()

status = ib.connect('127.0.0.1', 4001, clientId=0x2)
status = True
if not status:
    sys.exit(0)
    
nyse = mcal.get_calendar('NYSE')
try:
    while True:
        os.system('cls')
        today = dt.datetime.now(tz=nyse.tz)
        schedule = nyse.schedule(start_date=today, end_date=today)

        if len(schedule) > 0:
            market_open = schedule.iloc[0]['market_open']
            market_close = schedule.iloc[0]['market_close']
            acc_info = query_account_info_return_str(ib)
            print(acc_info)
            print(get_spx_return_str(ib))
            if market_open <= today <= market_close:
                print(str(nyse.tz) + ' ' +str(today.now()) + " : In RTH.")
                
            else:
                print(str(nyse.tz) + ' ' + str(today.now()) + " : Not in RTH.")

                
        else:
            print(str(today.date()) + " : Market close today.")
        
        sleep(3)
        
finally:
    ib.disconnect()
