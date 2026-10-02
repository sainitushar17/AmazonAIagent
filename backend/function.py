"""
backend/function.py
Core analytical calculation engines and visualization generators for Amazon Sales Report data.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from helper import format_currency, save_chart_image

logger = logging.getLogger(__name__)

# Modern Amazon Analytics Palette
PRIMARY_COLOR = '#FF9900'   # Amazon Orange
SECONDARY_COLOR = '#232F3E' # Amazon Dark Blue
ACCENT_BLUE = '#146EB4'     # Amazon Soft Blue
ACCENT_GREEN = '#007600'    # Success Green
ACCENT_RED = '#B12704'      # Alert/Cancel Red
BG_COLOR = '#FBFBFC'

# Set Seaborn styling
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'


def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculates high-level executive KPIs."""
    if df.empty:
        return {
            "total_revenue": 0.0,
            "formatted_revenue": "₹0.00",
            "total_orders": 0,
            "total_qty": 0,
            "average_order_value": 0.0,
            "formatted_aov": "₹0.00",
            "cancellation_rate": 0.0,
            "top_category": "N/A",
            "top_city": "N/A",
            "b2b_percentage": 0.0
        }

    # Total Orders
    total_orders = df['order_id'].nunique() if 'order_id' in df.columns else len(df)

    # Cancelled Orders
    cancelled_mask = pd.Series(False, index=df.index)
    if 'status' in df.columns:
        cancelled_mask = df['status'].str.lower().str.contains('cancel', na=False)
    cancelled_orders = df[cancelled_mask]['order_id'].nunique() if 'order_id' in df.columns else cancelled_mask.sum()
    cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0.0

    # Net / Shipped Revenue
    valid_sales_df = df[~cancelled_mask] if 'status' in df.columns else df
    total_revenue = float(valid_sales_df['amount'].sum()) if 'amount' in valid_sales_df.columns else 0.0
    total_qty = int(valid_sales_df['qty'].sum()) if 'qty' in valid_sales_df.columns else len(valid_sales_df)

    # AOV (Average Order Value)
    valid_order_count = valid_sales_df['order_id'].nunique() if 'order_id' in valid_sales_df.columns else len(valid_sales_df)
    aov = (total_revenue / valid_order_count) if valid_order_count > 0 else 0.0

    # Top Category
    top_category = "N/A"
    if 'category' in valid_sales_df.columns and not valid_sales_df.empty:
        top_cat_series = valid_sales_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        if not top_cat_series.empty:
            top_category = str(top_cat_series.index[0])

    # Top City
    top_city = "N/A"
    if 'ship_city' in valid_sales_df.columns and not valid_sales_df.empty:
        top_city_series = valid_sales_df['ship_city'].value_counts()
        if not top_city_series.empty:
            top_city = str(top_city_series.index[0]).title()

    # B2B Percentage
    b2b_pct = 0.0
    if 'b2b' in df.columns:
        b2b_orders = df[df['b2b'] == True]['order_id'].nunique() if 'order_id' in df.columns else (df['b2b'] == True).sum()
        b2b_pct = (b2b_orders / total_orders * 100) if total_orders > 0 else 0.0

    return {
        "total_revenue": total_revenue,
        "formatted_revenue": format_currency(total_revenue),
        "total_orders": total_orders,
        "total_qty": total_qty,
        "average_order_value": aov,
        "formatted_aov": format_currency(aov),
        "cancellation_rate": round(cancellation_rate, 2),
        "top_category": top_category,
        "top_city": top_city,
        "b2b_percentage": round(b2b_pct, 2)
    }


