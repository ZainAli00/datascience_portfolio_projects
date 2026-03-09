#!/usr/bin/env python3
"""
Premier League Performance Tracker
=====================================
Analyse Premier League match and player stats — team performance, xG analysis,
home/away splits, and form trends across the 2023/24 season.

Tools: Python (Pandas, Matplotlib), SQL, Tableau-ready export
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
print("PROJECT 4: Premier League Performance Tracker")
print("=" * 60)

# ============================================================
# 1. GENERATE REALISTIC PL DATA (2023/24 SEASON)
# ============================================================

teams = {
    'Manchester City': {'strength': 92, 'xg_factor': 1.15},
    'Arsenal': {'strength': 89, 'xg_factor': 1.10},
    'Liverpool': {'strength': 87, 'xg_factor': 1.08},
    'Aston Villa': {'strength': 80, 'xg_factor': 1.02},
    'Tottenham': {'strength': 79, 'xg_factor': 1.05},
    'Chelsea': {'strength': 76, 'xg_factor': 0.98},
    'Newcastle': {'strength': 78, 'xg_factor': 1.00},
    'Manchester United': {'strength': 75, 'xg_factor': 0.95},
    'West Ham': {'strength': 73, 'xg_factor': 0.92},
    'Crystal Palace': {'strength': 70, 'xg_factor': 0.88},
    'Brighton': {'strength': 72, 'xg_factor': 0.95},
    'Bournemouth': {'strength': 68, 'xg_factor': 0.85},
    'Fulham': {'strength': 69, 'xg_factor': 0.87},
    'Wolves': {'strength': 67, 'xg_factor': 0.84},
    'Everton': {'strength': 65, 'xg_factor': 0.80},
    'Brentford': {'strength': 70, 'xg_factor': 0.90},
    'Nottingham Forest': {'strength': 64, 'xg_factor': 0.78},
    'Luton Town': {'strength': 58, 'xg_factor': 0.72},
    'Burnley': {'strength': 56, 'xg_factor': 0.70},
    'Sheffield United': {'strength': 54, 'xg_factor': 0.68},
}

# Generate all 380 matches
team_names = list(teams.keys())
matches = []
match_id = 1
match_weeks = []
start_date = pd.Timestamp('2023-08-12')

for gw in range(1, 39):
    # Simple round-robin pairing
    shuffled = team_names.copy()
    np.random.shuffle(shuffled)
    for i in range(0, 20, 2):
        home = shuffled[i]
        away = shuffled[i + 1]
        
        home_str = teams[home]['strength'] + np.random.normal(5, 3)  # home advantage
        away_str = teams[away]['strength']
        
        # xG generation
        home_xg = max(0.2, np.random.normal(1.5 * teams[home]['xg_factor'] * (home_str / 80), 0.6))
        away_xg = max(0.1, np.random.normal(1.2 * teams[away]['xg_factor'] * (away_str / 80), 0.5))
        
        # Goals (slightly random vs xG)
        home_goals = max(0, int(np.random.poisson(home_xg)))
        away_goals = max(0, int(np.random.poisson(away_xg)))
        
        home_shots = max(home_goals, int(np.random.poisson(12 * teams[home]['xg_factor'])))
        away_shots = max(away_goals, int(np.random.poisson(10 * teams[away]['xg_factor'])))
        home_sot = min(home_shots, max(home_goals, int(home_shots * np.random.uniform(0.3, 0.5))))
        away_sot = min(away_shots, max(away_goals, int(away_shots * np.random.uniform(0.25, 0.45))))
        
        home_poss = np.clip(50 + (home_str - away_str) * 0.3 + np.random.normal(0, 5), 30, 75)
        away_poss = 100 - home_poss
        
        match_date = start_date + pd.Timedelta(weeks=gw-1) + pd.Timedelta(days=np.random.choice([0, 1, 2]))
        
        matches.append({
            'match_id': match_id,
            'gameweek': gw,
            'date': match_date,
            'home_team': home,
            'away_team': away,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'home_xg': round(home_xg, 2),
            'away_xg': round(away_xg, 2),
            'home_shots': home_shots,
            'away_shots': away_shots,
            'home_shots_on_target': home_sot,
            'away_shots_on_target': away_sot,
            'home_possession': round(home_poss, 1),
            'away_possession': round(away_poss, 1),
            'home_corners': np.random.randint(2, 12),
            'away_corners': np.random.randint(1, 10),
            'home_fouls': np.random.randint(6, 18),
            'away_fouls': np.random.randint(7, 20),
            'attendance': np.random.randint(20000, 62000),
            'referee': np.random.choice(['Michael Oliver', 'Anthony Taylor', 'Simon Hooper', 'Chris Kavanagh', 'Paul Tierney', 'Craig Pawson']),
        })
        match_id += 1

matches_df = pd.DataFrame(matches)
matches_df['result'] = matches_df.apply(lambda r: 'H' if r['home_goals'] > r['away_goals'] else ('A' if r['away_goals'] > r['home_goals'] else 'D'), axis=1)

matches_df.to_csv('data/pl_matches_2324.csv', index=False)
print(f"\nMatches generated: {len(matches_df)}")
print(f"Total goals: {matches_df['home_goals'].sum() + matches_df['away_goals'].sum()}")

# ============================================================
# 2. BUILD LEAGUE TABLE
# ============================================================

table_rows = []
for team in team_names:
    home = matches_df[matches_df['home_team'] == team]
    away = matches_df[matches_df['away_team'] == team]
    
    hw = (home['home_goals'] > home['away_goals']).sum()
    hd = (home['home_goals'] == home['away_goals']).sum()
    hl = (home['home_goals'] < home['away_goals']).sum()
    aw = (away['away_goals'] > away['home_goals']).sum()
    ad = (away['away_goals'] == away['home_goals']).sum()
    al = (away['away_goals'] < away['home_goals']).sum()
    
    gf = home['home_goals'].sum() + away['away_goals'].sum()
    ga = home['away_goals'].sum() + away['home_goals'].sum()
    xgf = home['home_xg'].sum() + away['away_xg'].sum()
    xga = home['away_xg'].sum() + away['home_xg'].sum()
    
    pts = (hw + aw) * 3 + (hd + ad)
    played = len(home) + len(away)
    
    table_rows.append({
        'team': team, 'played': played, 'won': hw + aw, 'drawn': hd + ad, 'lost': hl + al,
        'goals_for': int(gf), 'goals_against': int(ga), 'goal_difference': int(gf - ga),
        'xg_for': round(xgf, 1), 'xg_against': round(xga, 1), 'xg_difference': round(xgf - xga, 1),
        'points': pts,
        'home_wins': hw, 'home_draws': hd, 'home_losses': hl,
        'away_wins': aw, 'away_draws': ad, 'away_losses': al,
    })

table_df = pd.DataFrame(table_rows).sort_values('points', ascending=False).reset_index(drop=True)
table_df.index += 1
table_df.index.name = 'position'
table_df.to_csv('data/pl_table_2324.csv')
print("\n--- Final League Table ---")
print(table_df[['team', 'played', 'won', 'drawn', 'lost', 'goals_for', 'goals_against', 'goal_difference', 'points']].head(10).to_string())

# ============================================================
# 3. SQL DATABASE
# ============================================================

conn = sqlite3.connect('data/premier_league.db')
matches_df.to_sql('matches', conn, if_exists='replace', index=False)
table_df.to_sql('league_table', conn, if_exists='replace', index=True)
conn.commit()
print("\n✓ SQLite database created")

# ============================================================
# 4. VISUALISATIONS
# ============================================================

fig_dir = 'visualisations'
sns.set_theme(style='whitegrid')

# --- Chart 1: League Table ---
fig, ax = plt.subplots(figsize=(12, 10))
colors = ['#FFD700' if i < 4 else '#C0C0C0' if i < 6 else '#CD7F32' if i < 7 else '#DC2626' if i >= 17 else '#3B82F6' for i in range(len(table_df))]
ax.barh(table_df['team'][::-1], table_df['points'][::-1], color=colors[::-1])
ax.set_title('Premier League 2023/24 Final Standings', fontsize=14, fontweight='bold')
ax.set_xlabel('Points')
for i, (pts, team) in enumerate(zip(table_df['points'][::-1], table_df['team'][::-1])):
    ax.text(pts + 0.5, i, str(pts), va='center', fontsize=9, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{fig_dir}/01_league_table.png', dpi=150)
plt.close()
print("✓ Chart 1: League table")

# --- Chart 2: xG vs Actual Goals ---
fig, ax = plt.subplots(figsize=(10, 10))
ax.scatter(table_df['xg_for'], table_df['goals_for'], s=100, c='#3B82F6', alpha=0.7, edgecolors='white', linewidth=1.5)
for _, row in table_df.iterrows():
    ax.annotate(row['team'], (row['xg_for'], row['goals_for']), fontsize=8, ha='center', va='bottom', textcoords='offset points', xytext=(0, 8))
max_val = max(table_df['xg_for'].max(), table_df['goals_for'].max()) + 5
ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label='xG = Goals')
ax.set_xlabel('Expected Goals (xG)')
ax.set_ylabel('Actual Goals')
ax.set_title('xG vs Actual Goals Scored', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/02_xg_vs_actual.png', dpi=150)
plt.close()
print("✓ Chart 2: xG vs actual goals")

# --- Chart 3: Home vs Away Performance ---
fig, ax = plt.subplots(figsize=(14, 8))
x = np.arange(len(table_df))
width = 0.35
ax.bar(x - width/2, table_df['home_wins'] * 3 + table_df['home_draws'], width, label='Home Points', color='#3B82F6')
ax.bar(x + width/2, table_df['away_wins'] * 3 + table_df['away_draws'], width, label='Away Points', color='#F97316')
ax.set_xticks(x)
ax.set_xticklabels(table_df['team'], rotation=90, fontsize=8)
ax.set_title('Home vs Away Points', fontsize=14, fontweight='bold')
ax.set_ylabel('Points')
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/03_home_away.png', dpi=150)
plt.close()
print("✓ Chart 3: Home vs away")

# --- Chart 4: Goals Per Gameweek Trend ---
gw_goals = matches_df.groupby('gameweek').agg(
    total_goals=('home_goals', lambda x: x.sum() + matches_df.loc[x.index, 'away_goals'].sum()),
).reset_index()
# Recalculate properly
gw_goals = matches_df.groupby('gameweek').apply(lambda x: x['home_goals'].sum() + x['away_goals'].sum()).reset_index()
gw_goals.columns = ['gameweek', 'total_goals']

fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(gw_goals['gameweek'], gw_goals['total_goals'], color='#8B5CF6', alpha=0.7)
ax.axhline(y=gw_goals['total_goals'].mean(), color='#DC2626', linestyle='--', label=f"Avg: {gw_goals['total_goals'].mean():.1f} goals/GW")
ax.set_title('Total Goals per Gameweek', fontsize=14, fontweight='bold')
ax.set_xlabel('Gameweek')
ax.set_ylabel('Goals')
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/04_goals_per_gw.png', dpi=150)
plt.close()
print("✓ Chart 4: Goals per gameweek")

# --- Chart 5: xG Overperformance ---
table_df['xg_diff_actual'] = table_df['goals_for'] - table_df['xg_for']
xg_over = table_df.sort_values('xg_diff_actual')

fig, ax = plt.subplots(figsize=(12, 10))
colors = ['#059669' if x > 0 else '#DC2626' for x in xg_over['xg_diff_actual']]
ax.barh(xg_over['team'], xg_over['xg_diff_actual'], color=colors)
ax.axvline(x=0, color='black', linewidth=0.8)
ax.set_title('Goals vs xG: Over/Under Performance', fontsize=14, fontweight='bold')
ax.set_xlabel('Goals - xG (positive = overperforming)')
plt.tight_layout()
plt.savefig(f'{fig_dir}/05_xg_overperformance.png', dpi=150)
plt.close()
print("✓ Chart 5: xG overperformance")

# Tableau export
matches_df.to_csv('data/pl_tableau_export.csv', index=False)
conn.close()

print("\n" + "=" * 60)
print("PROJECT 4 COMPLETE")
print("=" * 60)
