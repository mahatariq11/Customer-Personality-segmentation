import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler

class CustomerFeaturePipeline(BaseEstimator, TransformerMixin):
    """
    Reusable Preprocessing Pipeline for Customer Personality Segmentation.
    """
    def __init__(self, current_year=2026):
        self.current_year = current_year
        self.scaler = StandardScaler()

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()
        
        # Missing Value Imputation
        if 'Income' in df.columns:
            df['Income'] = df['Income'].fillna(df['Income'].median())
            
        # Feature Creation
        if 'Year_Birth' in df.columns:
            df['Customer_Age'] = self.current_year - df['Year_Birth']
            
        df['Total_Children'] = df['Kidhome'] + df['Teenhome']
        
        spend_cols = [c for c in df.columns if c.startswith('Mnt')]
        purchase_cols = [c for c in df.columns if c.startswith('Num') and 'Purchases' in c]
        
        df['Total_Spending'] = df[spend_cols].sum(axis=1)
        df['Total_Purchases'] = df[purchase_cols].sum(axis=1)
        
        # Log Transformations
        df['Total_Spending_Log'] = np.log1p(df['Total_Spending'].clip(lower=0))
        df['Income_Log'] = np.log1p(df['Income'].clip(lower=0))
        
        # Drop Redundant Identifiers
        drop_cols = ['ID', 'Year_Birth', 'Dt_Customer', 'Z_CostContact', 'Z_Revenue']
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        
        return df

if __name__ == "__main__":
    print("[INFO] Reusable Preprocessing Pipeline Script Loaded Successfully.")