def analyze_category_performance(df: pd.DataFrame, top_n: int = 8) -> Dict[str, Any]:
    """Analyzes product categories by revenue, order volume, and unit share."""
    if df.empty or 'category' not in df.columns or 'amount' not in df.columns:
        return {"summary": "Category data not available.", "data": [], "chart_url": None}

    cat_df = df.groupby('category').agg(
        revenue=('amount', 'sum'),
        orders=('order_id', 'nunique') if 'order_id' in df.columns else ('amount', 'count'),
        quantity=('qty', 'sum') if 'qty' in df.columns else ('amount', 'count')
    ).reset_index().sort_values(by='revenue', ascending=False)

    total_revenue = cat_df['revenue'].sum()
    cat_df['share_pct'] = (cat_df['revenue'] / total_revenue * 100).round(2)
    top_cats = cat_df.head(top_n)

    # Generate Chart
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(top_cats['category'][::-1], top_cats['revenue'][::-1] / 100_000, color=ACCENT_BLUE, edgecolor=SECONDARY_COLOR, height=0.65)
    ax.set_xlabel('Revenue (Lakh ₹)', fontsize=11, fontweight='bold', color=SECONDARY_COLOR)
    ax.set_title('Top Product Categories by Gross Revenue', fontsize=13, fontweight='bold', color=SECONDARY_COLOR, pad=15)
    
    # Add data value labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width + (0.5 if width > 0 else 0), bar.get_y() + bar.get_height()/2, 
                f" ₹{width:,.1f}L", va='center', ha='left', fontsize=9, fontweight='bold', color='#333333')

    plt.tight_layout()
    chart_url = save_chart_image(fig, "category_revenue")

    # Format table for response
    data_records = []
    for _, row in top_cats.iterrows():
        data_records.append({
            "category": str(row['category']),
            "revenue": format_currency(row['revenue']),
            "orders": int(row['orders']),
            "share": f"{row['share_pct']}%"
        })

    top_name = str(top_cats.iloc[0]['category']) if not top_cats.empty else "N/A"
    top_share = top_cats.iloc[0]['share_pct'] if not top_cats.empty else 0.0

    summary = (
        f"The top-performing category is **{top_name}**, generating **{format_currency(top_cats.iloc[0]['revenue'])}** "
        f"which represents **{top_share}%** of all sales. "
        f"The top {len(top_cats)} categories account for {top_cats['share_pct'].sum():.1f}% of total catalog revenue."
    )

    return {"summary": summary, "data": data_records, "chart_url": chart_url}


