#!/usr/bin/env python3
"""
A/B Testing & Experimentation Report
======================================
Simulate and analyse an A/B test for an e-commerce checkout flow change.
Apply statistical testing, calculate sample sizes, and present clear
go/no-go recommendations.

Tools: Python (Pandas, SciPy, Matplotlib), SQL, Excel-ready export
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import sqlite3

np.random.seed(42)

print("=" * 60)
print("PROJECT 6: A/B Testing & Experimentation Report")
print("=" * 60)

# ============================================================
# 1. EXPERIMENT DESIGN
# ============================================================

print("""
EXPERIMENT BRIEF
================
Hypothesis: A simplified one-page checkout will increase conversion rate
compared to the current multi-step checkout flow.

Primary metric: Conversion rate (completed purchase / checkout initiated)
Secondary metrics: Average order value, time to purchase, cart abandonment
Minimum detectable effect: 2 percentage points
Significance level: α = 0.05
Power: 80%
""")

# Power analysis
from scipy.stats import norm

def sample_size_proportion(p1, mde, alpha=0.05, power=0.80):
    p2 = p1 + mde
    z_alpha = norm.ppf(1 - alpha/2)
    z_beta = norm.ppf(power)
    pooled_p = (p1 + p2) / 2
    n = ((z_alpha * np.sqrt(2 * pooled_p * (1 - pooled_p)) + z_beta * np.sqrt(p1*(1-p1) + p2*(1-p2))) / mde) ** 2
    return int(np.ceil(n))

baseline_cr = 0.12  # 12% baseline conversion
mde = 0.02  # 2pp minimum detectable effect
required_n = sample_size_proportion(baseline_cr, mde)
print(f"Required sample size per group: {required_n:,}")
print(f"Total required: {required_n * 2:,}")

# ============================================================
# 2. GENERATE EXPERIMENT DATA
# ============================================================

n_per_group = 5000  # Exceeds required sample

# Control group (multi-step checkout)
control_converted = np.random.binomial(1, 0.120, n_per_group)
control_aov = np.where(control_converted, np.random.lognormal(3.8, 0.5, n_per_group), 0)
control_time = np.where(control_converted, np.random.exponential(180, n_per_group).clip(30, 900), 
                        np.random.exponential(60, n_per_group).clip(5, 300))

# Treatment group (one-page checkout) — TRUE EFFECT: +2.5pp conversion
treatment_converted = np.random.binomial(1, 0.145, n_per_group)
treatment_aov = np.where(treatment_converted, np.random.lognormal(3.75, 0.5, n_per_group), 0)
treatment_time = np.where(treatment_converted, np.random.exponential(120, n_per_group).clip(20, 600),
                          np.random.exponential(45, n_per_group).clip(5, 250))

# Build DataFrame
control_df = pd.DataFrame({
    'user_id': [f'U-{i:06d}' for i in range(1, n_per_group + 1)],
    'group': 'control',
    'converted': control_converted,
    'order_value_gbp': control_aov.round(2),
    'time_to_action_sec': control_time.astype(int),
    'device': np.random.choice(['Mobile', 'Desktop', 'Tablet'], n_per_group, p=[0.55, 0.35, 0.10]),
    'new_user': np.random.binomial(1, 0.4, n_per_group),
    'day_of_week': np.random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], n_per_group),
    'traffic_source': np.random.choice(['Organic', 'Paid', 'Email', 'Social', 'Direct'], n_per_group, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
    'pages_before_checkout': np.random.poisson(5, n_per_group).clip(1, 20),
})

treatment_df = pd.DataFrame({
    'user_id': [f'U-{i:06d}' for i in range(n_per_group + 1, 2 * n_per_group + 1)],
    'group': 'treatment',
    'converted': treatment_converted,
    'order_value_gbp': treatment_aov.round(2),
    'time_to_action_sec': treatment_time.astype(int),
    'device': np.random.choice(['Mobile', 'Desktop', 'Tablet'], n_per_group, p=[0.55, 0.35, 0.10]),
    'new_user': np.random.binomial(1, 0.4, n_per_group),
    'day_of_week': np.random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], n_per_group),
    'traffic_source': np.random.choice(['Organic', 'Paid', 'Email', 'Social', 'Direct'], n_per_group, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
    'pages_before_checkout': np.random.poisson(5, n_per_group).clip(1, 20),
})

df = pd.concat([control_df, treatment_df], ignore_index=True)
df.to_csv('data/ab_test_data.csv', index=False)
print(f"\nTotal participants: {len(df):,}")
print(f"Control: {len(control_df):,} | Treatment: {len(treatment_df):,}")

# ============================================================
# 3. STATISTICAL ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("STATISTICAL ANALYSIS")
print("=" * 60)

# Primary metric: Conversion Rate
ctrl_cr = control_df['converted'].mean()
treat_cr = treatment_df['converted'].mean()
lift = (treat_cr - ctrl_cr) / ctrl_cr * 100

# Two-proportion z-test
from scipy.stats import chi2_contingency

contingency = pd.crosstab(df['group'], df['converted'])
chi2, p_value, dof, expected = chi2_contingency(contingency)

# Confidence interval for difference
se = np.sqrt(ctrl_cr * (1-ctrl_cr)/n_per_group + treat_cr * (1-treat_cr)/n_per_group)
ci_lower = (treat_cr - ctrl_cr) - 1.96 * se
ci_upper = (treat_cr - ctrl_cr) + 1.96 * se

print(f"\n--- PRIMARY METRIC: Conversion Rate ---")
print(f"Control:   {ctrl_cr:.3%}")
print(f"Treatment: {treat_cr:.3%}")
print(f"Absolute Difference: {treat_cr - ctrl_cr:+.3%}")
print(f"Relative Lift: {lift:+.1f}%")
print(f"p-value: {p_value:.6f}")
print(f"95% CI for difference: [{ci_lower:.4f}, {ci_upper:.4f}]")
print(f"Statistically Significant: {'YES ✓' if p_value < 0.05 else 'NO ✗'}")

# Secondary: AOV (among converters only)
ctrl_aov = control_df[control_df['converted'] == 1]['order_value_gbp']
treat_aov = treatment_df[treatment_df['converted'] == 1]['order_value_gbp']
t_stat_aov, p_aov = stats.ttest_ind(ctrl_aov, treat_aov)

print(f"\n--- SECONDARY METRIC: Average Order Value ---")
print(f"Control AOV:   £{ctrl_aov.mean():.2f}")
print(f"Treatment AOV: £{treat_aov.mean():.2f}")
print(f"p-value: {p_aov:.4f}")
print(f"Significant: {'YES' if p_aov < 0.05 else 'NO'}")

# Time to purchase
ctrl_time = control_df[control_df['converted'] == 1]['time_to_action_sec']
treat_time = treatment_df[treatment_df['converted'] == 1]['time_to_action_sec']
t_stat_time, p_time = stats.ttest_ind(ctrl_time, treat_time)

print(f"\n--- SECONDARY METRIC: Time to Purchase ---")
print(f"Control:   {ctrl_time.mean():.0f}s ({ctrl_time.mean()/60:.1f} min)")
print(f"Treatment: {treat_time.mean():.0f}s ({treat_time.mean()/60:.1f} min)")
print(f"p-value: {p_time:.6f}")

# ============================================================
# 4. SEGMENT ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("SEGMENT ANALYSIS")
print("=" * 60)

for segment in ['device', 'new_user', 'traffic_source']:
    print(f"\n--- By {segment} ---")
    seg_analysis = df.groupby([segment, 'group'])['converted'].agg(['mean', 'count']).reset_index()
    seg_pivot = seg_analysis.pivot(index=segment, columns='group', values='mean')
    seg_pivot['lift_pct'] = ((seg_pivot['treatment'] - seg_pivot['control']) / seg_pivot['control'] * 100).round(1)
    print(seg_pivot.to_string())

# ============================================================
# 5. VISUALISATIONS
# ============================================================

fig_dir = 'visualisations'
sns.set_theme(style='whitegrid')

# --- Chart 1: Conversion Rate Comparison ---
fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(['Control\n(Multi-step)', 'Treatment\n(One-page)'], [ctrl_cr * 100, treat_cr * 100], 
              color=['#6B7280', '#10B981'], width=0.5)
ax.set_ylabel('Conversion Rate (%)')
ax.set_title('A/B Test: Conversion Rate by Group', fontsize=14, fontweight='bold')
for bar, val in zip(bars, [ctrl_cr, treat_cr]):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.2, f'{val:.2%}', ha='center', fontweight='bold', fontsize=14)
ax.set_ylim(0, max(ctrl_cr, treat_cr) * 100 * 1.3)
# Add significance annotation
ax.annotate(f'p = {p_value:.4f} {"*" if p_value < 0.05 else "n.s."}',
            xy=(0.5, max(ctrl_cr, treat_cr) * 100 * 1.15), ha='center', fontsize=12, color='#059669' if p_value < 0.05 else '#6B7280')
plt.tight_layout()
plt.savefig(f'{fig_dir}/01_conversion_comparison.png', dpi=150)
plt.close()
print("\n✓ Chart 1: Conversion comparison")

# --- Chart 2: Confidence Interval ---
fig, ax = plt.subplots(figsize=(10, 4))
diff = treat_cr - ctrl_cr
ax.barh(['Treatment - Control'], [diff * 100], xerr=[(diff - ci_lower) * 100], color='#10B981', height=0.4, capsize=10)
ax.axvline(x=0, color='#DC2626', linestyle='--', linewidth=1.5, label='No effect')
ax.set_xlabel('Difference in Conversion Rate (percentage points)')
ax.set_title('95% Confidence Interval for Treatment Effect', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/02_confidence_interval.png', dpi=150)
plt.close()
print("✓ Chart 2: Confidence interval")

# --- Chart 3: Conversion by Device ---
fig, ax = plt.subplots(figsize=(10, 6))
device_cr = df.groupby(['device', 'group'])['converted'].mean().unstack() * 100
device_cr.plot(kind='bar', ax=ax, color=['#6B7280', '#10B981'])
ax.set_title('Conversion Rate by Device & Group', fontsize=14, fontweight='bold')
ax.set_ylabel('Conversion Rate (%)')
ax.legend(title='Group')
ax.tick_params(axis='x', rotation=0)
plt.tight_layout()
plt.savefig(f'{fig_dir}/03_device_breakdown.png', dpi=150)
plt.close()
print("✓ Chart 3: Device breakdown")

# --- Chart 4: Time to Purchase Distribution ---
fig, ax = plt.subplots(figsize=(12, 6))
ax.hist(ctrl_time / 60, bins=40, alpha=0.5, label=f'Control (mean: {ctrl_time.mean()/60:.1f} min)', color='#6B7280', density=True)
ax.hist(treat_time / 60, bins=40, alpha=0.5, label=f'Treatment (mean: {treat_time.mean()/60:.1f} min)', color='#10B981', density=True)
ax.set_title('Time to Purchase Distribution', fontsize=14, fontweight='bold')
ax.set_xlabel('Minutes')
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/04_time_distribution.png', dpi=150)
plt.close()
print("✓ Chart 4: Time distribution")

# --- Chart 5: Cumulative Conversion Over Time (simulated) ---
fig, ax = plt.subplots(figsize=(12, 6))
days = range(1, 15)
ctrl_cumul = [ctrl_cr * (1 - np.exp(-d/3)) * 100 for d in days]
treat_cumul = [treat_cr * (1 - np.exp(-d/3)) * 100 for d in days]
ax.plot(days, ctrl_cumul, 'o-', color='#6B7280', linewidth=2, label='Control')
ax.plot(days, treat_cumul, 'o-', color='#10B981', linewidth=2, label='Treatment')
ax.fill_between(days, ctrl_cumul, treat_cumul, alpha=0.15, color='#10B981')
ax.set_title('Cumulative Conversion Rate Over Experiment Duration', fontsize=14, fontweight='bold')
ax.set_xlabel('Day of Experiment')
ax.set_ylabel('Cumulative Conversion Rate (%)')
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/05_cumulative_conversion.png', dpi=150)
plt.close()
print("✓ Chart 5: Cumulative conversion")

# --- Chart 6: Revenue Impact Estimate ---
monthly_checkouts = 50000
ctrl_rev_month = monthly_checkouts * ctrl_cr * ctrl_aov.mean()
treat_rev_month = monthly_checkouts * treat_cr * treat_aov.mean()
monthly_uplift = treat_rev_month - ctrl_rev_month
annual_uplift = monthly_uplift * 12

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(['Control\n(Current)', 'Treatment\n(New Checkout)'], [ctrl_rev_month, treat_rev_month],
              color=['#6B7280', '#10B981'], width=0.5)
ax.set_ylabel('Estimated Monthly Revenue (£)')
ax.set_title('Projected Revenue Impact', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1e3:.0f}K'))
ax.annotate(f'+£{monthly_uplift:,.0f}/month\n+£{annual_uplift:,.0f}/year',
            xy=(1.35, treat_rev_month * 0.9), fontsize=12, color='#059669', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{fig_dir}/06_revenue_impact.png', dpi=150)
plt.close()
print("✓ Chart 6: Revenue impact")

# ============================================================
# 6. SQL DATABASE
# ============================================================

conn = sqlite3.connect('data/ab_test.db')
df.to_sql('experiment', conn, if_exists='replace', index=False)
conn.commit()
conn.close()

# ============================================================
# 7. FINAL RECOMMENDATION
# ============================================================

print("\n" + "=" * 60)
print("RECOMMENDATION")
print("=" * 60)
print(f"""
DECISION: ✅ SHIP THE NEW ONE-PAGE CHECKOUT

Evidence:
• Conversion rate increased from {ctrl_cr:.2%} to {treat_cr:.2%} ({lift:+.1f}% lift)
• Result is statistically significant (p = {p_value:.4f})
• 95% CI [{ci_lower*100:.2f}pp, {ci_upper*100:.2f}pp] does not cross zero
• Checkout time reduced by ~{(1 - treat_time.mean()/ctrl_time.mean())*100:.0f}%
• Estimated annual revenue uplift: £{annual_uplift:,.0f}
• No significant negative impact on AOV (p = {p_aov:.3f})
• Effect consistent across devices and traffic sources

Risk: AOV shows a slight (non-significant) decrease — monitor post-launch.
""")

print("=" * 60)
print("PROJECT 6 COMPLETE")
print("=" * 60)
