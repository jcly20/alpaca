

import sys

import account.authentication as auth
import portfolio.watchlists as watchlists
import portfolio.portfolio as portfolio


#load login credentials from enviroment
email, password, paperAcc, liveAcc, paperAccUUID, accUUID, api_key, secret_key = auth.load_credentials()

#create client
try:
    client = auth.load_client(email, api_key, secret_key)
except Exception as error:
    print("error creating client ...\nexiting program ...\ngoodbye!")
    sys.exit(error)

#get all watchlists
allWatchlists = watchlists.getAllWatchlists(client)
print(allWatchlists)


#get symbols in watchlist
testSymbols = watchlists.getWatchlistSymbols(client, "alg1Watchlist")
print(testSymbols)


# #demo all
# watchlists.createWatchlist(client, 'demo', ['AMD', 'AAPL'])
# watchlists.createWatchlist(client, 'watch', ['WM', 'WMT'])
# #show all watchlists
# watchlists.showAllWatchlists(client)
# watchlists.addToWatchlist(client, 'demo', 'demo',['QQQ'])
# #show specific watchlist
# watchlists.showWatchlist(client, 'demo')
# #delete symbol in watchlist
# watchlists.deleteFromWatchlist(client, 'watch', 'WM')
# watchlists.showWatchlist(client, 'watch')
# #delete watchlist
# watchlists.deleteWatchlist(client, 'watch', 'yes')
# watchlists.showAllWatchlists(client)
# watchlists.deleteWatchlist(client, "demo", "yes")
# watchlists.showAllWatchlists(client)


#get all account info
portfolio.showAccountInfo(client)