def analyze_sales_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes sales performance across months or time periods."""
    if df.empty or 'date' not in df.columns or 'amount' not in df.columns:
        return {"summary": "Time-series date data not available.", "data": [], "chart_url": None}

    temp_df = df.dropna(subset=['date']).copy()
    if temp_df.empty:
        return {"summary": "No valid dates found in dataset.", "data": [], "chart_url": None}

    temp_df['period'] = temp_df['date'].dt.to_period('M').astype(str)
    trend_df = temp_df.groupby('period').agg(
        revenue=('amount', 'sum'),
        orders=('order_id', 'nunique') if 'order_id' in temp_df.columns else ('amount', 'count')
    ).reset_index().sort_values(by='period')

    if trend_df.empty:
        return {"summary": "Unable to calculate trend.", "data": [], "chart_url": None}

    # Generate Line & Bar combo chart
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()

    x = np.arange(len(trend_df))
    bars = ax1.bar(x, trend_df['revenue'] / 100_000, width=0.45, color=PRIMARY_COLOR, alpha=0.85, label='Revenue (Lakh ₹)')
    line = ax2.plot(x, trend_df['orders'], color=SECONDARY_COLOR, marker='o', linewidth=2.5, label='Order Count')

    ax1.set_xticks(x)
    ax1.set_xticklabels(trend_df['period'], rotation=25, ha='right', fontsize=10)
    ax1.set_ylabel('Revenue (Lakh ₹)', fontsize=11, fontweight='bold', color=PRIMARY_COLOR)
    ax2.set_ylabel('Total Orders', fontsize=11, fontweight='bold', color=SECONDARY_COLOR)
    ax1.set_title('Monthly Revenue & Order Volume Trajectory', fontsize=13, fontweight='bold', pad=15)

    plt.tight_layout()
    chart_url = save_chart_image(fig, "monthly_trend")

    best_period = trend_df.loc[trend_df['revenue'].idxmax()]
    data_records = []
    for _, row in trend_df.iterrows():
        data_records.append({
            "period": str(row['period']),
            "revenue": format_currency(row['revenue']),
            "orders": int(row['orders'])
        })

    summary = (
        f"Sales performance peaked in **{best_period['period']}** with **{format_currency(best_period['revenue'])}** "
        f"in gross revenue across **{int(best_period['orders']):,} orders**. "
        f"Total recorded operational timeline spans {len(trend_df)} months."
    )

    return {"summary": summary, "data": data_records, "chart_url": chart_url}


def analyze_cancellations(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes cancellations, return rates, and financial revenue impact."""
    if df.empty or 'status' not in df.columns:
        return {"summary": "Status data not available.", "data": [], "chart_url": None}

    total_orders = df['order_id'].nunique() if 'order_id' in df.columns else len(df)
    cancelled_df = df[df['status'].str.lower().str.contains('cancel', na=False)]
    cancelled_orders = cancelled_df['order_id'].nunique() if 'order_id' in df.columns else len(cancelled_df)
    cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0.0

    lost_revenue = cancelled_df['amount'].sum() if 'amount' in cancelled_df.columns else 0.0

    # Top cancelled categories
    cat_cancels = cancelled_df['category'].value_counts().head(6) if 'category' in cancelled_df.columns else pd.Series()

    # Generate Chart
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not cat_cancels.empty:
        sns.barplot(x=cat_cancels.values, y=cat_cancels.index, hue=cat_cancels.index, legend=False, ax=ax, palette="Reds_r")
        ax.set_xlabel('Number of Cancelled Orders', fontsize=11, fontweight='bold')
        ax.set_title('Top Product Categories Affected by Cancellations', fontsize=13, fontweight='bold', color=ACCENT_RED, pad=15)
    else:
        status_counts = df['status'].value_counts().head(5)
        sns.barplot(x=status_counts.values, y=status_counts.index, hue=status_counts.index, legend=False, ax=ax, palette="coolwarm")
        ax.set_title('Order Status Overview', fontsize=13, fontweight='bold')

    plt.tight_layout()
    chart_url = save_chart_image(fig, "cancellation_analysis")

    data_records = []
    if not cat_cancels.empty:
        for cat, cnt in cat_cancels.items():
            data_records.append({"category": str(cat), "cancelled_orders": int(cnt)})

    summary = (
        f"Out of **{total_orders:,} total orders**, **{cancelled_orders:,} were cancelled** "
        f"(an overall cancellation rate of **{cancellation_rate:.2f}%**). "
        f"This accounts for approximately **{format_currency(lost_revenue)}** in lost potential gross sales. "
        f"The category with the highest cancellation frequency is **{cat_cancels.index[0] if not cat_cancels.empty else 'N/A'}**."
    )

    return {"summary": summary, "data": data_records, "chart_url": chart_url}


