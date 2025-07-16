

import sys

import account.authentication_paper as auth
from account.authentication_paper import client, historicalClient
import portfolio.watchlists as watchlists
import portfolio.portfolio as portfolio
import algorithm.algorithm1.algorithm1 as alg1

#get all watchlists
# allWatchlists = watchlists.getAllWatchlists()
# print(allWatchlists)

alg1.trader("alg1Watchlist")


















# #get all watchlists
# allWatchlists = watchlists.getAllWatchlists()
# print(allWatchlists)


# #get symbols in watchlist
# testSymbols = watchlists.getWatchlistSymbols("alg1Watchlist")
# print(testSymbols)


# #demo all
# watchlists.createWatchlist('demo', ['AMD', 'AAPL'])
# watchlists.createWatchlist('watch', ['WM', 'WMT'])
# #show all watchlists
# watchlists.showAllWatchlists()
# watchlists.addToWatchlist('demo', 'demo',['QQQ'])
# #show specific watchlist
# watchlists.showWatchlist('demo')
# #delete symbol in watchlist
# watchlists.deleteFromWatchlist('watch', 'WM')
# watchlists.showWatchlist('watch')
# #delete watchlist
# watchlists.deleteWatchlist('watch', 'yes')
# watchlists.showAllWatchlists()
# watchlists.deleteWatchlist("demo", "yes")
# watchlists.showAllWatchlists()


# #get all account info
# portfolio.showAccountInfo()








