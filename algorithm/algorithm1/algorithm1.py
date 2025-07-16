#algortihm 1
#test/demo algorithm

import sys
import time
from datetime import datetime

import account.authentication_paper as auth
from account.authentication_paper import client, historicalClient
import portfolio.watchlists as watchlists
import portfolio.portfolio as portfolio
import algorithm.tradingObjects.candle as candle

from alpaca.trading.requests import MarketOrderRequest, OrderRequest, TakeProfitRequest, StopLossRequest, TrailingStopOrderRequest, LimitOrderRequest
from alpaca.data.requests import StockLatestQuoteRequest, StockQuotesRequest, StockBarsRequest, StockSnapshotRequest
from alpaca.data.historical.stock import StockHistoricalDataClient


def trader(watchlistName):

    print(client.get_account())
    request_params = StockSnapshotRequest(symbol_or_symbols="AMD")
    snapshot = historicalClient.get_stock_snapshot(request_params)
    print(snapshot)

    print(f"launching < algorithm1 > trader ...\nscanning symbols in < {watchlistName} >\nsymbols: {watchlists.getWatchlistSymbols(watchlistName)}\n")

    print(f"checking market hours ...")
    if openMarket():
        print("market is OPEN ...\nrunning trader ...")
        #run trader
        symbols = watchlists.getWatchlistSymbols(watchlistName)
        marketScan(symbols)
    else:
        print("market is CLOSED ...\nclosing trader ...\ngoodbye!")


def openMarket():

    return  client.get_clock().is_open


def panicMode(error):

    client.close_all_positions(cancel_orders=True)
    sys.exit(str(error))


def signalScan(data, symbols):

    for i in range(0, len(symbols)):
        currentBar = len(data[i]) - 1
        previousBar = currentBar - 1
        dblpreviousBar = currentBar - 2

        if data[i][currentBar].close > data[i][previousBar].close > data[i][dblpreviousBar].close :
            print('buy', symbols[i])
            price = data[i][currentBar].lastPrice
            takeProfit = TakeProfitRequest(
                limit_price = round(price * 1.005, 2)
            )
            stopLoss = StopLossRequest(
                stop_price = round(price * .9975, 2)
            )
            orderRequest = LimitOrderRequest(
                symbol = symbols[i],
                qty = 1,
                side = 'buy',
                type = 'limit',
                time_in_force = 'gtc',
                order_class = 'bracket',
                take_profit = takeProfit,
                stop_loss = stopLoss,
                limit_price=round(price * 1.001, 2)
            )
            order = client.submit_order(order_data=orderRequest)


def marketScan(symbols) :

    symbolLen = rows = len(symbols)
    data = [[] for _ in range(symbolLen)]

    try :

        while openMarket():

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] scanning market\n")

            for i in range(0, symbolLen) :
                priceRequest = StockSnapshotRequest(
                    symbol_or_symbols=symbols[i],
                )
                latestData = historicalClient.get_stock_snapshot(priceRequest)
                openPrice = latestData[symbols[i]].minute_bar.open
                highPrice = latestData[symbols[i]].minute_bar.high
                lowPrice = latestData[symbols[i]].minute_bar.low
                closePrice = latestData[symbols[i]].minute_bar.close
                lastPrice = latestData[symbols[i]].latest_trade.price
                bar = candle.Candle(openPrice, highPrice, lowPrice, closePrice, lastPrice)
                data[i].append(bar)

            if len(data[0]) >= 3:
                signalScan(data, symbols)

            time.sleep(5)

    except Exception as error:
        print("\nan error in program\nclosing all positions")
        panicMode(error)
