import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf

def get_sp500_stocks():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')  # Use built-in HTML parser

    table = soup.find('table', {'id': 'constituents'})
    df = pd.read_html(str(table))[0]

    # Clean and rename columns
    df = df[['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry']]
    df.columns = ['Symbol', 'Company', 'Sector', 'Sub-Industry']

    return df

def enrich_with_yfinance(df):
    summaries = []
    for symbol in df['Symbol']:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            summaries.append({
                "Symbol": symbol,
                "Market Cap": info.get("marketCap"),
                "Volume": info.get("volume"),
                "Sector_YF": info.get("sector"),
                "Industry_YF": info.get("industry")
            })
        except Exception as e:
            summaries.append({
                "Symbol": symbol,
                "Market Cap": None,
                "Volume": None,
                "Sector_YF": None,
                "Industry_YF": None
            })
    return pd.DataFrame(summaries)

def merge_trade_stats(enriched_path, trade_stats_path):
    # Load enriched data and trade stats from CSVs
    df_enriched = pd.read_csv(enriched_path)
    stats_df = pd.read_csv(trade_stats_path)
    stats_df.columns = [col.strip() for col in stats_df.columns]  # Clean column names
    stats_df = stats_df.rename(columns={"Symbol": "Symbol", "Total Trades": "Total Trades", "Win Rate (%)": "Win Rate"})

    # Merge enriched data with trade stats
    df_combined = pd.merge(df_enriched, stats_df, on="Symbol", how="left")
    return df_combined


def add_market_cap_category(df):
    bins = [-float('inf'), 2e9, 10e9, 200e9, float('inf')]
    labels = ['Small Cap', 'Mid Cap', 'Large Cap', 'Mega Cap']
    df['Market Cap Category'] = pd.cut(df['Market Cap'], bins=bins, labels=labels)
    return df


def summarize_winners_losers_stats(merged_csv_path):
    df = pd.read_csv(merged_csv_path)
    df = add_market_cap_category(df)

    # Define winners and losers
    winners = df[(df['Total Trades'] > 5) & (df['Win Rate'] > 33)]
    losers = df[~((df['Total Trades'] > 5) & (df['Win Rate'] > 33))]

    def format_large_number(num):
        if pd.isna(num):
            return None
        elif num >= 1e12:
            return f"{num / 1e12:.2f}T"
        elif num >= 1e9:
            return f"{num / 1e9:.2f}B"
        elif num >= 1e6:
            return f"{num / 1e6:.2f}M"
        else:
            return f"{num:.2f}"


    def summary_stats(group):
        return {
            'Count': len(group),
            'Avg Volume': format_large_number(group['Volume'].mean()),
            'Max Volume': format_large_number(group['Volume'].max()),
            'Min Volume': format_large_number(group['Volume'].min()),
            'Avg Market Cap': format_large_number(group['Market Cap'].mean()),
            'Max Market Cap': format_large_number(group['Market Cap'].max()),
            'Min Market Cap': format_large_number(group['Market Cap'].min()),
            'Top Sectors': group['Sector'].value_counts().head(5).to_dict()
        }

    winner_stats = summary_stats(winners)
    loser_stats = summary_stats(losers)

    # Calculate winners and losers per Market Cap Category
    winners_by_cap = winners['Market Cap Category'].value_counts().to_dict()
    losers_by_cap = losers['Market Cap Category'].value_counts().to_dict()

    print("Winners Summary:")
    print(winner_stats)
    print("\nLosers Summary:")
    print(loser_stats)
    print("\nWinners by Market Cap Category:")
    print(winners_by_cap)
    print("\nLosers by Market Cap Category:")
    print(losers_by_cap)

    return {
        'winner_stats': winner_stats,
        'loser_stats': loser_stats,
        'winners_by_cap': winners_by_cap,
        'losers_by_cap': losers_by_cap,
    }


def filter_symbols(csv_path):
    df = pd.read_csv(csv_path)

    # Make sure Market Cap Category column exists, if not raise error
    if 'Market Cap Category' not in df.columns:
        raise ValueError("CSV must have a 'Market Cap Category' column")
    if 'Sector' not in df.columns:
        raise ValueError("CSV must have a 'Sector' column")

    excluded_sectors = ['Consumer Staples', 'Real Estate', 'Communication Services']
    included_caps = ['Large Cap', 'Mega Cap']

    filtered_df = df[
        (~df['Sector'].isin(excluded_sectors)) &
        (df['Market Cap Category'].isin(included_caps))
        ]

    return filtered_df['Symbol'].tolist()


def get_high_quality_symbols(csv_path):
    df = pd.read_csv(csv_path)
    filtered_df = df[(df['Total Trades'] > 11) & (df['Win Rate'] > 33)]
    return filtered_df['Symbol'].dropna().tolist()


if __name__ == "__main__":
    #df_sp500 = get_sp500_stocks()
    #df_enriched = enrich_with_yfinance(df_sp500)
    #df_enriched_full = pd.merge(df_sp500, df_enriched, on="Symbol", how="left")
    #df_enriched_full.to_csv("sp500_enriched.csv", index=False)

    # Add trade stats
    #df_final_with_stats = merge_trade_stats("sp500_companies_enriched.csv", "symbol_trade_stats.csv")
    #print(df_final_with_stats.head())
    #df_final_with_stats.to_csv("sp500_companies_enriched_with_stats.csv", index=False)

    #summarize_winners_losers_stats("sp500_companies_enriched_stats_cats.csv")

    #tradeList = filter_symbols("sp500_companies_enriched_stats_cats.csv")

    tradeList = get_high_quality_symbols("sp500_companies_enriched_stats_cats.csv")
    print(tradeList)
    print(len(tradeList))



