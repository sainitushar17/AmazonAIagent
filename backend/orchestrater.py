"""
backend/orchestrater.py
Autonomous Orchestration Agent for Natural Language E-commerce Data Analysis.
Supports both an Advanced Offline Multi-Dimensional Semantic Engine (no API key required)
and an LLM-Powered Python/Pandas Code Synthesis Engine (via Gemini or OpenAI).
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

from text import SYSTEM_PROMPT, EXPLAIN_TEMPLATES
from helper import format_currency, save_chart_image
from backend.models import dataset_store
import backend.function as fn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)

logger = logging.getLogger(__name__)

def get_gemini_key():
    return os.getenv("GEMINI_API_KEY", "").strip()

def get_openai_key():
    return os.getenv("OPENAI_API_KEY", "").strip()

MONTH_MAP = {
    'january': 1, 'jan': 1,
    'february': 2, 'feb': 2,
    'march': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'may': 5,
    'june': 6, 'jun': 6,
    'july': 7, 'jul': 7,
    'august': 8, 'aug': 8,
    'september': 9, 'sep': 9,
    'october': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'december': 12, 'dec': 12
}


class OrchestraterAgent:
    """Autonomous Orchestrator that coordinates natural language understanding,
    dynamic multi-dimensional data querying, visualization generation, and narrative reporting."""

    def __init__(self):
        self.store = dataset_store

    def plan_and_execute(
        self,
        query: str,
        schema_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main entry point: parses user English query, incorporates schema/context, and executes analysis."""
        df = self.store.get_data()
        if df.empty:
            return {
                "answer": "⚠️ No sales dataset is currently loaded. Please upload a CSV or JSON dataset to begin.",
                "intent": "empty_dataset",
                "chart_url": None,
                "data_table": [],
                "schema_used": {"columns": [], "custom_schema": schema_info or {}},
                "context_applied": context or {},
                "suggestions": ["Upload Amazon Sales Report CSV", "Load sample JSON dataset"],
                "execution_type": "offline_engine",
                "status": "error"
            }

        query_clean = query.strip()
        logger.info(f"Processing query: '{query_clean}' with schema_info: {bool(schema_info)}, context: {bool(context)}")

        # 1. If an LLM API key (Gemini or OpenAI) is configured, try LLM Code Synthesis first with schema and context
        gemini_key = get_gemini_key()
        openai_key = get_openai_key()
        if gemini_key or openai_key:
            llm_result = self._try_llm_code_execution(query_clean, df, schema_info=schema_info, context=context)
            if llm_result and llm_result.get("status") == "success":
                llm_result["schema_used"] = {"columns": list(df.columns), "custom_schema": schema_info or {}}
                llm_result["context_applied"] = context or {}
                return llm_result

        # 2. Advanced Offline Multi-Dimensional Semantic Engine (100% offline, zero API keys needed)
        result = self._execute_dynamic_semantic_query(query_clean, df, context=context)
        result["schema_used"] = {"columns": list(df.columns), "custom_schema": schema_info or {}}
        result["context_applied"] = context or {}
        return result

    def _execute_dynamic_semantic_query(self, query: str, df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts filters, metrics, and grouping dimensions to answer arbitrary questions."""
        q_lower = query.lower()

        # Step 1: Detect Filters
        filtered_df = df.copy()
        applied_filters = []

        # Context-specified filters (from API or session)
        if context and isinstance(context, dict):
            ctx_items = {}
            if "filters" in context and isinstance(context["filters"], dict):
                ctx_items.update(context["filters"])
            if "filter" in context and isinstance(context["filter"], dict):
                ctx_items.update(context["filter"])
            for k, v in context.items():
                if k not in ["filters", "filter"] and not isinstance(v, (dict, list)):
                    ctx_items[k] = v

            for col_candidate, val in ctx_items.items():
                if val is None or val == "":
                    continue
                matched_col = None
                normalized_cand = col_candidate.lower().replace(" ", "_").replace("-", "_")
                for col in df.columns:
                    if col.lower() == normalized_cand:
                        matched_col = col
                        break
                if matched_col:
                    val_str = str(val).strip().lower()
                    if pd.api.types.is_bool_dtype(filtered_df[matched_col]):
                        b_val = val_str in ['true', '1', 'yes']
                        filtered_df = filtered_df[filtered_df[matched_col] == b_val]
                    elif pd.api.types.is_numeric_dtype(filtered_df[matched_col]):
                        try:
                            n_val = float(val)
                            filtered_df = filtered_df[filtered_df[matched_col] == n_val]
                        except ValueError:
                            pass
                    else:
                        filtered_df = filtered_df[filtered_df[matched_col].astype(str).str.strip().str.lower() == val_str]
                    applied_filters.append(f"{matched_col}: **{val}** (context)")

        # Category filter (skip if already filtered via context)
        has_category_filter = any('category' in f.lower() for f in applied_filters)
        if 'category' in df.columns and not has_category_filter:
            for cat in sorted(df['category'].dropna().unique(), key=lambda x: len(str(x)), reverse=True):
                cat_str = str(cat).strip()
                # Special disambiguation for category "Top": avoid treating ranking phrases like "top 5", "top cities" as the garment
                if cat_str.lower() == 'top':
                    if re.search(r'\btop\s+(\d+|cities|city|states|state|categories|category|products|sku|skus|sellers|selling|markets|market|performing|revenue)\b', q_lower):
                        continue
                    if not re.search(r'\b(tops|crop top|women top|category\s+top)\b', q_lower):
                        continue
                if re.search(r'\b' + re.escape(cat_str.lower()) + r'\b', q_lower):
                    filtered_df = filtered_df[filtered_df['category'].str.lower() == cat_str.lower()]
                    applied_filters.append(f"Category: **{cat_str}**")
                    break

        # State filter
        if 'ship_state' in df.columns:
            for st in df['ship_state'].dropna().unique():
                st_str = str(st).strip()
                if len(st_str) > 2 and re.search(r'\b' + re.escape(st_str.lower()) + r'\b', q_lower):
                    filtered_df = filtered_df[filtered_df['ship_state'].str.lower() == st_str.lower()]
                    applied_filters.append(f"State: **{st_str.title()}**")
                    break

        # City filter
        if 'ship_city' in df.columns:
            # Check major cities first
            for city in df['ship_city'].value_counts().head(300).index:
                city_str = str(city).strip()
                if len(city_str) > 3 and re.search(r'\b' + re.escape(city_str.lower()) + r'\b', q_lower):
                    filtered_df = filtered_df[filtered_df['ship_city'].str.lower() == city_str.lower()]
                    applied_filters.append(f"City: **{city_str.title()}**")
                    break

        # Month filter
        if 'date' in df.columns:
            for m_name, m_num in MONTH_MAP.items():
                if re.search(r'\b' + re.escape(m_name) + r'\b', q_lower):
                    filtered_df = filtered_df[filtered_df['date'].dt.month == m_num]
                    applied_filters.append(f"Month: **{m_name.title()}**")
                    break

        # Status filter
        is_cancel_rate_query = any(w in q_lower for w in ['cancellation rate', 'cancel rate', 'rate of cancellation', 'cancel percentage', 'rate of cancel'])
        if 'status' in df.columns and not is_cancel_rate_query:
            if any(w in q_lower for w in ['cancelled orders', 'only cancel', 'cancelled', 'cancellations', 'cancellation']) and 'rate' not in q_lower:
                filtered_df = filtered_df[filtered_df['status'].str.lower().str.contains('cancel', na=False)]
                applied_filters.append("Status: **Cancelled**")
            elif any(w in q_lower for w in ['delivered', 'delivery']):
                filtered_df = filtered_df[filtered_df['status'].str.lower().str.contains('deliver', na=False)]
                applied_filters.append("Status: **Delivered**")
            elif 'shipped' in q_lower and 'cancel' not in q_lower:
                filtered_df = filtered_df[filtered_df['status'].str.lower().str.contains('ship', na=False)]
                applied_filters.append("Status: **Shipped**")

        # Size filter
        if 'size' in df.columns:
            for sz in ['3xl', 'xxxl', '2xl', 'xxl', 'xl', 'xs', 's', 'm', 'l', '4xl', '5xl', '6xl']:
                if re.search(r'\b' + re.escape(sz) + r'\b', q_lower):
                    filtered_df = filtered_df[filtered_df['size'].str.lower() == sz]
                    applied_filters.append(f"Size: **{sz.upper()}**")
                    break

        # Fulfillment filter
        if 'fulfilment' in df.columns:
            if 'amazon' in q_lower or 'fba' in q_lower:
                filtered_df = filtered_df[filtered_df['fulfilment'].str.lower() == 'amazon']
                applied_filters.append("Fulfillment: **Amazon (FBA)**")
            elif 'merchant' in q_lower or 'easy ship' in q_lower:
                filtered_df = filtered_df[filtered_df['fulfilment'].str.lower() == 'merchant']
                applied_filters.append("Fulfillment: **Merchant**")

        # Shipping Service Level filter
        if 'ship_service_level' in df.columns:
            if 'expedited' in q_lower:
                filtered_df = filtered_df[filtered_df['ship_service_level'].str.lower() == 'expedited']
                applied_filters.append("Shipping: **Expedited**")
            elif 'standard' in q_lower:
                filtered_df = filtered_df[filtered_df['ship_service_level'].str.lower() == 'standard']
                applied_filters.append("Shipping: **Standard**")

        # B2B filter
        if 'b2b' in df.columns:
            if any(w in q_lower for w in ['b2b', 'wholesale', 'business buyer']):
                filtered_df = filtered_df[filtered_df['b2b'] == True]
                applied_filters.append("Segment: **B2B (Wholesale)**")
            elif any(w in q_lower for w in ['b2c', 'retail consumer']):
                filtered_df = filtered_df[filtered_df['b2b'] == False]
                applied_filters.append("Segment: **B2C (Retail)**")

        # Step 2: Detect Grouping / Ranking / Listing Request
        group_col = None
        group_label = None
        chart_title = None

        if any(w in q_lower for w in [
            'list of product', 'list of products', 'products', 'product', 'items', 'item', 'catalog',
            'by category', 'which category', 'top category', 'top categories', 'categories', 'category',
            'product list', 'what products', 'all products', 'best selling product', 'best selling products'
        ]):
            group_col = 'category'
            group_label = 'Product Category'
            chart_title = 'Product Category Breakdown'
        elif any(w in q_lower for w in ['by city', 'which city', 'top city', 'top cities', 'cities', 'city', 'list of cities', 'markets', 'market']):
            group_col = 'ship_city'
            group_label = 'City'
            chart_title = 'Top Cities'
        elif any(w in q_lower for w in ['by state', 'which state', 'top state', 'top states', 'states', 'state', 'list of states']):
            group_col = 'ship_state'
            group_label = 'State'
            chart_title = 'Top States'
        elif any(w in q_lower for w in ['by size', 'which size', 'popular size', 'popular sizes', 'sizes', 'size', 'list of sizes']):
            group_col = 'size'
            group_label = 'Size'
            chart_title = 'Size Distribution'
        elif any(w in q_lower for w in ['by month', 'monthly', 'over time', 'trend', 'trajectory', 'sales over time', 'timeline']):
            group_col = 'year_month'
            group_label = 'Month'
            chart_title = 'Monthly Trajectory'
        elif any(w in q_lower for w in ['by fulfillment', 'amazon vs merchant', 'channel', 'fulfillment']):
            group_col = 'fulfilment'
            group_label = 'Fulfillment Channel'
            chart_title = 'Fulfillment Breakdown'
        elif any(w in q_lower for w in ['by status', 'order status', 'statuses', 'status breakdown', 'status']):
            group_col = 'status'
            group_label = 'Status'
            chart_title = 'Status Breakdown'
        elif any(w in q_lower for w in ['style', 'styles', 'best style', 'top style', 'list of styles']):
            group_col = 'style'
            group_label = 'Style'
            chart_title = 'Top Styles'
        elif any(w in q_lower for w in ['by sku', 'top sku', 'top skus', 'skus', 'sku', 'which sku', 'list of skus']):
            group_col = 'sku'
            group_label = 'SKU'
            chart_title = 'Top SKUs'

        # If grouping/breakdown requested
        if group_col and group_col in filtered_df.columns and not filtered_df.empty:
            return self._generate_grouped_response(query, filtered_df, group_col, group_label, chart_title, applied_filters)

        # Step 3: Compute Direct Metrics on Filtered Data
        if filtered_df.empty:
            return {
                "answer": f"### 🔍 No Records Found\n\nNo records match your specified criteria: {', '.join(applied_filters) if applied_filters else query}.\n\nPlease try adjusting the filter terms.",
                "intent": "empty_filtered_result",
                "chart_url": None,
                "data_table": [],
                "suggestions": ["What is our total revenue?", "Which are the top 5 categories?"],
                "execution_type": "dynamic_semantic_engine",
                "status": "success"
            }

        total_orders = filtered_df['order_id'].nunique() if 'order_id' in filtered_df.columns else len(filtered_df)
        total_revenue = float(filtered_df['amount'].sum()) if 'amount' in filtered_df.columns else 0.0
        total_qty = int(filtered_df['qty'].sum()) if 'qty' in filtered_df.columns else len(filtered_df)
        aov = (total_revenue / total_orders) if total_orders > 0 else 0.0
        max_amount = float(filtered_df['amount'].max()) if 'amount' in filtered_df.columns else 0.0
        min_amount = float(filtered_df[filtered_df['amount'] > 0]['amount'].min()) if 'amount' in filtered_df.columns and not filtered_df[filtered_df['amount'] > 0].empty else 0.0

        pct_of_total_orders = (total_orders / (df['order_id'].nunique() if 'order_id' in df.columns else len(df)) * 100)
        pct_of_total_rev = (total_revenue / (df['amount'].sum() if 'amount' in df.columns else 1.0) * 100)

        # Check for specific metric questions
        if any(w in q_lower for w in ['how many orders', 'order count', 'number of orders', 'how many transactions']):
            metric_highlight = f"**{total_orders:,} orders**"
            primary_text = f"There were {metric_highlight} matching your request."
        elif any(w in q_lower for w in ['how many items', 'quantity', 'units sold', 'how many units', 'how many pieces']):
            metric_highlight = f"**{total_qty:,} units**"
            primary_text = f"A total of {metric_highlight} were ordered."
        elif any(w in q_lower for w in ['average price', 'average order value', 'aov', 'mean price', 'ticket size']):
            metric_highlight = f"**{format_currency(aov)}**"
            primary_text = f"The average order value (AOV) is {metric_highlight}."
        elif any(w in q_lower for w in ['maximum', 'highest price', 'most expensive', 'peak order']):
            metric_highlight = f"**{format_currency(max_amount)}**"
            primary_text = f"The highest transaction amount was {metric_highlight}."
        elif any(w in q_lower for w in ['minimum', 'lowest price', 'cheapest']):
            metric_highlight = f"**{format_currency(min_amount)}**"
            primary_text = f"The lowest (non-zero) transaction amount was {metric_highlight}."
        elif any(w in q_lower for w in ['cancellation rate', 'cancel percentage']):
            cancels = filtered_df[filtered_df['status'].str.lower().str.contains('cancel', na=False)]
            c_rate = (len(cancels) / len(filtered_df) * 100) if len(filtered_df) > 0 else 0.0
            metric_highlight = f"**{c_rate:.2f}%**"
            primary_text = f"The cancellation rate is {metric_highlight} ({len(cancels):,} of {len(filtered_df):,} orders)."
        else:
            primary_text = f"Total gross revenue is **{format_currency(total_revenue)}** across **{total_orders:,} orders**."

        filter_summary = f" (*Filtered by: {', '.join(applied_filters)}*)" if applied_filters else ""

        answer = (
            f"### 📊 Analysis Findings for: *\"{query}\"*\n\n"
            f"{primary_text}{filter_summary}\n\n"
            f"**Detailed Breakdown:**\n"
            f"- **Gross Revenue:** {format_currency(total_revenue)} ({pct_of_total_rev:.1f}% of total catalog)\n"
            f"- **Order Volume:** {total_orders:,} transactions ({pct_of_total_orders:.1f}% of total orders)\n"
            f"- **Total Quantity Sold:** {total_qty:,} items\n"
            f"- **Average Order Value (AOV):** {format_currency(aov)}\n"
        )

        data_table = [
            {"Metric": "Gross Revenue", "Value": format_currency(total_revenue)},
            {"Metric": "Total Orders", "Value": f"{total_orders:,}"},
            {"Metric": "Units Sold", "Value": f"{total_qty:,}"},
            {"Metric": "Average Order Value", "Value": format_currency(aov)}
        ]

        return {
            "answer": answer,
            "intent": "dynamic_query",
            "chart_url": None,
            "data_table": data_table,
            "suggestions": [
                "Which category generated the highest revenue?",
                "Show monthly sales trend",
                "What is our overall cancellation rate?"
            ],
            "execution_type": "dynamic_semantic_engine",
            "status": "success"
        }

    def _generate_grouped_response(self, query: str, df: pd.DataFrame, group_col: str, group_label: str, chart_title: str, applied_filters: List[str]) -> Dict[str, Any]:
        """Calculates grouping aggregations and produces a chart for ranking questions."""
        grouped = df.groupby(group_col).agg(
            revenue=('amount', 'sum'),
            orders=('order_id', 'nunique') if 'order_id' in df.columns else ('amount', 'count'),
            qty=('qty', 'sum') if 'qty' in df.columns else ('amount', 'count')
        ).reset_index().sort_values(by='revenue', ascending=False)

        top_df = grouped.head(8)
        if top_df.empty:
            return {"answer": "No data available to group.", "status": "error", "chart_url": None}

        # Generate Chart
        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        labels = [str(x)[:22] for x in top_df[group_col]]
        y_pos = np.arange(len(top_df))

        bars = ax.barh(y_pos, top_df['revenue'] / 100_000, color='#2563EB', edgecolor='#1E293B', height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlabel('Revenue (Lakh ₹)', fontsize=10, fontweight='bold')
        filter_str = f" ({', '.join(applied_filters)})" if applied_filters else ""
        ax.set_title(f"{chart_title}{filter_str}", fontsize=12, fontweight='bold', pad=12)

        for bar in bars:
            w = bar.get_width()
            ax.text(w + 0.1, bar.get_y() + bar.get_height()/2, f" ₹{w:,.1f}L", va='center', ha='left', fontsize=8.5, fontweight='bold', color='#1E293B')

        plt.tight_layout()
        chart_url = save_chart_image(fig, f"grouped_{group_col}")

        # Top item summary
        top_item = top_df.iloc[0]
        top_name = str(top_item[group_col]).title() if group_col in ['ship_city', 'ship_state'] else str(top_item[group_col])
        total_rev = top_df['revenue'].sum()
        top_share = (top_item['revenue'] / total_rev * 100) if total_rev > 0 else 0.0

        filter_text = f" with filters ({', '.join(applied_filters)})" if applied_filters else ""
        summary = (
            f"### 📊 {chart_title} Results\n\n"
            f"Analyzing *\"{query}\"*{filter_text}:\n\n"
            f"- **#1 Ranked {group_label}:** **{top_name}** leading with **{format_currency(top_item['revenue'])}** across **{int(top_item['orders']):,} orders** ({top_share:.1f}% of top group revenue).\n"
            f"- **Second Highest:** **{str(top_df.iloc[1][group_col]).title() if len(top_df) > 1 else 'N/A'}** with {format_currency(top_df.iloc[1]['revenue']) if len(top_df) > 1 else 'N/A'}.\n\n"
            f"See the generated ranking chart below:"
        )

        data_table = []
        for _, r in top_df.iterrows():
            name = str(r[group_col]).title() if group_col in ['ship_city', 'ship_state'] else str(r[group_col])
            data_table.append({
                group_label: name,
                "Revenue": format_currency(r['revenue']),
                "Orders": f"{int(r['orders']):,}",
                "Units": f"{int(r['qty']):,}"
            })

        return {
            "answer": summary,
            "intent": f"grouped_{group_col}",
            "chart_url": chart_url,
            "data_table": data_table,
            "suggestions": [
                f"Show monthly sales trend for {top_name}",
                "What is our cancellation rate?",
                "Which category generated the highest revenue?"
            ],
            "execution_type": "dynamic_semantic_engine",
            "status": "success"
        }

    def _try_llm_code_execution(
        self,
        user_query: str,
        df: pd.DataFrame,
        schema_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Synthesizes and executes Python/Pandas code via Gemini or OpenAI when an API key is provided."""
        schema_section = ""
        if schema_info:
            schema_section = f"\nDataset Schema / Columns info:\n{json.dumps(schema_info, indent=2)}\n"

        context_section = ""
        if context:
            context_section = f"\nDataset Context / Active Filters / Constraints:\n{json.dumps(context, indent=2)}\n"

        # 1. Try Gemini
        gemini_key = get_gemini_key()
        if gemini_key:
            try:
                import requests
                prompt = (
                    "You are an expert Autonomous Python Data Science Agent.\n"
                    f"We have a Pandas DataFrame called `df` representing an Amazon Sales Report.\n"
                    f"Columns: {list(df.columns)}\n"
                    f"{schema_section}"
                    f"{context_section}"
                    f"User Question: '{user_query}'\n\n"
                    "Write ONLY executable Python code (inside ```python ... ``` block) that calculates the answer and assigns the final readable string summary or dictionary to a variable named `result`.\n"
                    "Important columns in df: 'amount' (sales in INR, float), 'order_id' (order id), 'qty' (units, int), 'category', 'status', 'ship_city', 'ship_state', 'size', 'fulfilment', 'b2b' (bool), 'date' (datetime).\n"
                    "If dataset context/constraints are provided, ensure you apply them when filtering or calculating.\n"
                    "Do not invent columns. Always check lowercase when comparing strings, e.g. df['category'].str.lower() == 'kurta'.\n"
                    "Example:\n```python\ntotal = df[df['category'].str.lower() == 'kurta']['amount'].sum()\nresult = f'Total revenue for Kurta is ₹{total:,.2f}'\n```"
                )

                for model in ['gemini-flash-lite-latest', 'gemini-flash-latest', 'gemini-3.8-flash', 'gemini-pro-latest']:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    try:
                        resp = requests.post(url, json=payload, timeout=20)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates and "content" in candidates[0]:
                                parts = candidates[0]["content"].get("parts", [])
                                if parts and "text" in parts[0]:
                                    code_text = parts[0]["text"]
                                    result_payload = self._execute_sandbox_code(code_text, user_query, df, model)
                                    if result_payload:
                                        return result_payload
                        else:
                            logger.warning(f"Gemini model {model} returned status {resp.status_code}")
                    except Exception as model_err:
                        logger.warning(f"Error querying Gemini model {model}: {model_err}")

            except Exception as e:
                logger.warning(f"Gemini execution attempt failed: {e}")

        # 2. Try OpenAI
        openai_key = get_openai_key()
        if openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                prompt = (
                    f"You are an expert Autonomous Python Data Science Agent.\n"
                    f"We have a Pandas DataFrame called `df` representing an Amazon Sales Report.\n"
                    f"Columns: {list(df.columns)}\n"
                    f"{schema_section}"
                    f"{context_section}"
                    f"User Question: '{user_query}'\n\n"
                    f"Write ONLY executable Python code (inside ```python ... ``` block) that computes the answer and assigns the final readable string summary or dictionary to a variable named `result`.\n"
                    "If dataset context/constraints are provided, ensure you apply them when filtering or calculating.\n"
                )
                model_to_use = os.getenv("MODEL_NAME", "gpt-4o-mini")
                res = client.chat.completions.create(
                    model=model_to_use,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                code_text = res.choices[0].message.content
                return self._execute_sandbox_code(code_text, user_query, df, model_to_use)
            except Exception as e:
                logger.warning(f"OpenAI execution attempt failed: {e}")

        return None

    def _execute_sandbox_code(self, code_text: str, user_query: str, df: pd.DataFrame, model_used: str) -> Optional[Dict[str, Any]]:
        """Executes LLM-generated Python code in a safe sandbox."""
        # Extract code between ```python and ```
        match = re.search(r'```python\s*(.*?)\s*```', code_text, re.DOTALL)
        code_to_run = match.group(1) if match else code_text

        local_vars = {"df": df, "pd": pd, "np": np, "format_currency": format_currency}
        try:
            exec(code_to_run, {}, local_vars)
            output_val = local_vars.get("result")
            if output_val is not None:
                data_table = []
                if isinstance(output_val, pd.DataFrame):
                    data_table = output_val.head(25).to_dict(orient="records")
                    output_text = output_val.head(25).to_markdown(index=False)
                elif isinstance(output_val, pd.Series):
                    df_series = output_val.reset_index()
                    data_table = df_series.head(25).to_dict(orient="records")
                    output_text = df_series.head(25).to_markdown(index=False)
                elif isinstance(output_val, dict):
                    output_lines = []
                    for k, v in output_val.items():
                        title_k = str(k).replace('_', ' ').title()
                        if isinstance(v, list):
                            items_preview = ", ".join(map(str, v[:25]))
                            suffix = f" ... *(and {len(v) - 25} more)*" if len(v) > 25 else ""
                            output_lines.append(f"- **{title_k} ({len(v)} total):** {items_preview}{suffix}")
                        else:
                            output_lines.append(f"- **{title_k}:** {v}")
                    output_text = "\n".join(output_lines)
                elif isinstance(output_val, (list, tuple, set)):
                    items_list = list(output_val)
                    output_lines = [f"- {item}" for item in items_list[:30]]
                    if len(items_list) > 30:
                        output_lines.append(f"\n*(and {len(items_list) - 30} more items)*")
                    output_text = "\n".join(output_lines)
                else:
                    output_text = str(output_val)

                answer = (
                    f"### 🤖 AI Data Science Findings\n\n"
                    f"**Analysis for:** *\"{user_query}\"*\n\n"
                    f"{output_text}"
                )
                return {
                    "answer": answer,
                    "intent": "llm_code_execution",
                    "chart_url": None,
                    "data_table": data_table,
                    "suggestions": ["Show monthly sales trend", "What is our cancellation rate?"],
                    "execution_type": f"llm_synthesized ({model_used})",
                    "status": "success"
                }
        except Exception as err:
            logger.warning(f"Sandbox execution error: {err}")
            return None


orchestrater = OrchestraterAgent()
