#!/usr/bin/env python3
"""
NHS A&E Wait Times Analysis
============================
Analyse NHS England A&E waiting times data to uncover trends in hospital
performance, seasonal patterns, and regional disparities across trusts.

Tools: Python (Pandas, Matplotlib, Seaborn), SQL, Tableau-ready exports
Data: Simulated based on real NHS England A&E statistics patterns
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import os
from datetime import datetime, timedelta

np.random.seed(42)

# ============================================================
# 1. GENERATE REALISTIC NHS A&E DATA
# ============================================================

print("=" * 60)
print("PROJECT 1: NHS A&E Wait Times Analysis")
print("=" * 60)

# NHS Regions and Trusts
regions = {
    'London': ['Barts Health NHS Trust', 'Imperial College Healthcare', 'Kings College Hospital', "Guy's and St Thomas'", 'University College London Hospitals'],
    'North West': ['Manchester University NHS Foundation Trust', 'Liverpool University Hospitals', 'Lancashire Teaching Hospitals', 'Bolton NHS Foundation Trust'],
    'Midlands': ['University Hospitals Birmingham', 'Nottingham University Hospitals', 'University Hospitals of Leicester', 'Coventry and Warwickshire'],
    'South East': ['Oxford University Hospitals', 'Brighton and Sussex', 'Royal Surrey NHS Foundation Trust', 'East Kent Hospitals'],
    'North East & Yorkshire': ['Newcastle upon Tyne Hospitals', 'Leeds Teaching Hospitals', 'Sheffield Teaching Hospitals', 'Hull University Teaching Hospitals'],
    'South West': ['University Hospitals Bristol', 'Royal Devon University Healthcare', 'Plymouth Hospitals NHS Trust'],
    'East of England': ['Cambridge University Hospitals', 'Norfolk and Norwich', 'Addenbrookes Hospital Trust'],
}

ae_types = ['Type 1 - Major A&E', 'Type 2 - Specialist', 'Type 3 - Minor Injuries']

months = pd.date_range('2021-01-01', '2024-12-01', freq='MS')

records = []
for month in months:
    for region, trusts in regions.items():
        for trust in trusts:
            for ae_type in ae_types:
                base_attendances = np.random.randint(3000, 15000) if ae_type == 'Type 1 - Major A&E' else np.random.randint(500, 4000)
                
                # Seasonal pattern: winter surge
                month_num = month.month
                if month_num in [12, 1, 2]:
                    seasonal_factor = 1.15 + np.random.uniform(0, 0.1)
                elif month_num in [6, 7, 8]:
                    seasonal_factor = 0.9 + np.random.uniform(0, 0.05)
                else:
                    seasonal_factor = 1.0 + np.random.uniform(-0.05, 0.05)
                
                # COVID impact 2021
                if month.year == 2021 and month.month <= 6:
                    seasonal_factor *= 0.75
                
                # Year-on-year growth in demand
                year_factor = 1 + (month.year - 2021) * 0.03
                
                attendances = int(base_attendances * seasonal_factor * year_factor)
                
                # 4-hour target performance (varies by trust quality and pressure)
                base_performance = np.random.uniform(0.65, 0.92)
                if region == 'London':
                    base_performance -= 0.05
                winter_pressure = -0.08 if month_num in [12, 1, 2] else 0
                trend_decline = -(month.year - 2021) * 0.02  # declining performance over time
                
                pct_within_4hrs = min(0.98, max(0.45, base_performance + winter_pressure + trend_decline + np.random.uniform(-0.05, 0.05)))
                
                breaches = int(attendances * (1 - pct_within_4hrs))
                emergency_admissions = int(attendances * np.random.uniform(0.15, 0.35))
                avg_wait_mins = max(30, int((1 - pct_within_4hrs) * 600 + np.random.randint(-30, 30)))
                
                records.append({
                    'period': month.strftime('%Y-%m'),
                    'date': month,
                    'region': region,
                    'trust_name': trust,
                    'ae_type': ae_type,
                    'total_attendances': attendances,
                    'within_4hrs': attendances - breaches,
                    'breaches_over_4hrs': breaches,
                    'pct_within_4hrs': round(pct_within_4hrs * 100, 1),
                    'emergency_admissions': emergency_admissions,
                    'avg_wait_minutes': avg_wait_mins,
                    'over_12hr_waits': max(0, int(breaches * np.random.uniform(0, 0.15))) if ae_type == 'Type 1 - Major A&E' else 0,
                })

df = pd.DataFrame(records)
print(f"\nDataset created: {len(df):,} records")
print(f"Date range: {df['period'].min()} to {df['period'].max()}")
print(f"Trusts: {df['trust_name'].nunique()}")
print(f"Regions: {df['region'].nunique()}")

# Save raw data
df.to_csv('data/nhs_ae_raw_data.csv', index=False)
print("\n✓ Raw data saved to data/nhs_ae_raw_data.csv")

# ============================================================
# 2. SQL DATABASE SETUP
# ============================================================

print("\n" + "=" * 60)
print("SETTING UP SQL DATABASE")
print("=" * 60)

conn = sqlite3.connect('data/nhs_ae_analysis.db')

df.to_sql('ae_attendances', conn, if_exists='replace', index=False)

# Create useful views
conn.execute("""
CREATE VIEW IF NOT EXISTS monthly_regional_summary AS
SELECT 
    period,
    region,
    SUM(total_attendances) as total_attendances,
    SUM(within_4hrs) as total_within_4hrs,
    SUM(breaches_over_4hrs) as total_breaches,
    ROUND(CAST(SUM(within_4hrs) AS FLOAT) / SUM(total_attendances) * 100, 1) as pct_within_4hrs,
    SUM(emergency_admissions) as total_admissions,
    ROUND(AVG(avg_wait_minutes), 0) as avg_wait_minutes,
    SUM(over_12hr_waits) as total_12hr_waits
