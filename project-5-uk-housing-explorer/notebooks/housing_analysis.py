#!/usr/bin/env python3
"""
UK Housing Market Explorer
============================
Combine simulated HM Land Registry price-paid data with ONS income statistics
to explore housing affordability across UK regions.

Tools: Python (Pandas, Matplotlib), SQL, Power BI-ready exports
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3

np.random.seed(42)

print("=" * 60)
print("PROJECT 5: UK Housing Market Explorer")
print("=" * 60)

# ============================================================
# 1. GENERATE UK HOUSING DATA
# ============================================================

regions = {
    'London': {'avg_price': 520000, 'avg_income': 44000, 'growth_rate': 0.04},
    'South East': {'avg_price': 375000, 'avg_income': 38000, 'growth_rate': 0.045},
    'East of England': {'avg_price': 330000, 'avg_income': 35000, 'growth_rate': 0.04},
    'South West': {'avg_price': 305000, 'avg_income': 32000, 'growth_rate': 0.05},
    'West Midlands': {'avg_price': 230000, 'avg_income': 30000, 'growth_rate': 0.035},
    'East Midlands': {'avg_price': 220000, 'avg_income': 29500, 'growth_rate': 0.04},
    'North West': {'avg_price': 200000, 'avg_income': 30000, 'growth_rate': 0.045},
    'Yorkshire': {'avg_price': 195000, 'avg_income': 28500, 'growth_rate': 0.04},
    'North East': {'avg_price': 155000, 'avg_income': 27000, 'growth_rate': 0.03},
    'Wales': {'avg_price': 195000, 'avg_income': 27500, 'growth_rate': 0.055},
    'Scotland': {'avg_price': 185000, 'avg_income': 30500, 'growth_rate': 0.04},
    'Northern Ireland': {'avg_price': 170000, 'avg_income': 27000, 'growth_rate': 0.05},
}

property_types = {'Detached': 1.6, 'Semi-Detached': 1.0, 'Terraced': 0.75, 'Flat': 0.55}
years = range(2018, 2025)
months = range(1, 13)

# Generate property transactions
n_transactions = 50000
records = []
for i in range(n_transactions):
    region = np.random.choice(list(regions.keys()), p=[0.15, 0.12, 0.09, 0.08, 0.08, 0.07, 0.1, 0.08, 0.05, 0.06, 0.07, 0.05])
    year = np.random.choice(list(years))
    month = np.random.randint(1, 13)
    prop_type = np.random.choice(list(property_types.keys()), p=[0.2, 0.3, 0.3, 0.2])
    
    reg = regions[region]
    year_factor = (1 + reg['growth_rate']) ** (year - 2018)
    
    # COVID dip in 2020, stamp duty holiday bounce 2021
    if year == 2020 and month <= 6:
        year_factor *= 0.95
    elif year == 2021:
        year_factor *= 1.08
    elif year == 2023:
        year_factor *= 0.97  # rate rise impact
    
    base_price = reg['avg_price'] * property_types[prop_type] * year_factor
    price = max(50000, int(np.random.lognormal(np.log(base_price), 0.3)))
    
    new_build = np.random.binomial(1, 0.15)
    
    records.append({
        'transaction_id': f'TX-{i+1:06d}',
        'date': f'{year}-{month:02d}-{np.random.randint(1,29):02d}',
        'year': year,
        'month': month,
        'price_gbp': price,
        'property_type': prop_type,
        'new_build': new_build,
        'region': region,
        'postcode_area': f'{region[:2].upper()}{np.random.randint(1,30)}',
    })

transactions = pd.DataFrame(records)
transactions['date'] = pd.to_datetime(transactions['date'], errors='coerce')
transactions.to_csv('data/uk_house_prices.csv', index=False)
print(f"\nTransactions: {len(transactions):,}")
print(f"Avg price: £{transactions['price_gbp'].mean():,.0f}")

# Income data
income_records = []
for region, data in regions.items():
    for year in years:
        growth = 1 + np.random.uniform(0.01, 0.04)
        income = data['avg_income'] * (growth ** (year - 2018))
        income_records.append({
            'region': region, 'year': year,
            'median_income': round(income),
            'lower_quartile_income': round(income * 0.65),
            'upper_quartile_income': round(income * 1.45),
        })

income_df = pd.DataFrame(income_records)
income_df.to_csv('data/regional_incomes.csv', index=False)
print(f"Income records: {len(income_df)}")

# ============================================================
# 2. SQL DATABASE
# ============================================================

conn = sqlite3.connect('data/uk_housing.db')
transactions.to_sql('transactions', conn, if_exists='replace', index=False)
income_df.to_sql('incomes', conn, if_exists='replace', index=False)

conn.execute("""
CREATE VIEW IF NOT EXISTS affordability AS
SELECT 
    t.region,
    t.year,
    ROUND(AVG(t.price_gbp), 0) AS avg_house_price,
    i.median_income,
    ROUND(CAST(AVG(t.price_gbp) AS FLOAT) / i.median_income, 1) AS price_to_income_ratio,
    COUNT(*) AS num_transactions