def analyze_fulfillment_methods(df: pd.DataFrame) -> Dict[str, Any]:
    """Compares Merchant (Easy Ship) vs Amazon Fulfillment (FBA)."""
    if df.empty or 'fulfilment' not in df.columns:
        return {"summary": "Fulfillment information not found.", "data": [], "chart_url": None}

    ful_df = df.groupby('fulfilment').agg(
        orders=('order_id', 'nunique') if 'order_id' in df.columns else ('amount', 'count'),
        revenue=('amount', 'sum') if 'amount' in df.columns else ('order_id', 'count')
    ).reset_index()

    total_orders = ful_df['orders'].sum()
    ful_df['share_pct'] = (ful_df['orders'] / total_orders * 100).round(2)

    # Donut chart
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = [ACCENT_BLUE, PRIMARY_COLOR, '#6C757D']
    ax.pie(ful_df['orders'], labels=ful_df['fulfilment'], autopct='%1.1f%%',
           startangle=140, colors=colors[:len(ful_df)],
           wedgeprops=dict(width=0.45, edgecolor='w', linewidth=2))
    ax.set_title('Fulfillment Channel Distribution (Amazon vs Merchant)', fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    chart_url = save_chart_image(fig, "fulfillment_share")

    data_records = []
    for _, row in ful_df.iterrows():
        data_records.append({
            "channel": str(row['fulfilment']),
            "orders": int(row['orders']),
            "revenue": format_currency(row['revenue']),
            "share": f"{row['share_pct']}%"
        })

    dominant = ful_df.sort_values(by='orders', ascending=False).iloc[0]
    summary = (
        f"**{dominant['fulfilment']}** is the dominant channel, handling **{dominant['share_pct']}%** "
        f"({int(dominant['orders']):,} orders) generating **{format_currency(dominant['revenue'])}**. "
        f"Using Amazon-fulfilled logistics typically offers faster delivery times and higher conversion rates."
    )

    return {"summary": summary, "data": data_records, "chart_url": chart_url}


def analyze_geographic_distribution(df: pd.DataFrame, top_n: int = 8) -> Dict[str, Any]:
    """Analyzes customer orders and revenue across states and cities."""
    if df.empty or 'ship_state' not in df.columns:
        return {"summary": "Geographical state data not available.", "data": [], "chart_url": None}

    state_df = df.groupby('ship_state').agg(
        orders=('order_id', 'nunique') if 'order_id' in df.columns else ('amount', 'count'),
        revenue=('amount', 'sum') if 'amount' in df.columns else ('order_id', 'count')
    ).reset_index().sort_values(by='revenue', ascending=False).head(top_n)

    # Generate Chart
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=state_df, x='revenue', y='ship_state', hue='ship_state', legend=False, ax=ax, palette="Blues_r")
    ax.set_xlabel('Revenue (₹)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Destination State', fontsize=11, fontweight='bold')
    ax.set_title(f'Top {top_n} Indian States by Sales Revenue', fontsize=13, fontweight='bold', color=SECONDARY_COLOR, pad=15)
    plt.tight_layout()
    chart_url = save_chart_image(fig, "geographic_distribution")

    data_records = []
    for _, row in state_df.iterrows():
        data_records.append({
            "state": str(row['ship_state']).title(),
            "revenue": format_currency(row['revenue']),
            "orders": int(row['orders'])
        })

    top_state = str(state_df.iloc[0]['ship_state']).title() if not state_df.empty else "N/A"
    summary = (
        f"The primary regional market is **{top_state}**, leading in both volume and revenue with "
        f"**{format_currency(state_df.iloc[0]['revenue'])}** across **{int(state_df.iloc[0]['orders']):,} orders**. "
        f"Targeting local regional ad campaigns in top states can generate higher return on ad spend."
    )

    return {"summary": summary, "data": data_records, "chart_url": chart_url}


