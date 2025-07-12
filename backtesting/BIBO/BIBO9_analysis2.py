import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

# Load your file (adjust path as needed)
df = pd.read_csv("bibo9.csv")


def parse_strategy_block(block_lines):
    data = {}
    for line in block_lines:
        if m := re.search(r'Initial Capital:\s*(\d+)', line):
            data['Initial Capital'] = float(m.group(1))
        elif m := re.search(r'Risk Amount:\s*([\d.]+)', line):
            data['Risk Amount'] = float(m.group(1))
        elif m := re.search(r'SL Multiple:\s*([\d.]+)', line):
            # Collect SL multiples in a list, so you can decide which is SL and which is TP
            data.setdefault('SL Multiples', []).append(float(m.group(1)))
        elif m := re.search(r'TP Multiple:\s*([\d.]+)', line):
            data['TP Multiple'] = float(m.group(1))
        elif m := re.search(r'Total PnL:\s*([-\d.]+)', line):
            data['Total PnL'] = float(m.group(1))
        elif m := re.search(r'Win Rate:\s*([\d.]+)%', line):
            data['Win Rate (%)'] = float(m.group(1))
        elif m := re.search(r'Average PnL:\s*([-\d.]+)', line):
            data['Average PnL'] = float(m.group(1))
        elif m := re.search(r'Average Bars Held:\s*([\d.]+)', line):
            data['Average Bars Held'] = float(m.group(1))
        elif m := re.search(r'% Change:\s*([-\d.]+)%', line):
            data['% Change'] = float(m.group(1))
        elif m := re.search(r'Max Drawdown \(%\):\s*([\d.]+)', line):
            data['Max Drawdown (%)'] = float(m.group(1))
    # Now decide SL and TP multiples:
    sl_mults = data.get('SL Multiples', [])
    if len(sl_mults) == 2:
        data['SL Mult'] = sl_mults[0]
        data['TP Mult'] = sl_mults[1]
    elif len(sl_mults) == 1:
        data['SL Mult'] = sl_mults[0]
        data['TP Mult'] = None
    else:
        data['SL Mult'] = None
        data['TP Mult'] = None
    # Remove the temporary list
    if 'SL Multiples' in data:
        del data['SL Multiples']
    return data


# Example usage:
records = []
block_size = 14  # or number of lines per block (from your data)
num_blocks = len(df) // block_size

for i in range(num_blocks):
    block = df.iloc[i*block_size:(i+1)*block_size]['Strategy Description:'].tolist()
    try:
        parsed = parse_strategy_block(block)
        records.append(parsed)
    except Exception as e:
        print(f"Error parsing block {i}: {e}")
        print("Block contents:", block)
        continue

parsed_df = pd.DataFrame(records)

# Filter for strategies with > 80% change
high_growth_df = parsed_df[parsed_df['% Change'] > 80]

# # Plot all available statistics in the summary
# summary_stats = [
#     'Total PnL', 'Win Rate (%)', 'Average PnL', 'Average Bars Held',
#     '% Change', 'Max Drawdown (%)'
# ]
#
# # Create pairplot for all summary stats
# sns.pairplot(high_growth_df[summary_stats].dropna())
# plt.suptitle("Summary Statistics for Strategies with >80% Change", y=1.02)
# plt.tight_layout()
# plt.show()

high_win_df = parsed_df[parsed_df['Win Rate (%)'] > 20]
high_win_df = high_win_df[high_win_df['Total PnL'] > 10000]
print(high_win_df)
print(high_win_df.iloc[1])
print(high_win_df.iloc[3])
print(high_win_df.iloc[4])
