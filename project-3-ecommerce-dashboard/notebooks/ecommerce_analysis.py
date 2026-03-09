#!/usr/bin/env python3
"""
E-commerce Sales & Marketing Dashboard
========================================
Analysis for a fictional UK online retailer tracking KPIs like revenue,
conversion rates, average order value, and marketing channel performance.

Tools: Python (Pandas), SQL, Power BI-ready exports
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
print("PROJECT 3: E-commerce Sales & Marketing Dashboard")
print("=" * 60)

# ============================================================
# 1. GENERATE UK E-COMMERCE DATA
# ============================================================

n_orders = 25000
dates = pd.date_range('2023-01-01', '2024-12-31', freq='h')
order_dates = np.random.choice(dates, n_orders)

categories = ['Electronics', 'Fashion', 'Home & Garden', 'Health & Beauty', 'Sports', 'Books & Media', 'Food & Drink']
cat_weights = [0.2, 0.22, 0.15, 0.13, 0.1, 0.1, 0.1]

uk_regions = ['London', 'South East', 'North West', 'West Midlands', 'Yorkshire', 'East of England', 'South West', 'East Midlands', 'North East', 'Scotland', 'Wales', 'Northern Ireland']
region_weights = [0.18, 0.14, 0.12, 0.09, 0.09, 0.08, 0.08, 0.07, 0.04, 0.05, 0.03, 0.03]

channels = ['Organic Search', 'Paid Search', 'Social Media', 'Email', 'Direct', 'Referral']
channel_weights = [0.28, 0.22, 0.18, 0.15, 0.1, 0.07]

devices = ['Mobile', 'Desktop', 'Tablet']
device_weights = [0.55, 0.35, 0.10]

categories_chosen = np.random.choice(categories, n_orders, p=cat_weights)
base_prices = {'Electronics': 85, 'Fashion': 45, 'Home & Garden': 60, 'Health & Beauty': 30, 'Sports': 55, 'Books & Media': 15, 'Food & Drink': 25}

order_values = []
for cat in categories_chosen:
    base = base_prices[cat]
    val = np.random.lognormal(np.log(base), 0.6)
    order_values.append(round(min(val, 2000), 2))

orders = pd.DataFrame({
    'order_id': [f'ORD-{i:06d}' for i in range(1, n_orders + 1)],
    'order_date': order_dates,
    'customer_id': [f'CUST-{np.random.randint(1, 8000):05d}' for _ in range(n_orders)],
    'category': categories_chosen,
    'order_value_gbp': order_values,
    'quantity': np.random.randint(1, 6, n_orders),
    'region': np.random.choice(uk_regions, n_orders, p=region_weights),
    'marketing_channel': np.random.choice(channels, n_orders, p=channel_weights),
    'device': np.random.choice(devices, n_orders, p=device_weights),
    'is_returning_customer': np.random.binomial(1, 0.4, n_orders),
    'discount_applied': np.random.binomial(1, 0.25, n_orders),
    'delivery_days': np.random.choice([1, 2, 3, 5, 7], n_orders, p=[0.1, 0.25, 0.35, 0.2, 0.1]),
    'returned': np.random.binomial(1, 0.08, n_orders),
})

orders['order_date'] = pd.to_datetime(orders['order_date'])
orders['revenue_gbp'] = (orders['order_value_gbp'] * orders['quantity'] * (1 - orders['returned'] * 0.95)).round(2)
orders['month'] = orders['order_date'].dt.to_period('M').astype(str)
orders['day_of_week'] = orders['order_date'].dt.day_name()
orders['hour'] = orders['order_date'].dt.hour

# Website sessions data
n_sessions = 150000
sessions = pd.DataFrame({
    'session_date': np.random.choice(pd.date_range('2023-01-01', '2024-12-31'), n_sessions),
    'channel': np.random.choice(channels, n_sessions, p=channel_weights),
    'device': np.random.choice(devices, n_sessions, p=device_weights),
    'pages_viewed': np.random.poisson(4, n_sessions).clip(1, 30),
    'session_duration_sec': np.random.exponential(180, n_sessions).clip(5, 3600).astype(int),
    'converted': np.random.binomial(1, 0.17, n_sessions),
    'bounced': np.random.binomial(1, 0.42, n_sessions),
})

orders.to_csv('data/ecommerce_orders.csv', index=False)
sessions.to_csv('data/website_sessions.csv', index=False)
print(f"\nOrders: {len(orders):,} | Sessions: {len(sessions):,}")
print(f"Total Revenue: £{orders['revenue_gbp'].sum():,.0f}")
print("✓ Data saved")

# ============================================================
# 2. SQL DATABASE
# ============================================================

conn = sqlite3.connect('data/ecommerce.db')
orders.to_sql('orders', conn, if_exists='replace', index=False)
sessions.to_sql('sessions', conn, if_exists='replace', index=False)
conn.commit()
print("✓ SQLite database created")

# ============================================================
# 3. ANALYSIS & VISUALISATIONS
# ============================================================

print("\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)

fig_dir = 'visualisations'
sns.set_theme(style='whitegrid')

# --- Chart 1: Monthly Revenue Trend ---
monthly_rev = orders.groupby('month')['revenue_gbp'].sum().reset_index()
fig, ax = plt.subplots(figsize=(14, 6))
ax.fill_between(range(len(monthly_rev)), monthly_rev['revenue_gbp'], alpha=0.2, color='#2563EB')
ax.plot(range(len(monthly_rev)), monthly_rev['revenue_gbp'], color='#2563EB', linewidth=2.5, marker='o', markersize=4)
ax.set_xticks(range(0, len(monthly_rev), 3))
ax.set_xticklabels(monthly_rev['month'].iloc[::3], rotation=45)
ax.set_title('Monthly Revenue Trend (2023-2024)', fontsize=14, fontweight='bold')
ax.set_ylabel('Revenue (£)')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))
plt.tight_layout()
plt.savefig(f'{fig_dir}/01_monthly_revenue.png', dpi=150)
plt.close()
print("✓ Chart 1: Monthly revenue")

# --- Chart 2: Revenue by Category ---
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
cat_rev = orders.groupby('category')['revenue_gbp'].sum().sort_values()
cat_rev.plot(kind='barh', ax=axes[0], color='#8B5CF6')
axes[0].set_title('Revenue by Category', fontweight='bold')
axes[0].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))

cat_aov = orders.groupby('category')['order_value_gbp'].mean().sort_values()
cat_aov.plot(kind='barh', ax=axes[1], color='#F59E0B')
axes[1].set_title('Avg Order Value by Category', fontweight='bold')
axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:.0f}'))
plt.tight_layout()
plt.savefig(f'{fig_dir}/02_category_performance.png', dpi=150)
plt.close()
print("✓ Chart 2: Category performance")

# --- Chart 3: Marketing Channel Performance ---
channel_perf = orders.groupby('marketing_channel').agg(
    orders_count=('order_id', 'count'),
    total_revenue=('revenue_gbp', 'sum'),
    avg_order_value=('order_value_gbp', 'mean')
).sort_values('total_revenue', ascending=False)

session_conv = sessions.groupby('channel')['converted'].mean() * 100

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
channel_perf['total_revenue'].plot(kind='bar', ax=axes[0], color='#10B981')
axes[0].set_title('Revenue by Marketing Channel', fontweight='bold')
axes[0].set_ylabel('Revenue (£)')
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))
axes[0].tick_params(axis='x', rotation=45)

session_conv.sort_values().plot(kind='barh', ax=axes[1], color='#3B82F6')
axes[1].set_title('Conversion Rate by Channel', fontweight='bold')
axes[1].set_xlabel('Conversion Rate (%)')
plt.tight_layout()
plt.savefig(f'{fig_dir}/03_channel_performance.png', dpi=150)
plt.close()
print("✓ Chart 3: Channel performance")

# --- Chart 4: Device Split ---
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
device_orders = orders['device'].value_counts()
axes[0].pie(device_orders, labels=device_orders.index, autopct='%1.1f%%', colors=['#3B82F6', '#10B981', '#F59E0B'], startangle=90)
axes[0].set_title('Orders by Device', fontweight='bold')

device_aov = orders.groupby('device')['order_value_gbp'].mean()
axes[1].bar(device_aov.index, device_aov.values, color=['#3B82F6', '#10B981', '#F59E0B'])
axes[1].set_title('Avg Order Value by Device', fontweight='bold')
axes[1].set_ylabel('AOV (£)')
plt.tight_layout()
plt.savefig(f'{fig_dir}/04_device_analysis.png', dpi=150)
plt.close()
print("✓ Chart 4: Device analysis")

# --- Chart 5: Day of Week & Hour Patterns ---
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
daily = orders.groupby('day_of_week')['order_id'].count().reindex(day_order)
daily.plot(kind='bar', ax=axes[0], color='#8B5CF6')
axes[0].set_title('Orders by Day of Week', fontweight='bold')
axes[0].set_ylabel('Number of Orders')
axes[0].tick_params(axis='x', rotation=45)

hourly = orders.groupby('hour')['order_id'].count()
axes[1].fill_between(hourly.index, hourly.values, alpha=0.3, color='#EC4899')
axes[1].plot(hourly.index, hourly.values, color='#EC4899', linewidth=2)
axes[1].set_title('Orders by Hour of Day', fontweight='bold')
axes[1].set_xlabel('Hour')
axes[1].set_ylabel('Number of Orders')
plt.tight_layout()
plt.savefig(f'{fig_dir}/05_temporal_patterns.png', dpi=150)
plt.close()
print("✓ Chart 5: Temporal patterns")

# --- Chart 6: Regional Revenue ---
fig, ax = plt.subplots(figsize=(12, 7))
regional = orders.groupby('region')['revenue_gbp'].sum().sort_values()
regional.plot(kind='barh', ax=ax, color='#0EA5E9')
ax.set_title('Revenue by UK Region', fontsize=14, fontweight='bold')
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))
plt.tight_layout()
plt.savefig(f'{fig_dir}/06_regional_revenue.png', dpi=150)
plt.close()
print("✓ Chart 6: Regional revenue")

# KPI Summary
print(f"\n--- KPI SUMMARY ---")
print(f"Total Revenue: £{orders['revenue_gbp'].sum():,.0f}")
print(f"Total Orders: {len(orders):,}")
print(f"Avg Order Value: £{orders['order_value_gbp'].mean():.2f}")
print(f"Return Rate: {orders['returned'].mean():.1%}")
print(f"Returning Customer Rate: {orders['is_returning_customer'].mean():.1%}")
print(f"Overall Conversion Rate: {sessions['converted'].mean():.1%}")
print(f"Bounce Rate: {sessions['bounced'].mean():.1%}")

# Power BI exports
orders.to_csv('data/powerbi_orders.csv', index=False)
sessions.to_csv('data/powerbi_sessions.csv', index=False)

conn.close()
print("\n✓ Power BI-ready exports saved")
print("=" * 60)
print("PROJECT 3 COMPLETE")
print("=" * 60)
