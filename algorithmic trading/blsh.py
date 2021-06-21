import time
from kiteconnect import KiteConnect
from paths import *
import pandas as pd
import datetime as dt
import numpy as np
import nsepy
import sys

"""
blsh - buy low sell high
"""

"""
1. lauches at 9:00 *
2. Authorize CDSL *
3. sell previous days stock if price per share has increased > 0.05
4. At 15:29 
"""


class tradx_driver:

    def __init__(self):
        print("Initialized TradeX driver\n")

    def get_holdings_info(self):
        data = kite.holdings()
        try:
            holds = pd.DataFrame(data[0], index=[0])
        except:
            holds = pd.DataFrame(data[0])
        holds = holds[["tradingsymbol", "product", "quantity", "average_price", "last_price", "pnl"]]
        return holds

    def get_positions_info(self):
        data = kite.positions()
        net = pd.DataFrame(data['net'])
        day = pd.DataFrame(data['day'])
        positions = day[["tradingsymbol", "product", "quantity", "average_price", "last_price", "pnl"]]
        return positions

    def get_orders_info(self):
        data = kite.orders()
        order = pd.DataFrame(data)
        order = order[["tradingsymbol", "order_type", "status", "transaction_type", "product", "quantity", "price"]]
        return order

    def place_cnc_order(self, symbol, buy_sell, quantity):
        # Place an intraday market order on NSE
        if buy_sell == "buy":
            t_type = kite.TRANSACTION_TYPE_BUY
        elif buy_sell == "sell":
            t_type = kite.TRANSACTION_TYPE_SELL
        kite.place_order(tradingsymbol=symbol,
                         exchange=kite.EXCHANGE_NSE,
                         transaction_type=t_type,
                         quantity=quantity,
                         order_type=kite.ORDER_TYPE_MARKET,
                         product=kite.PRODUCT_CNC,
                         variety=kite.VARIETY_REGULAR)

    def place_limit_order(self, symbol, buy_sell, quantity, price):
        # Place an intraday market order on NSE
        if buy_sell == "buy":
            t_type = kite.TRANSACTION_TYPE_BUY
        elif buy_sell == "sell":
            t_type = kite.TRANSACTION_TYPE_SELL
        kite.place_order(tradingsymbol=symbol,
                         exchange=kite.EXCHANGE_NSE,
                         transaction_type=t_type,
                         quantity=quantity,
                         order_type=kite.ORDER_TYPE_LIMIT,
                         product=kite.PRODUCT_CNC,
                         variety=kite.VARIETY_REGULAR,
                         price=price)


tradable_instruments = ["PNB", "UNIONBANK"]
print("Tradx will be using: {} for blsh algo\n".format(tradable_instruments))

access_token = open(access_token_path, "r").read()
key_secret = open(auth_details_path, 'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)
print("kite object initialized\n")

tx = tradx_driver()

year = dt.datetime.now().year
month = dt.datetime.now().month
day = dt.datetime.now().day

start_time = dt.datetime(year=year, month=month, day=day, hour=9, minute=15, second=00)
end_time = dt.datetime(year=year, month=month, day=day, hour=15, minute=30, second=00)
buy_time = dt.datetime(year=year, month=month, day=day, hour=15, minute=29, second=00)
sell_time = dt.datetime(year=year, month=month, day=day, hour=9, minute=40, second=00)

buy_pending = True

print("\nStart time: {} | end time:{}\n".format(start_time, end_time))
holdings = tx.get_holdings_info()
to_sell = holdings["tradingsymbol"].tolist()
to_buy = np.setdiff1d(tradable_instruments, to_sell)
sold = []

print("\nHOLDINDS\n{}\n".format(holdings))

while start_time < dt.datetime.now() < end_time:

    time.sleep(1)

    # SELL
    while dt.datetime.now() < sell_time and len(to_sell) > 0:
        for inst in to_sell:
            if holdings[holdings["tradingsymbol"] == inst]["pnl"][0] > 0:
                quantity = holdings[holdings["tradingsymbol"] == inst]["quantity"][0]
                tx.place_cnc_order(inst, "sell", quantity)
                sold.append(inst)
                print("SOLD {} with pnl:{}".format(inst, holdings[holdings["tradingsymbol"] == inst]["pnl"][0]))
        to_sell = np.setdiff1d(to_sell, sold)
        if not to_sell:
            break

    # BUY
    if buy_time <= dt.datetime.now() and buy_pending:
        holdings = tx.get_holdings_info()
        for inst in to_buy:
            tx.place_cnc_order(inst, "buy", 1)
            print("\n Order placed - {}")
            buy_pending = False

    sys.stdout.write('\r' + str(dt.datetime.now()))