FROM ae_attendances
GROUP BY period, region
ORDER BY period, region;
""")

conn.execute("""
CREATE VIEW IF NOT EXISTS trust_performance_ranking AS
SELECT 
    trust_name,
    region,
    COUNT(DISTINCT period) as months_reported,
    ROUND(AVG(pct_within_4hrs), 1) as avg_pct_within_4hrs,
    SUM(total_attendances) as total_attendances,
    SUM(breaches_over_4hrs) as total_breaches,
    ROUND(AVG(avg_wait_minutes), 0) as avg_wait_minutes,
    SUM(over_12hr_waits) as total_12hr_waits
FROM ae_attendances
WHERE ae_type = 'Type 1 - Major A&E'
GROUP BY trust_name, region
ORDER BY avg_pct_within_4hrs DESC;
""")

conn.commit()
print("✓ SQLite database created: data/nhs_ae_analysis.db")
print("✓ Views created: monthly_regional_summary, trust_performance_ranking")

# ============================================================
# 3. EXPLORATORY DATA ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("EXPLORATORY DATA ANALYSIS")
print("=" * 60)

type1 = df[df['ae_type'] == 'Type 1 - Major A&E'].copy()

# Key statistics
print(f"\n--- Key Findings (Type 1 Major A&E) ---")
print(f"Total attendances (2021-2024): {type1['total_attendances'].sum():,.0f}")
print(f"Total 4hr breaches: {type1['breaches_over_4hrs'].sum():,.0f}")
print(f"Overall % within 4hrs: {type1['within_4hrs'].sum() / type1['total_attendances'].sum() * 100:.1f}%")
print(f"Total 12hr+ waits: {type1['over_12hr_waits'].sum():,.0f}")

# Regional breakdown
regional = type1.groupby('region').agg(
    total_attendances=('total_attendances', 'sum'),
    avg_pct_within_4hrs=('pct_within_4hrs', 'mean'),
    avg_wait=('avg_wait_minutes', 'mean'),
    total_12hr=('over_12hr_waits', 'sum')
).round(1)
print(f"\n--- Regional Performance Summary ---")
print(regional.to_string())

# ============================================================
# 4. VISUALISATIONS
# ============================================================

print("\n" + "=" * 60)
print("CREATING VISUALISATIONS")
print("=" * 60)

sns.set_theme(style='whitegrid', palette='muted')
fig_dir = 'visualisations'

# --- Chart 1: National 4-Hour Performance Trend ---
monthly_national = type1.groupby('date').agg(
    total_att=('total_attendances', 'sum'),
    total_within=('within_4hrs', 'sum')
).reset_index()
monthly_national['pct'] = monthly_national['total_within'] / monthly_national['total_att'] * 100

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(monthly_national['date'], monthly_national['pct'], color='#1B4D7A', linewidth=2.5, marker='o', markersize=4)
ax.axhline(y=95, color='#DC2626', linestyle='--', linewidth=1.5, label='95% NHS Target')
ax.fill_between(monthly_national['date'], monthly_national['pct'], alpha=0.15, color='#1B4D7A')
ax.set_title('NHS England A&E: % Seen Within 4 Hours (Type 1 Major A&E)', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('% Within 4 Hours', fontsize=11)
ax.set_xlabel('')
ax.legend(fontsize=11)
ax.set_ylim(55, 100)
plt.tight_layout()
plt.savefig(f'{fig_dir}/01_national_4hr_trend.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Chart 1: National 4-hour performance trend")

# --- Chart 2: Regional Performance Comparison ---
regional_monthly = type1.groupby(['date', 'region']).agg(
    total_att=('total_attendances', 'sum'),
    total_within=('within_4hrs', 'sum')
).reset_index()
regional_monthly['pct'] = regional_monthly['total_within'] / regional_monthly['total_att'] * 100

fig, ax = plt.subplots(figsize=(14, 7))
for region in sorted(df['region'].unique()):
    data = regional_monthly[regional_monthly['region'] == region]
    ax.plot(data['date'], data['pct'], linewidth=1.8, label=region, alpha=0.85)
ax.axhline(y=95, color='#DC2626', linestyle='--', linewidth=1, alpha=0.6)
ax.set_title('A&E 4-Hour Performance by NHS Region', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('% Within 4 Hours')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
ax.set_ylim(50, 100)
plt.tight_layout()
plt.savefig(f'{fig_dir}/02_regional_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Chart 2: Regional comparison")

# --- Chart 3: Seasonal Heatmap ---
type1_copy = type1.copy()
type1_copy['year'] = type1_copy['date'].dt.year
type1_copy['month'] = type1_copy['date'].dt.month

seasonal = type1_copy.groupby(['year', 'month']).agg(
    pct=('pct_within_4hrs', 'mean')
).reset_index()
pivot = seasonal.pivot(index='year', columns='month', values='pct')
pivot.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

fig, ax = plt.subplots(figsize=(14, 5))
sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', vmin=60, vmax=90, linewidths=0.5, ax=ax, cbar_kws={'label': '% Within 4hrs'})
ax.set_title('Seasonal Pattern: A&E Performance by Month and Year', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('Year')
ax.set_xlabel('')
plt.tight_layout()
plt.savefig(f'{fig_dir}/03_seasonal_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Chart 3: Seasonal heatmap")

# --- Chart 4: Top & Bottom Performing Trusts ---
trust_perf = type1.groupby('trust_name').agg(
    avg_pct=('pct_within_4hrs', 'mean'),
    total_att=('total_attendances', 'sum')
).reset_index().sort_values('avg_pct')

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

bottom5 = trust_perf.head(5)
axes[0].barh(bottom5['trust_name'], bottom5['avg_pct'], color='#DC2626', alpha=0.8)
axes[0].set_title('5 Worst Performing Trusts', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Avg % Within 4hrs')
axes[0].set_xlim(55, 90)

top5 = trust_perf.tail(5)
axes[1].barh(top5['trust_name'], top5['avg_pct'], color='#059669', alpha=0.8)
axes[1].set_title('5 Best Performing Trusts', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Avg % Within 4hrs')
axes[1].set_xlim(55, 90)

plt.suptitle('Trust-Level A&E Performance Rankings (Type 1)', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{fig_dir}/04_trust_rankings.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Chart 4: Trust rankings")

# --- Chart 5: 12-Hour Waits Crisis ---
monthly_12hr = type1.groupby('date')['over_12hr_waits'].sum().reset_index()

fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(monthly_12hr['date'], monthly_12hr['over_12hr_waits'], width=25, color='#DC2626', alpha=0.75)
ax.set_title('Monthly 12-Hour+ Waits in A&E (National Total)', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('Number of 12hr+ Waits')
ax.set_xlabel('')
plt.tight_layout()
plt.savefig(f'{fig_dir}/05_12hr_waits_crisis.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Chart 5: 12-hour waits trend")

# --- Chart 6: Attendances Volume Trend ---
monthly_volume = type1.groupby('date')['total_attendances'].sum().reset_index()

fig, ax = plt.subplots(figsize=(14, 6))
ax.fill_between(monthly_volume['date'], monthly_volume['total_attendances'], alpha=0.3, color='#2563EB')
ax.plot(monthly_volume['date'], monthly_volume['total_attendances'], color='#2563EB', linewidth=2)
ax.set_title('Monthly A&E Attendances (Type 1 - All Trusts)', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('Total Attendances')
ax.set_xlabel('')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
plt.tight_layout()
plt.savefig(f'{fig_dir}/06_attendance_volume.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Chart 6: Attendance volume trend")

# ============================================================
# 5. TABLEAU-READY EXPORT
# ============================================================

tableau_export = type1.copy()
tableau_export['year'] = tableau_export['date'].dt.year
tableau_export['month_name'] = tableau_export['date'].dt.strftime('%B')
tableau_export['quarter'] = tableau_export['date'].dt.quarter
tableau_export.to_csv('data/nhs_ae_tableau_export.csv', index=False)
print("\n✓ Tableau-ready export saved to data/nhs_ae_tableau_export.csv")

# ============================================================
# 6. KEY FINDINGS SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("KEY FINDINGS SUMMARY")
print("=" * 60)

latest_year = type1[type1['date'].dt.year == 2024]
earliest_year = type1[type1['date'].dt.year == 2021]

print(f"""
1. DECLINING PERFORMANCE: National 4-hour performance declined from 
   ~{earliest_year['pct_within_4hrs'].mean():.1f}% (2021) to ~{latest_year['pct_within_4hrs'].mean():.1f}% (2024),
   well below the 95% NHS target.

2. WINTER CRISIS: Performance drops significantly in Dec-Feb each year,
   with the worst months seeing average waits of {type1[type1['date'].dt.month.isin([12,1,2])]['avg_wait_minutes'].mean():.0f} minutes.

3. REGIONAL INEQUALITY: {regional['avg_pct_within_4hrs'].idxmax()} performs best 
   ({regional['avg_pct_within_4hrs'].max():.1f}% avg), while {regional['avg_pct_within_4hrs'].idxmin()} 
   performs worst ({regional['avg_pct_within_4hrs'].min():.1f}% avg).

4. 12-HOUR WAITS: Total 12-hour waits have increased {type1[type1['date'].dt.year == 2024]['over_12hr_waits'].sum() / max(1, type1[type1['date'].dt.year == 2021]['over_12hr_waits'].sum()):.1f}x 
   from 2021 to 2024 — a patient safety concern.

5. DEMAND GROWTH: Attendances have grown year-on-year, with 2024 volumes
   {(latest_year['total_attendances'].sum() / earliest_year['total_attendances'].sum() - 1) * 100:.1f}% 
   higher than 2021.
""")

conn.close()
print("=" * 60)
print("PROJECT 1 COMPLETE")
print("=" * 60)
