import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def create_sample_dataset():
    print('Creating sample dataset for ZK proof testing...')
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Generate sample financial transaction data
    num_records = 50000  # Should create multiple 2MB blocks
    
    # Generate realistic financial data
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=random.randint(0, 365)) for _ in range(num_records)]
    
    data = {
        'transaction_id': [f'TXN_{i:08d}' for i in range(1, num_records + 1)],
        'timestamp': [date.strftime('%Y-%m-%d %H:%M:%S') for date in dates],
        'user_id': [f'USER_{random.randint(1000, 9999)}' for _ in range(num_records)],
        'account_from': [f'ACC_{random.randint(100000, 999999)}' for _ in range(num_records)],
        'account_to': [f'ACC_{random.randint(100000, 999999)}' for _ in range(num_records)],
        'amount': np.round(np.random.lognormal(mean=3, sigma=1.5, size=num_records), 2),
        'currency': np.random.choice(['USD', 'EUR', 'GBP', 'JPY'], size=num_records, p=[0.5, 0.25, 0.15, 0.1]),
        'transaction_type': np.random.choice(['transfer', 'payment', 'withdrawal', 'deposit'], size=num_records, p=[0.4, 0.3, 0.15, 0.15]),
        'status': np.random.choice(['completed', 'pending', 'failed'], size=num_records, p=[0.85, 0.1, 0.05]),
        'fee': np.round(np.random.uniform(0.1, 5.0, size=num_records), 2),
        'merchant_id': [f'MERCH_{random.randint(1000, 9999)}' if random.random() < 0.6 else '' for _ in range(num_records)],
        'description': [f'Transaction {i} - {random.choice(["Online purchase", "ATM withdrawal", "Bank transfer", "Bill payment", "Salary deposit"])}' for i in range(num_records)]
    }
    
    df = pd.DataFrame(data)
    
    # Save the dataset
    output_file = 'sample_financial_dataset.csv'
    df.to_csv(output_file, index=False)
    
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f'✅ Created {output_file}')
    print(f'📊 Records: {len(df):,}')
    print(f'📁 Size: {file_size_mb:.2f} MB')
    print(f'🔢 Columns: {len(df.columns)}')
    print(f'💰 Amount range: ${df["amount"].min():.2f} - ${df["amount"].max():.2f}')
    print(f'📅 Date range: {df["timestamp"].min()} to {df["timestamp"].max()}')
    
    # Show sample data
    print(f'\n📋 Sample records:')
    print(df.head(3).to_string(index=False))
    
    return output_file

if __name__ == "__main__":
    create_sample_dataset()