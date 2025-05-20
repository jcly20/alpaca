
from alpaca.common import APIError
from alpaca.trading.requests import CreateWatchlistRequest, UpdateWatchlistRequest


def getAllWatchlists(client) :
    allWatchlists = []
    watchlists = client.get_watchlists()

    for i in range(0, len(watchlists)) :
        watchlist = client.get_watchlist_by_id(watchlists[i].id)
        symbols = []
        for j in watchlist.assets :
            symbols.append(j.symbol)

        allWatchlists.append({"id":watchlists[i].id, "name":watchlists[i].name, "symbols":symbols})

    return allWatchlists


def showAllWatchlists(client) :
    watchlists = client.get_watchlists()
    ids = {}
    symbols = {}

    for i in range(0, len(watchlists)) :
        watchlist = client.get_watchlist_by_id(watchlists[i].id)
        symbolList = []
        for j in watchlist.assets :
            symbolList.append(j.symbol)
        ids.update({watchlist.name:watchlist.id})
        symbols.update({watchlist.name:symbolList})
        print("\n", watchlist.name, "  ", watchlist.id, "\n\t", symbolList)


def createWatchlist(client, name, symbols) :
    watchlistData = CreateWatchlistRequest(
        name=name,
        symbols=symbols
    )

    try:
        client.create_watchlist(watchlist_data=watchlistData)
        return "success"

    except APIError as e:
        print(f"API error: {e}")
        return "error"

    except Exception as e:
        print(f"Unexpected error: {e}")
        return "error"


def getWatchlistID(client, name):
    watchlists = client.get_watchlists()
    ids = {}

    for i in range(0, len(watchlists)):
        watchlist = client.get_watchlist_by_id(watchlists[i].id)
        ids.update({watchlist.name: watchlist.id})

    return ids[name]


def getWatchlistSymbols(client, name):
    id = getWatchlistID(client, name)
    watchlist = client.get_watchlist_by_id(id)
    symbols = []

    for j in watchlist.assets:
        symbols.append(j.symbol)

    return symbols


def showWatchlist(client, name) :
    id = getWatchlistID(client, name)
    symbols = getWatchlistSymbols(client, name)

    print("\n", name, "  ", id, "\n\t", symbols)


def addToWatchlist(client, name, newName, symbols):
    id = getWatchlistID(client, name)
    oldSymbols = getWatchlistSymbols(client, name)
    oldSymbols.extend(symbols)

    watchlistData = UpdateWatchlistRequest(
        name=newName,
        symbols=oldSymbols
    )

    try:
        client.update_watchlist_by_id(watchlist_id=id, watchlist_data=watchlistData)
        return "success"

    except APIError as e:
        print(f"API error: {e}")
        return "error"

    except Exception as e:
        print(f"Unexpected error: {e}")
        return "error"


def deleteFromWatchlist(client, name, symbol):
    id = getWatchlistID(client, name)

    try:
        client.remove_asset_from_watchlist_by_id(id, symbol)
        return "success"

    except APIError as e:
        print(f"API error: {e}")
        return "error"

    except Exception as e:
        print(f"Unexpected error: {e}")
        return "error"


def deleteWatchlist(client, name, sure):
    id = getWatchlistID(client, name)

    if sure == 'yes':
        try:
            client.delete_watchlist_by_id(id)
            return "success"

        except APIError as e:
            print(f"API error: {e}")
            return "error"

        except Exception as e:
            print(f"Unexpected error: {e}")
            return "error"