def analyze_product_sizes(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes demand by clothing sizes."""
    if df.empty or 'size' not in df.columns:
        return {"summary": "Size attribute not available.", "data": [], "chart_url": None}

    size_counts = df['size'].value_counts().head(8)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(x=size_counts.index, y=size_counts.values, hue=size_counts.index, legend=False, ax=ax, palette="viridis")
    ax.set_xlabel('Size', fontsize=11, fontweight='bold')
    ax.set_ylabel('Units Sold / Orders', fontsize=11, fontweight='bold')
    ax.set_title('Popularity of Apparel Sizes', fontsize=13, fontweight='bold', color=SECONDARY_COLOR, pad=15)
    plt.tight_layout()
    chart_url = save_chart_image(fig, "size_distribution")

    data_records = [{"size": str(s), "count": int(c)} for s, c in size_counts.items()]
    summary = (
        f"The most popular size requested is **{size_counts.index[0]}** ({size_counts.iloc[0]:,} orders), "
        f"followed by **{size_counts.index[1] if len(size_counts) > 1 else 'N/A'}**. "
        f"Ensuring adequate warehouse inventory in M, L, and XL sizes helps mitigate stockouts."
    )

    return {"summary": summary, "data": data_records, "chart_url": chart_url}


def analyze_b2b_vs_b2c(df: pd.DataFrame) -> Dict[str, Any]:
    """Compares B2B bulk purchases against B2C direct consumer sales."""
    if df.empty or 'b2b' not in df.columns:
        return {"summary": "B2B flag not available in dataset.", "data": [], "chart_url": None}

    b2b_df = df.groupby('b2b').agg(
        orders=('order_id', 'nunique') if 'order_id' in df.columns else ('amount', 'count'),
        revenue=('amount', 'sum') if 'amount' in df.columns else ('order_id', 'count')
    ).reset_index()

    b2b_df['label'] = b2b_df['b2b'].apply(lambda x: 'B2B (Business)' if x else 'B2C (Retail Consumer)')
    total_rev = b2b_df['revenue'].sum()
    b2b_df['share'] = (b2b_df['revenue'] / total_rev * 100).round(2)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.pie(b2b_df['revenue'], labels=b2b_df['label'], autopct='%1.1f%%',
           colors=[ACCENT_BLUE, PRIMARY_COLOR], startangle=90,
           wedgeprops=dict(width=0.4, edgecolor='w'))
    ax.set_title('Revenue Breakdown: B2B vs B2C', fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    chart_url = save_chart_image(fig, "b2b_vs_b2c")

    data_records = []
    for _, row in b2b_df.iterrows():
        data_records.append({
            "segment": row['label'],
            "revenue": format_currency(row['revenue']),
            "orders": int(row['orders']),
            "share": f"{row['share']}%"
        })

    b2b_row = b2b_df[b2b_df['b2b'] == True]
    b2b_share = b2b_row['share'].values[0] if not b2b_row.empty else 0.0

    summary = (
        f"Retail consumers (**B2C**) account for the massive majority of transactions, while **B2B** represents "
        f"**{b2b_share}%** of revenue. Introducing dedicated B2B tiered pricing and quantity discounts "
        f"presents a high-growth opportunity to increase wholesale orders."
    )

    return {"summary": summary, "data": data_records, "chart_url": chart_url}


def analyze_top_skus(df: pd.DataFrame, top_n: int = 10) -> Dict[str, Any]:
    """Extracts top performing SKUs and Styles."""
    if df.empty or 'sku' not in df.columns or 'amount' not in df.columns:
        return {"summary": "SKU data not available.", "data": [], "chart_url": None}

    sku_df = df.groupby('sku').agg(
        revenue=('amount', 'sum'),
        quantity=('qty', 'sum') if 'qty' in df.columns else ('amount', 'count')
    ).reset_index().sort_values(by='revenue', ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=sku_df, x='revenue', y='sku', hue='sku', legend=False, ax=ax, palette="mako")
    ax.set_xlabel('Gross Revenue (₹)', fontsize=11, fontweight='bold')
    ax.set_title(f'Top {top_n} Best-Selling SKUs by Gross Revenue', fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    chart_url = save_chart_image(fig, "top_skus")

    data_records = []
    for _, row in sku_df.iterrows():
        data_records.append({
            "sku": str(row['sku']),
            "revenue": format_currency(row['revenue']),
            "units_sold": int(row['quantity'])
        })

    best_sku = sku_df.iloc[0]
    summary = (
        f"The top-performing SKU in the catalog is **{best_sku['sku']}**, generating "
        f"**{format_currency(best_sku['revenue'])}** with **{int(best_sku['quantity']):,} units sold**. "
        f"Maintaining continuous safety stock for these top 10 SKUs is critical to protect core turnover."
    )

    return {"summary": summary, "data": data_records, "chart_url": chart_url}
