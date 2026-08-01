import pandas as pd
import numpy as np
import os
import glob
from sklearn.preprocessing import StandardScaler, LabelEncoder

# ==========================================
# 0. DATA LOADING & PATH RESOLUTION
# ==========================================
# Dynamically locate project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
raw_folder = os.path.join(project_dir, 'data', 'raw')

print(f"[INFO] Searching for raw dataset in: {raw_folder}")

# Locate matching CSV dataset file inside data/raw directory
possible_files = glob.glob(os.path.join(raw_folder, "*marketing*")) + glob.glob(os.path.join(raw_folder, "*.csv"))

if not possible_files:
    print("\n[ERROR] No dataset file found in 'data/raw' directory.")
    print("[ERROR] Please ensure 'marketing_campaign.csv' is placed inside 'Customer-Personality-Segmentation/data/raw/'.")
    exit()

input_path = possible_files[0]
print(f"[INFO] File located. Loading dataset from: {input_path}")

# Delimiter handling (Tab vs Comma separation)
try:
    df = pd.read_csv(input_path, sep='\t')
    if len(df.columns) == 1:
        df = pd.read_csv(input_path, sep=',')
except Exception:
    df = pd.read_csv(input_path, sep=',')

print(f"[INFO] Dataset loaded successfully. Initial shape: {df.shape}")

# ==========================================
# TASK 1: CUSTOMER FEATURE CREATION
# ==========================================
print("\n[INFO] Task 1: Engineering behavioral features...")

# 1. Customer Age & Tenure
df['Customer_Age'] = 2026 - df['Year_Birth']
df['Dt_Customer'] = pd.to_datetime(df['Dt_Customer'], format='%d-%m-%Y', errors='coerce')
df['Customer_Tenure'] = (pd.to_datetime('today') - df['Dt_Customer']).dt.days // 365

# 2. Family Dynamics & Household Size
df['Total_Children'] = df['Kidhome'] + df['Teenhome']
marital_map = {'Single': 1, 'Together': 2, 'Married': 2, 'Divorced': 1, 'Widow': 1, 'Alone': 1, 'Absurd': 1, 'YOLO': 1}
df['Family_Size'] = df['Marital_Status'].map(marital_map).fillna(1) + df['Total_Children']

# 3. Total Spending & Total Purchases
spend_cols = ['MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']
purchase_cols = ['NumWebPurchases', 'NumCatalogPurchases', 'NumStorePurchases']

df['Total_Spending'] = df[spend_cols].sum(axis=1)
df['Total_Purchases'] = df[purchase_cols].sum(axis=1)

# 4. Campaign Responsiveness
campaign_cols = ['AcceptedCmp1', 'AcceptedCmp2', 'AcceptedCmp3', 'AcceptedCmp4', 'AcceptedCmp5', 'Response']
df['Total_Campaign_Acceptance'] = df[campaign_cols].sum(axis=1)

# 5. Spending Ratios & Engagement Metrics
df['Avg_Spending_Per_Purchase'] = np.where(df['Total_Purchases'] > 0, df['Total_Spending'] / df['Total_Purchases'], 0)
df['Digital_Engagement'] = df['NumWebPurchases'] + df['NumWebVisitsMonth']
df['Deal_Dependency'] = np.where(df['Total_Purchases'] > 0, df['NumDealsPurchases'] / df['Total_Purchases'], 0)

# 6. Channel Preferences & Activity Categorization
df['Preferred_Shopping_Channel'] = df[purchase_cols].idxmax(axis=1).str.replace('Num', '').str.replace('Purchases', '')
df['Product_Preference'] = df[spend_cols].idxmax(axis=1).str.replace('Mnt', '')
df['Customer_Activity_Level'] = pd.qcut(df['Total_Purchases'], q=3, labels=['Low', 'Medium', 'High'])

# Missing value imputation for Income
df['Income'] = df['Income'].fillna(df['Income'].median())

# ==========================================
# TASK 2: CATEGORICAL FEATURE ENCODING
# ==========================================
print("[INFO] Task 2: Encoding categorical features...")

# Ordinal Encoding for Activity Level
le = LabelEncoder()
df['Customer_Activity_Level_Encoded'] = le.fit_transform(df['Customer_Activity_Level'])

# One-Hot Encoding for nominal variables
df = pd.get_dummies(df, columns=['Marital_Status', 'Education', 'Preferred_Shopping_Channel', 'Product_Preference'], drop_first=True)

# ==========================================
# TASK 3: FEATURE SELECTION
# ==========================================
print("[INFO] Task 3: Performing feature selection...")

# Drop identifier columns and redundant features
drop_cols = ['ID', 'Year_Birth', 'Dt_Customer', 'Z_CostContact', 'Z_Revenue', 'Customer_Activity_Level']
df_selected = df.drop(columns=[c for c in drop_cols if c in df.columns])

# ==========================================
# TASK 4: SKEWNESS & FEATURE TRANSFORMATION
# ==========================================
print("[INFO] Task 4: Transforming skewed features using log transformation...")

skewed_features = ['Total_Spending', 'Income', 'Avg_Spending_Per_Purchase']
for col in skewed_features:
    if col in df_selected.columns:
        df_selected[col + '_Log'] = np.log1p(df_selected[col].clip(lower=0))

# ==========================================
# TASK 5: FEATURE SCALING
# ==========================================
print("[INFO] Task 5: Normalizing numerical features with StandardScaler...")

scaler = StandardScaler()
num_cols = df_selected.select_dtypes(include=['float64', 'int64']).columns
df_scaled = df_selected.copy()
df_scaled[num_cols] = scaler.fit_transform(df_selected[num_cols])

# ==========================================
# TASK 8: DATASET VALIDATION & EXPORT
# ==========================================
processed_dir = os.path.join(project_dir, 'data', 'processed')
os.makedirs(processed_dir, exist_ok=True)

output_path = os.path.join(processed_dir, 'final_engineered_customer_data.csv')
df_scaled.to_csv(output_path, index=False)

print("\n[SUCCESS] Feature engineering pipeline executed successfully.")
print(f"[SUCCESS] Final ML-ready dataset saved at:\n'{output_path}'")