FROM transactions t
JOIN incomes i ON t.region = i.region AND t.year = i.year
GROUP BY t.region, t.year
ORDER BY t.region, t.year;
""")
conn.commit()
print("✓ SQLite database created")

# ============================================================
# 3. ANALYSIS & VISUALISATIONS
# ============================================================

fig_dir = 'visualisations'
sns.set_theme(style='whitegrid')

# --- Chart 1: Average Price by Region ---
regional_avg = transactions.groupby('region')['price_gbp'].mean().sort_values()
fig, ax = plt.subplots(figsize=(12, 8))
colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.9, len(regional_avg)))
ax.barh(regional_avg.index, regional_avg.values, color=colors)
ax.set_title('Average House Price by UK Region', fontsize=14, fontweight='bold')
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))
plt.tight_layout()
plt.savefig(f'{fig_dir}/01_regional_prices.png', dpi=150)
plt.close()
print("✓ Chart 1: Regional prices")

# --- Chart 2: Price Trends Over Time ---
yearly_region = transactions.groupby(['year', 'region'])['price_gbp'].mean().reset_index()
fig, ax = plt.subplots(figsize=(14, 7))
for region in ['London', 'South East', 'North West', 'Scotland', 'North East', 'Wales']:
    data = yearly_region[yearly_region['region'] == region]
    ax.plot(data['year'], data['price_gbp'], marker='o', linewidth=2, label=region)
ax.set_title('House Price Trends by Region (2018-2024)', fontsize=14, fontweight='bold')
ax.set_ylabel('Average Price (£)')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/02_price_trends.png', dpi=150)
plt.close()
print("✓ Chart 2: Price trends")

# --- Chart 3: Affordability Ratio ---
afford = pd.read_sql("SELECT * FROM affordability", conn)
latest = afford[afford['year'] == 2024].sort_values('price_to_income_ratio')
fig, ax = plt.subplots(figsize=(12, 8))
colors = ['#DC2626' if x > 10 else '#F97316' if x > 8 else '#22C55E' for x in latest['price_to_income_ratio']]
ax.barh(latest['region'], latest['price_to_income_ratio'], color=colors)
ax.axvline(x=8, color='#333', linestyle='--', alpha=0.5, label='Historically "affordable" threshold')
ax.set_title('Housing Affordability: Price-to-Income Ratio (2024)', fontsize=14, fontweight='bold')
ax.set_xlabel('House Price ÷ Median Income')
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/03_affordability.png', dpi=150)
plt.close()
print("✓ Chart 3: Affordability ratio")

# --- Chart 4: Property Type Distribution ---
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
type_price = transactions.groupby('property_type')['price_gbp'].mean().sort_values()
type_price.plot(kind='barh', ax=axes[0], color='#6366F1')
axes[0].set_title('Avg Price by Property Type', fontweight='bold')
axes[0].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))

type_count = transactions['property_type'].value_counts()
axes[1].pie(type_count, labels=type_count.index, autopct='%1.1f%%', colors=['#3B82F6', '#10B981', '#F59E0B', '#EC4899'])
axes[1].set_title('Transaction Volume by Type', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{fig_dir}/04_property_types.png', dpi=150)
plt.close()
print("✓ Chart 4: Property types")

# --- Chart 5: Affordability Over Time Heatmap ---
afford_pivot = afford.pivot(index='region', columns='year', values='price_to_income_ratio')
fig, ax = plt.subplots(figsize=(14, 8))
sns.heatmap(afford_pivot, annot=True, fmt='.1f', cmap='RdYlGn_r', linewidths=0.5, ax=ax, vmin=4, vmax=14)
ax.set_title('Housing Affordability Ratio by Region & Year', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{fig_dir}/05_affordability_heatmap.png', dpi=150)
plt.close()
print("✓ Chart 5: Affordability heatmap")

# --- Chart 6: Price Distribution ---
fig, ax = plt.subplots(figsize=(14, 6))
for region in ['London', 'North West', 'Scotland']:
    data = transactions[transactions['region'] == region]['price_gbp']
    ax.hist(data, bins=50, alpha=0.5, label=region, density=True)
ax.set_title('House Price Distribution: London vs North West vs Scotland', fontsize=14, fontweight='bold')
ax.set_xlabel('Price (£)')
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))
ax.legend()
ax.set_xlim(0, 1500000)
plt.tight_layout()
plt.savefig(f'{fig_dir}/06_price_distribution.png', dpi=150)
plt.close()
print("✓ Chart 6: Price distribution")

# Power BI exports
afford.to_csv('data/powerbi_affordability.csv', index=False)

conn.close()
print("\n" + "=" * 60)
print("PROJECT 5 COMPLETE")
print("=" * 60)
