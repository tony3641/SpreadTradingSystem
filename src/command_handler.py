import asyncio
from ib_insync import *
from account_management_util import query_account_info_return_str, TradingClient
from trading_util import *
import math

# Shared Queue for commands from CLI & Discord
command_queue = asyncio.Queue()

# Trading Engine (Dummy Implementation)
def process_command(command, trading_client : TradingClient):
    parts = command.split()
    if not parts:
        return "Invalid command format."

    cmd_type = parts[0].lower()

    if cmd_type == "!account":
        output_str, _ = query_account_info_return_str(trading_client.IBClient)
        return output_str
    elif cmd_type == "!position":
        return "Current Position: 5 Contracts of SPY Calls"
    elif cmd_type == "!liquidate":
        return "Force Liquidation Executed"
    elif cmd_type == "!watch":
        output = ""
        for ticker in trading_client.watchList:
            symbol= ticker.contract.symbol
            if math.isnan(ticker.last):
                price = "$---"
                change = ""
            else:
                price = f"${ticker.last:.2f}"
                change = f" {round((ticker.last-ticker.close)/ticker.close*100, 2)}%"
        
                output += f"{symbol:<6} {price:<8} {change:<6}\n"
            #output+=str(ticker.contract.symbol)
            #if math.isnan(ticker.last):
            #    output+=" $---"+"\n"
            #else:
            #    output+=" $"+str(ticker.last)+" "+str(round((ticker.last-ticker.close)/ticker.close*100, 2))+"%\n"

        return output
    
    elif cmd_type == "!0dte":
        if len(parts) < 4:
            return "Usage: !0dte [margin] [delta] [immediate_order]"
        try:
            margin = int(parts[1])
            delta = float(parts[2])/100
            immediate_order = int(parts[3])
        
        except ValueError:
            return "Invalid input. Margin and delta must be numbers"
    
        return 0
    
    elif cmd_type == "!buy":
        if len(parts) < 4:
            return "Usage: !buy [ticker] [order_type] [quantity] (optional: [lmt_price] [stp_price])"

        ticker = parts[1].upper()
        order_type = parts[2].upper()
        try:
            quantity = int(parts[3])
        except ValueError:
            return "Invalid quantity. Must be an integer."

        if order_type == "MKT":
            return f"Placing market order: Buy {quantity} {ticker}"
        elif order_type == "LMT":
            if len(parts) < 5:
                return "Limit order requires a limit price. Usage: !buy [ticker] LMT [quantity] [lmt_price]"
            try:
                lmt_price = float(parts[4])
            except ValueError:
                return "Invalid limit price. Must be a number."
            return f"Placing limit order: Buy {quantity} {ticker} at {lmt_price}"
        elif order_type == "LMT_STP":
            if len(parts) < 6:
                return "Stop limit order requires limit and stop prices. Usage: !buy [ticker] LMT STP [quantity] [lmt_price] [stp_price]"
            try:
                lmt_price = float(parts[4])
                stp_price = float(parts[5])
            except ValueError:
                return "Invalid price values. Both limit and stop prices must be numbers."
            return f"Placing stop-limit order: Buy {quantity} {ticker} at {lmt_price}, stop price {stp_price}"
        else:
            return "Invalid order type. Allowed types: MKT, LMT, LMT STP"

    elif cmd_type in ["!opt_buy", "!opt_sell"]:
        if len(parts) == 2 and parts[1] in ["-h", "--help"]:
            return f"""
            Usage: {cmd_type} [ticker] [call/put] [strike_price] [order_type] [quantity] (optional: [lmt_price] [stp_price])
        
            Order Types:
            MKT: Market Order
            LMT: Limit Order
            LMT_STP: Stop Limit Order
        
            Example:
            {cmd_type} AAPL CALL 150.0 MKT 10
            {cmd_type} AAPL CALL 150.0 LMT 10 5.0
            {cmd_type} AAPL CALL 150.0 LMT_STP 10 5.0 6.0
            """

        if len(parts) < 6:
            return f"Usage: {cmd_type} [ticker] [call/put] [strike_price] [order_type] [quantity] (optional: [lmt_price] [stp_price])"

        ticker = parts[1].upper()
        option_type = parts[2].upper()
        try:
            strike_price = float(parts[3])
        except ValueError:
            return "Invalid strike price. Must be a number."
        order_type = parts[4].upper()
        try:
            quantity = int(parts[5])
        except ValueError:
            return "Invalid quantity. Must be an integer."

        if option_type not in ["CALL", "PUT"]:
            return "Invalid option type. Must be CALL or PUT."

        if order_type == "MKT":
            return f"Placing market order: {cmd_type.capitalize()} {quantity} {ticker} {option_type} {strike_price}"
        elif order_type == "LMT":
            if len(parts) < 7:
                return f"Limit order requires a limit price. Usage: {cmd_type} [ticker] [call/put] [strike_price] LMT [quantity] [lmt_price]"
            try:
                lmt_price = float(parts[6])
            except ValueError:
                return "Invalid limit price. Must be a number."
            return f"Placing limit order: {cmd_type.capitalize()} {quantity} {ticker} {option_type} {strike_price} at {lmt_price}"
        elif order_type == "LMT_STP":
            if len(parts) < 8:
                return f"Stop limit order requires limit and stop prices. Usage: {cmd_type} [ticker] [call/put] [strike_price] LMT STP [quantity] [lmt_price] [stp_price]"
            try:
                lmt_price = float(parts[6])
                stp_price = float(parts[7])
            except ValueError:
                return "Invalid price values. Both limit and stop prices must be numbers."
            return f"Placing stop-limit order: {cmd_type.capitalize()} {quantity} {ticker} {option_type} {strike_price} at {lmt_price}, stop price {stp_price}"
        else:
            return "Invalid order type. Allowed types: MKT, LMT, LMT STP"
        
    elif cmd_type in ["!opt_buy", "!opt_sell"]:
        if len(parts) == 2 and parts[1] in ["-h", "--help"]:
            return f"""
            Usage: {cmd_type} [ticker] [call/put] [strike_price] [order_type] [quantity] (optional: [lmt_price] [stp_price])
        
            Order Types:
            MKT: Market Order
            LMT: Limit Order
            LMT_STP: Stop Limit Order
        
            Example:
            {cmd_type} AAPL CALL 150.0 MKT 10
            {cmd_type} AAPL CALL 150.0 LMT 10 5.0
            {cmd_type} AAPL CALL 150.0 LMT_STP 10 5.0 6.0
            """

        if len(parts) < 6:
            return f"Usage: {cmd_type} [ticker] [call/put] [strike_price] [order_type] [quantity] (optional: [lmt_price] [stp_price])"

        ticker = parts[1].upper()
        option_type = parts[2].upper()
        try:
            strike_price = float(parts[3])
        except ValueError:
            return "Invalid strike price. Must be a number."
        order_type = parts[4].upper()
        try:
            quantity = int(parts[5])
        except ValueError:
            return "Invalid quantity. Must be an integer."

        if option_type not in ["CALL", "PUT"]:
            return "Invalid option type. Must be CALL or PUT."

        if order_type == "MKT":
            return f"Placing market order: {cmd_type.capitalize()} {quantity} {ticker} {option_type} {strike_price}"
        elif order_type == "LMT":
            if len(parts) < 7:
                return f"Limit order requires a limit price. Usage: {cmd_type} [ticker] [call/put] [strike_price] LMT [quantity] [lmt_price]"
            try:
                lmt_price = float(parts[6])
            except ValueError:
                return "Invalid limit price. Must be a number."
            return f"Placing limit order: {cmd_type.capitalize()} {quantity} {ticker} {option_type} {strike_price} at {lmt_price}"
        elif order_type == "LMT_STP":
            if len(parts) < 8:
                return f"Stop limit order requires limit and stop prices. Usage: {cmd_type} [ticker] [call/put] [strike_price] LMT STP [quantity] [lmt_price] [stp_price]"
            try:
                lmt_price = float(parts[6])
                stp_price = float(parts[7])
            except ValueError:
                return "Invalid price values. Both limit and stop prices must be numbers."
            return f"Placing stop-limit order: {cmd_type.capitalize()} {quantity} {ticker} {option_type} {strike_price} at {lmt_price}, stop price {stp_price}"
        else:
            return "Invalid order type. Allowed types: MKT, LMT, LMT STP"
    
    elif cmd_type == "!help":
        return """
        Available Commands:
        !balance: View account balance
        !position: View current position
        !liquidate: Force liquidation
        !buy: Buy stock
        !sell: Sell stock
        !opt_buy: Buy option
        !opt_sell: Sell option
        
        Type '!buy -h', '!sell -h', '!opt_buy -h', or '!opt_sell -h' for command-specific help.
        """

    return "Unknown command."
