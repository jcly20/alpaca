import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('bibo8.20.csv')

# Clean column headers
df.columns = df.columns.str.strip()

# Parse EntryDate with coercion
df['EntryDate'] = pd.to_datetime(df['EntryDate'], errors='coerce')

# Drop rows where EntryDate couldn't be parsed
df = df.dropna(subset=['EntryDate'])

# Sort by EntryDate
df = df.sort_values('EntryDate')

# Starting capital
initial_capital = 10000

# Compute equity curve
df['Equity'] = initial_capital + df['PnL'].cumsum()

# Plot equity curve
plt.figure(figsize=(12,6))
plt.plot(df['EntryDate'], df['Equity'], label='Equity Curve')
plt.title('Equity Curve Over Time')
plt.xlabel('Trade Date')
plt.ylabel('Portfolio Value ($)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
