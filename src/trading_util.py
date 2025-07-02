from ib_insync import *

def get_ticker_info(ib_client: IB, ticker, contract_type):
    if contract_type == 'IND':
        contract = Contract(symbol=ticker, secType=contract_type)
        ib_client.qualifyContracts(contract)
        ib_client.reqHeadTimeStamp(contract=contract, whatToShow="TRADES", useRTH=True)
    else:
        contract = Contract(symbol=ticker, exchange='SMART', secType=contract_type, currency='USD')
        ib_client.qualifyContracts(contract)
        ib_client.reqHeadTimeStamp(contract=contract, whatToShow="TRADES", useRTH=False)
        
    ticker = ib_client.reqMktData(contract)
    
    return contract, ticker