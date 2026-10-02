"""
helper.py
Utility functions for dataset loading, data cleaning, number formatting,
file upload management, and chart serialization.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(DATASET_DIR, "csv"), exist_ok=True)
os.makedirs(os.path.join(DATASET_DIR, "json"), exist_ok=True)
os.makedirs(os.path.join(DATASET_DIR, "images"), exist_ok=True)


def format_currency(value: float, currency_symbol: str = "₹") -> str:
    """Formats numeric values into friendly currency format."""
    if pd.isna(value) or value is None:
        return f"{currency_symbol}0.00"
    
    val = float(value)
    abs_val = abs(val)
    prefix = "-" if val < 0 else ""
    
    if abs_val >= 10_000_000:
        return f"{prefix}{currency_symbol}{abs_val / 10_000_000:.2f} Cr"
    elif abs_val >= 100_000:
        return f"{prefix}{currency_symbol}{abs_val / 100_000:.2f} Lakh"
    elif abs_val >= 1_000:
        return f"{prefix}{currency_symbol}{abs_val:,.2f}"
    else:
        return f"{prefix}{currency_symbol}{abs_val:.2f}"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans raw Amazon Sales Report dataframe."""
    # Standardize column names
    df.columns = [str(c).strip() for c in df.columns]
    
    # Drop unnamed/empty index columns if present
    drop_cols = [c for c in df.columns if c.lower().startswith('unnamed') or c == 'index']
    if drop_cols:
        df = df.drop(columns=drop_cols, errors='ignore')
        
    # Map common column variations
    col_mapping = {
        'Order ID': 'order_id',
        'Date': 'date',
        'Status': 'status',
        'Fulfilment': 'fulfilment',
        'Sales Channel': 'sales_channel',
        'ship-service-level': 'ship_service_level',
        'Style': 'style',
        'SKU': 'sku',
        'Category': 'category',
        'Size': 'size',
        'ASIN': 'asin',
        'Courier Status': 'courier_status',
        'Qty': 'qty',
        'currency': 'currency',
        'Amount': 'amount',
        'ship-city': 'ship_city',
        'ship-state': 'ship_state',
        'ship-postal-code': 'ship_postal_code',
        'ship-country': 'ship_country',
        'promotion-ids': 'promotion_ids',
        'B2B': 'b2b',
        'fulfilled-by': 'fulfilled_by'
    }
    
    rename_dict = {}
    for col in df.columns:
        if col in col_mapping:
            rename_dict[col] = col_mapping[col]
        else:
            # normalized lower case
            clean_name = col.lower().replace(' ', '_').replace('-', '_')
            rename_dict[col] = clean_name
            
    df = df.rename(columns=rename_dict)
    
    # Cast Amount to numeric
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        
    # Cast Qty to numeric
    if 'qty' in df.columns:
        df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(1).astype(int)
        
    # Cast Date to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce', format='mixed')
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        df['month_name'] = df['date'].dt.strftime('%B %Y')
        
    # Clean text strings
    text_cols = ['status', 'category', 'fulfilment', 'ship_city', 'ship_state', 'size', 'style', 'sku']
    for tc in text_cols:
        if tc in df.columns:
            df[tc] = df[tc].astype(str).str.strip().replace('nan', 'Unknown')
            
    # Normalize B2B column
    if 'b2b' in df.columns:
        df['b2b'] = df['b2b'].astype(str).str.lower().isin(['true', '1', 'yes', 't'])
        
    return df


def load_dataset(file_path: Optional[str] = None) -> pd.DataFrame:
    """Loads dataset from CSV or JSON file path."""
    if not file_path or not os.path.exists(file_path):
        # Fallback to default CSV path
        csv_default = os.path.join(DATASET_DIR, "csv", "amazon_sales_report.csv")
        json_default = os.path.join(DATASET_DIR, "json", "amazon_sales_sample.json")
        if os.path.exists(csv_default):
            file_path = csv_default
        elif os.path.exists(json_default):
            file_path = json_default
        else:
            logger.warning("No default dataset found. Creating empty dataset.")
            return pd.DataFrame()
            
    logger.info(f"Loading dataset from: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.csv':
            # Low_memory=False to prevent mixed type warnings
            df = pd.read_csv(file_path, low_memory=False)
        elif ext == '.json':
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported dataset format: {ext}")
            
        df = clean_dataframe(df)
        logger.info(f"Dataset successfully loaded with {len(df):,} records and {len(df.columns)} columns.")
        return df
    except Exception as e:
        logger.error(f"Error loading dataset from {file_path}: {e}")
        return pd.DataFrame()


def save_chart_image(fig: plt.Figure, filename_prefix: str = "chart") -> str:
    """Saves a matplotlib figure to the outputs directory and returns its relative web path."""
    import time
    timestamp = int(time.time() * 1000)
    filename = f"{filename_prefix}_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, bbox_inches='tight', dpi=120)
    plt.close(fig)
    return f"/outputs/{filename}"


def get_available_datasets() -> Dict[str, Any]:
    """Scans the dataset directory for CSV, JSON, and Image files."""
    csv_files = []
    json_files = []
    image_files = []
    
    csv_dir = os.path.join(DATASET_DIR, "csv")
    json_dir = os.path.join(DATASET_DIR, "json")
    img_dir = os.path.join(DATASET_DIR, "images")
    
    if os.path.exists(csv_dir):
        for f in os.listdir(csv_dir):
            fp = os.path.join(csv_dir, f)
            if os.path.isfile(fp) and f.endswith('.csv'):
                csv_files.append({
                    "name": f,
                    "path": fp,
                    "size_mb": round(os.path.getsize(fp) / (1024 * 1024), 2),
                    "type": "CSV"
                })
                
    if os.path.exists(json_dir):
        for f in os.listdir(json_dir):
            fp = os.path.join(json_dir, f)
            if os.path.isfile(fp) and f.endswith('.json'):
                json_files.append({
                    "name": f,
                    "path": fp,
                    "size_mb": round(os.path.getsize(fp) / (1024 * 1024), 2),
                    "type": "JSON"
                })
                
    if os.path.exists(img_dir):
        for f in os.listdir(img_dir):
            fp = os.path.join(img_dir, f)
            if os.path.isfile(fp) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
                image_files.append({
                    "name": f,
                    "path": fp,
                    "size_kb": round(os.path.getsize(fp) / 1024, 2),
                    "url": f"/dataset/images/{f}",
                    "type": "IMAGE"
                })
                
    return {
        "csv": csv_files,
        "json": json_files,
        "images": image_files
    }


def save_uploaded_file(file_storage, custom_name: Optional[str] = None) -> Tuple[bool, str, str]:
    """Saves an uploaded file to the appropriate dataset subfolder."""
    filename = custom_name or file_storage.filename
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.csv':
        target_dir = os.path.join(DATASET_DIR, "csv")
        file_type = "CSV"
    elif ext == '.json':
        target_dir = os.path.join(DATASET_DIR, "json")
        file_type = "JSON"
    elif ext in ['.png', '.jpg', '.jpeg', '.webp', '.svg']:
        target_dir = os.path.join(DATASET_DIR, "images")
        file_type = "IMAGE"
    else:
        return False, f"Unsupported file type: {ext}. Upload CSV, JSON, or images (.png, .jpg).", ""
        
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, filename)
    file_storage.save(target_path)
    
    return True, f"Successfully uploaded {filename} to dataset/{file_type.lower()}", target_path
