#!/usr/bin/env python3
"""
UK Fintech Customer Churn Predictor
=====================================
Build a customer churn analysis for a simulated UK fintech company.
Explore which factors drive customers to leave, segment users by risk,
and present actionable retention strategies.

Tools: Python (Pandas, Scikit-learn, Matplotlib), SQL, Excel export
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

print("=" * 60)
print("PROJECT 2: UK Fintech Customer Churn Predictor")
print("=" * 60)

# ============================================================
# 1. GENERATE UK FINTECH CUSTOMER DATA
# ============================================================

n_customers = 8000

ages = np.random.normal(35, 12, n_customers).clip(18, 75).astype(int)
genders = np.random.choice(['Male', 'Female', 'Non-binary'], n_customers, p=[0.48, 0.48, 0.04])
regions = np.random.choice(
    ['London', 'South East', 'North West', 'Midlands', 'Scotland', 'Yorkshire', 'South West', 'Wales', 'East of England', 'Northern Ireland'],
    n_customers, p=[0.22, 0.14, 0.12, 0.11, 0.09, 0.08, 0.08, 0.05, 0.06, 0.05]
)

products = np.random.choice(['Current Account', 'Savings', 'Investment ISA', 'Crypto Wallet', 'Business Account'], n_customers, p=[0.35, 0.25, 0.15, 0.15, 0.10])
tenure_months = np.random.exponential(24, n_customers).clip(1, 120).astype(int)
monthly_transactions = np.random.poisson(15, n_customers).clip(0, 100)
avg_balance = np.random.lognormal(7.5, 1.2, n_customers).clip(0, 500000).round(2)
num_products = np.random.choice([1, 2, 3, 4], n_customers, p=[0.4, 0.3, 0.2, 0.1])
has_credit_card = np.random.binomial(1, 0.45, n_customers)
num_support_tickets = np.random.poisson(2, n_customers).clip(0, 20)
app_logins_month = np.random.poisson(12, n_customers).clip(0, 60)
referral_source = np.random.choice(['Organic', 'Paid Ads', 'Referral', 'Social Media'], n_customers, p=[0.3, 0.25, 0.25, 0.2])
satisfaction_score = np.random.choice([1, 2, 3, 4, 5], n_customers, p=[0.05, 0.1, 0.25, 0.35, 0.25])

# Churn logic - realistic factors
churn_prob = (
    0.15
    - tenure_months * 0.002
    - num_products * 0.05
    + num_support_tickets * 0.025
    - app_logins_month * 0.005
    - (satisfaction_score - 3) * 0.08
    + (avg_balance < 500) * 0.1
    - has_credit_card * 0.05
    + (monthly_transactions < 5) * 0.12
    + np.random.normal(0, 0.05, n_customers)
)
churn_prob = np.clip(churn_prob, 0.02, 0.85)
churned = np.random.binomial(1, churn_prob)

df = pd.DataFrame({
    'customer_id': [f'CUST-{i:05d}' for i in range(1, n_customers + 1)],
    'age': ages,
    'gender': genders,
    'region': regions,
    'primary_product': products,
    'tenure_months': tenure_months,
    'monthly_transactions': monthly_transactions,
    'avg_balance_gbp': avg_balance,
    'num_products': num_products,
    'has_credit_card': has_credit_card,
    'num_support_tickets': num_support_tickets,
    'app_logins_per_month': app_logins_month,
    'referral_source': referral_source,
    'satisfaction_score': satisfaction_score,
    'churned': churned
})

print(f"\nDataset: {len(df):,} customers")
print(f"Churn rate: {df['churned'].mean():.1%}")
print(f"Features: {len(df.columns) - 2}")

df.to_csv('data/fintech_customers.csv', index=False)
print("✓ Data saved to data/fintech_customers.csv")

# ============================================================
# 2. SQL DATABASE
# ============================================================

conn = sqlite3.connect('data/fintech_churn.db')
df.to_sql('customers', conn, if_exists='replace', index=False)

conn.execute("""
CREATE VIEW IF NOT EXISTS churn_by_segment AS
SELECT 
    primary_product,
    region,
    COUNT(*) as total_customers,
    SUM(churned) as churned_count,
    ROUND(CAST(SUM(churned) AS FLOAT) / COUNT(*) * 100, 1) as churn_rate,
    ROUND(AVG(tenure_months), 1) as avg_tenure,
    ROUND(AVG(avg_balance_gbp), 0) as avg_balance,
    ROUND(AVG(satisfaction_score), 2) as avg_satisfaction
