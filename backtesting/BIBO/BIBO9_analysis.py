import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

# Load your file (adjust path as needed)
df = pd.read_csv("bibo9.csv")

# Group rows into blocks of 10 (each strategy is 10 lines)
block_size = 10
num_blocks = len(df) // block_size

records = []

for i in range(num_blocks):
    block = df.iloc[i*block_size:(i+1)*block_size]['Strategy Description:'].tolist()
    try:
        initial_cap = float(re.search(r'Initial Capital:\s*(\d+)', block[0]).group(1))
        risk = float(re.search(r'Risk Amount:\s*([\d.]+)', block[1]).group(1))
        sl = float(re.search(r'SL Multiple:\s*([\d.]+)', block[2]).group(1))
        tp = float(re.search(r'SL Multiple:\s*([\d.]+)', block[3]).group(1))  # second SL line = TP
        total_pnl = float(re.search(r'Total PnL:\s*([-\.\d]+)', block[5]).group(1))
        win_rate = float(re.search(r'Win Rate:\s*([\d.]+)%', block[6]).group(1))
        avg_pnl = float(re.search(r'Average PnL:\s*([-\.\d]+)', block[7]).group(1))
        avg_bars = float(re.search(r'Average Bars Held:\s*([\d.]+)', block[8]).group(1))
        pct_change = float(re.search(r'% Change:\s*([-\.\d]+)%', block[9]).group(1))

        # Try to get max drawdown if it exists
        dd_match = re.search(r'Max Drawdown \(%\):\s*([\d.]+)', block[9])
        max_dd = float(dd_match.group(1)) if dd_match else None

        records.append({
            'Initial Capital': initial_cap,
            'Risk Amount': risk,
            'SL Mult': sl,
            'TP Mult': tp,
            'Total PnL': total_pnl,
            'Win Rate (%)': win_rate,
            'Average PnL': avg_pnl,
            'Average Bars Held': avg_bars,
            '% Change': pct_change,
            'Max Drawdown (%)': max_dd
        })

    except Exception as e:
        print(f"Error parsing block {i}: {e}")
        continue

# Create DataFrame
parsed_df = pd.DataFrame(records)

# Filter for PnL > 5000
high_pnl_df = parsed_df[parsed_df["Total PnL"] > 5000]

# Pivot table for heatmap
pivot = high_pnl_df.pivot_table(index="TP Mult", columns="SL Mult", values="Total PnL", aggfunc="mean")

# Plot heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="RdYlGn", cbar_kws={'label': 'Avg Total PnL'})
plt.title("TP vs SL Multiples (Filtered: PnL > 5000)")
plt.xlabel("SL Multiplier")
plt.ylabel("TP Multiplier")
plt.tight_layout()
plt.show()

# Scatter Plot 1: Win Rate vs Total PnL
plt.figure(figsize=(8, 5))
sns.scatterplot(data=parsed_df, x="Win Rate (%)", y="Total PnL", hue="Risk Amount", palette="viridis")
plt.title("Win Rate vs Total PnL")
plt.xlabel("Win Rate (%)")
plt.ylabel("Total PnL")
plt.legend(title="Risk")
plt.tight_layout()
plt.show()

# Scatter Plot 2: Risk Amount vs % Change
plt.figure(figsize=(8, 5))
sns.scatterplot(data=parsed_df, x="Risk Amount", y="% Change", hue="Total PnL", palette="coolwarm")
plt.title("Risk Amount vs % Change")
plt.xlabel("Risk Amount")
plt.ylabel("% Change")
plt.legend(title="Total PnL")
plt.tight_layout()
plt.show()

# Scatter Plot 3: SL vs TP Multiples for strategies with PnL > 5000
plt.figure(figsize=(8, 5))
sns.scatterplot(data=high_pnl_df, x="SL Mult", y="TP Mult", size="Total PnL", hue="Total PnL", palette="Spectral", sizes=(20, 200))
plt.title("SL vs TP Multiples (PnL > 5000)")
plt.xlabel("SL Mult")
plt.ylabel("TP Mult")
plt.legend(title="Total PnL", loc='best')
plt.tight_layout()
plt.show()

# Scatter Plot 4: Risk vs Drawdown
plt.figure(figsize=(8, 5))
sns.scatterplot(data=parsed_df, x="Risk Amount", y="Max Drawdown (%)", hue="Total PnL", palette="plasma")
plt.title("Risk Amount vs Max Drawdown")
plt.xlabel("Risk Amount")
plt.ylabel("Max Drawdown (%)")
#plt.legend(title="Total PnL")
plt.tight_layout()
plt.show()