FROM customers
GROUP BY primary_product, region
ORDER BY churn_rate DESC;
""")
conn.commit()
print("✓ SQLite database created: data/fintech_churn.db")

# ============================================================
# 3. EXPLORATORY DATA ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("EXPLORATORY DATA ANALYSIS")
print("=" * 60)

fig_dir = 'visualisations'
sns.set_theme(style='whitegrid')

# --- Chart 1: Churn Rate by Product ---
fig, ax = plt.subplots(figsize=(10, 6))
churn_by_product = df.groupby('primary_product')['churned'].mean().sort_values(ascending=True) * 100
churn_by_product.plot(kind='barh', ax=ax, color=['#059669' if x < 25 else '#DC2626' for x in churn_by_product.values])
ax.set_title('Churn Rate by Product Type', fontsize=14, fontweight='bold')
ax.set_xlabel('Churn Rate (%)')
ax.axvline(x=df['churned'].mean() * 100, color='#333', linestyle='--', label=f"Overall: {df['churned'].mean():.1%}")
ax.legend()
plt.tight_layout()
plt.savefig(f'{fig_dir}/01_churn_by_product.png', dpi=150)
plt.close()
print("✓ Chart 1: Churn by product")

# --- Chart 2: Feature Correlations ---
numeric_cols = ['age', 'tenure_months', 'monthly_transactions', 'avg_balance_gbp', 'num_products', 'has_credit_card', 'num_support_tickets', 'app_logins_per_month', 'satisfaction_score', 'churned']
fig, ax = plt.subplots(figsize=(12, 9))
corr = df[numeric_cols].corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax, vmin=-0.5, vmax=0.5)
ax.set_title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{fig_dir}/02_correlation_matrix.png', dpi=150)
plt.close()
print("✓ Chart 2: Correlation matrix")

# --- Chart 3: Churn by Tenure Cohort ---
df['tenure_cohort'] = pd.cut(df['tenure_months'], bins=[0, 6, 12, 24, 48, 120], labels=['0-6m', '6-12m', '1-2yr', '2-4yr', '4yr+'])
fig, ax = plt.subplots(figsize=(10, 6))
churn_tenure = df.groupby('tenure_cohort', observed=True)['churned'].agg(['mean', 'count'])
bars = ax.bar(churn_tenure.index, churn_tenure['mean'] * 100, color='#3B82F6', alpha=0.8)
ax.set_title('Churn Rate by Customer Tenure', fontsize=14, fontweight='bold')
ax.set_ylabel('Churn Rate (%)')
ax.set_xlabel('Tenure Cohort')
for bar, count in zip(bars, churn_tenure['count']):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5, f'n={count:,}', ha='center', va='bottom', fontsize=9, color='#666')
plt.tight_layout()
plt.savefig(f'{fig_dir}/03_churn_by_tenure.png', dpi=150)
plt.close()
print("✓ Chart 3: Churn by tenure")

# --- Chart 4: Satisfaction vs Churn ---
fig, ax = plt.subplots(figsize=(10, 6))
sat_churn = df.groupby('satisfaction_score')['churned'].mean() * 100
ax.bar(sat_churn.index, sat_churn.values, color=['#DC2626', '#F97316', '#EAB308', '#22C55E', '#059669'])
ax.set_title('Churn Rate by Customer Satisfaction Score', fontsize=14, fontweight='bold')
ax.set_ylabel('Churn Rate (%)')
ax.set_xlabel('Satisfaction Score (1=Very Poor, 5=Excellent)')
plt.tight_layout()
plt.savefig(f'{fig_dir}/04_satisfaction_vs_churn.png', dpi=150)
plt.close()
print("✓ Chart 4: Satisfaction vs churn")

# --- Chart 5: Regional Churn Map ---
fig, ax = plt.subplots(figsize=(12, 6))
regional_churn = df.groupby('region')['churned'].agg(['mean', 'count']).sort_values('mean', ascending=True)
regional_churn['mean'] *= 100
colors = ['#059669' if x < 25 else '#EAB308' if x < 30 else '#DC2626' for x in regional_churn['mean']]
ax.barh(regional_churn.index, regional_churn['mean'], color=colors)
ax.set_title('Churn Rate by UK Region', fontsize=14, fontweight='bold')
ax.set_xlabel('Churn Rate (%)')
plt.tight_layout()
plt.savefig(f'{fig_dir}/05_regional_churn.png', dpi=150)
plt.close()
print("✓ Chart 5: Regional churn")

# ============================================================
# 4. PREDICTIVE MODELLING
# ============================================================

print("\n" + "=" * 60)
print("PREDICTIVE MODELLING")
print("=" * 60)

feature_cols = ['age', 'tenure_months', 'monthly_transactions', 'avg_balance_gbp', 'num_products', 'has_credit_card', 'num_support_tickets', 'app_logins_per_month', 'satisfaction_score']

le_product = LabelEncoder()
le_region = LabelEncoder()
le_source = LabelEncoder()
df['product_encoded'] = le_product.fit_transform(df['primary_product'])
df['region_encoded'] = le_region.fit_transform(df['region'])
df['source_encoded'] = le_source.fit_transform(df['referral_source'])
feature_cols += ['product_encoded', 'region_encoded', 'source_encoded']

X = df[feature_cols]
y = df['churned']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Logistic Regression
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train_scaled, y_train)
lr_pred = lr.predict(X_test_scaled)
lr_proba = lr.predict_proba(X_test_scaled)[:, 1]
lr_auc = roc_auc_score(y_test, lr_proba)

# Random Forest
rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_proba = rf.predict_proba(X_test)[:, 1]
rf_auc = roc_auc_score(y_test, rf_proba)

print(f"\nLogistic Regression AUC: {lr_auc:.3f}")
print(f"Random Forest AUC:      {rf_auc:.3f}")
print(f"\n--- Random Forest Classification Report ---")
print(classification_report(y_test, rf_pred, target_names=['Retained', 'Churned']))

# --- Chart 6: ROC Curve ---
fig, ax = plt.subplots(figsize=(8, 8))
for name, proba, auc_val in [('Logistic Regression', lr_proba, lr_auc), ('Random Forest', rf_proba, rf_auc)]:
    fpr, tpr, _ = roc_curve(y_test, proba)
    ax.plot(fpr, tpr, linewidth=2.5, label=f'{name} (AUC = {auc_val:.3f})')
ax.plot([0, 1], [0, 1], 'k--', linewidth=1)
ax.set_title('ROC Curve: Churn Prediction Models', fontsize=14, fontweight='bold')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig(f'{fig_dir}/06_roc_curve.png', dpi=150)
plt.close()
print("✓ Chart 6: ROC curve")

# --- Chart 7: Feature Importance ---
importances = pd.Series(rf.feature_importances_, index=feature_cols).sort_values()
fig, ax = plt.subplots(figsize=(10, 7))
importances.plot(kind='barh', ax=ax, color='#3B82F6')
ax.set_title('Feature Importance (Random Forest)', fontsize=14, fontweight='bold')
ax.set_xlabel('Importance')
plt.tight_layout()
plt.savefig(f'{fig_dir}/07_feature_importance.png', dpi=150)
plt.close()
print("✓ Chart 7: Feature importance")

# --- Chart 8: Confusion Matrix ---
fig, ax = plt.subplots(figsize=(7, 6))
cm = confusion_matrix(y_test, rf_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Retained', 'Churned'], yticklabels=['Retained', 'Churned'], ax=ax)
ax.set_title('Confusion Matrix (Random Forest)', fontsize=14, fontweight='bold')
ax.set_ylabel('Actual')
ax.set_xlabel('Predicted')
plt.tight_layout()
plt.savefig(f'{fig_dir}/08_confusion_matrix.png', dpi=150)
plt.close()
print("✓ Chart 8: Confusion matrix")

# ============================================================
# 5. CUSTOMER RISK SEGMENTATION
# ============================================================

print("\n" + "=" * 60)
print("CUSTOMER RISK SEGMENTATION")
print("=" * 60)

df['churn_risk_score'] = rf.predict_proba(X)[:, 1]
df['risk_segment'] = pd.cut(df['churn_risk_score'], bins=[0, 0.2, 0.4, 0.6, 1.0], labels=['Low Risk', 'Medium Risk', 'High Risk', 'Critical'])

segment_summary = df.groupby('risk_segment', observed=True).agg(
    customers=('customer_id', 'count'),
    actual_churn_rate=('churned', 'mean'),
    avg_balance=('avg_balance_gbp', 'mean'),
    avg_tenure=('tenure_months', 'mean'),
    avg_satisfaction=('satisfaction_score', 'mean')
).round(2)
print(segment_summary)

df.to_csv('data/fintech_customers_with_scores.csv', index=False)
print("\n✓ Scored dataset saved")

conn.close()
print("\n" + "=" * 60)
print("PROJECT 2 COMPLETE")
print("=" * 60)
