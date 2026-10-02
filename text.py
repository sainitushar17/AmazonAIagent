"""
text.py
Prompts, Natural Language Templates, and Sample Questions for the Autonomous
Amazon E-commerce Data Analyst Agent.
"""

SYSTEM_PROMPT = """You are an Autonomous Senior E-commerce Data Analyst specializing in Amazon Sales Reports.
Your mission is to analyze complex sales datasets and explain all metrics, trends, patterns, and anomalies in simple, clear, professional English.

Key Guidelines:
1. Always translate numbers into meaningful business context (e.g. explain what a cancellation rate of 15% means for logistics and cash flow).
2. Use clear formatting with bullet points, bold key figures, and actionable business recommendations.
3. Keep the tone friendly, authoritative, and accessible to non-technical stakeholders.
4. When relevant, reference visual charts that illustrate the key trends.
"""

KPI_DESCRIPTIONS = {
    "total_revenue": "Total gross revenue generated across all completed and shipped transactions.",
    "total_orders": "The cumulative number of unique orders placed during the recorded period.",
    "average_order_value": "The average gross transaction value per order (Total Revenue / Total Orders).",
    "cancellation_rate": "The percentage of total orders that were cancelled prior to or during fulfillment.",
    "top_category": "The product category generating the highest portion of total revenue.",
    "top_city": "The geographical city with the highest volume of successful deliveries."
}

SAMPLE_QUESTIONS = [
    {
        "category": "High-Level Performance",
        "question": "What is our total revenue and how many orders were placed?",
        "intent": "kpi_summary"
    },
    {
        "category": "Category & Products",
        "question": "Which are the top 5 best selling categories by revenue?",
        "intent": "category_analysis"
    },
    {
        "category": "Sales Trend",
        "question": "Show me the monthly sales and order volume trend.",
        "intent": "trend_analysis"
    },
    {
        "category": "Cancellations & Risk",
        "question": "What is the order cancellation rate and how much revenue was lost?",
        "intent": "cancellation_analysis"
    },
    {
        "category": "Fulfillment & Operations",
        "question": "Compare Amazon fulfillment vs Merchant fulfillment performance.",
        "intent": "fulfillment_analysis"
    },
    {
        "category": "Geographical Insights",
        "question": "Which states and cities generate the highest sales volume?",
        "intent": "geographical_analysis"
    },
    {
        "category": "Product Sizing",
        "question": "What are the most popular product sizes in our catalog?",
        "intent": "size_distribution"
    },
    {
        "category": "B2B vs B2C",
        "question": "What percentage of our orders come from B2B buyers compared to B2C?",
        "intent": "b2b_analysis"
    },
    {
        "category": "SKU Performance",
        "question": "What are the top 10 best-selling SKUs by quantity sold?",
        "intent": "top_skus"
    },
    {
        "category": "Delivery & Courier Status",
        "question": "What is the breakdown of order statuses and courier deliveries?",
        "intent": "status_distribution"
    }
]

EXPLAIN_TEMPLATES = {
    "greeting": (
        "Hello! I am your **Autonomous Amazon Sales Data Analyst**.\n\n"
        "I have loaded the e-commerce sales dataset. You can ask me any question in simple English, "
        "or upload new CSV, JSON, or images. How can I help you optimize your sales today?"
    ),
    "kpi_summary": (
        "### 📊 Overall Business Performance Summary\n\n"
        "- **Total Revenue:** {total_revenue}\n"
        "- **Total Order Volume:** {total_orders:,} orders\n"
        "- **Average Order Value (AOV):** {aov}\n"
        "- **Cancellation Rate:** {cancellation_rate:.2f}%\n"
        "- **Top Performing Category:** {top_category}\n"
        "- **Top Destination City:** {top_city}\n\n"
        "**Key Insight:** {insight}"
    ),
    "category_insight": (
        "### 👗 Category Revenue & Demand Breakdown\n\n"
        "Our catalog performance shows strong concentration in key product lines:\n\n"
        "{breakdown_table}\n\n"
        "**Strategic Takeaway:** The category **{top_category}** drives the lion's share of sales ({top_share:.1f}%). "
        "Ensuring stock availability and targeted promotions for this category will maximize your revenue returns."
    ),
    "trend_insight": (
        "### 📈 Monthly Revenue & Order Trajectory\n\n"
        "{trend_text}\n\n"
        "**Business Observation:** Sales activity demonstrates peak demand during {peak_period}. "
        "Inventory planning should be scaled 3-4 weeks ahead of this window to avoid stockouts."
    ),
    "cancellation_insight": (
        "### ⚠️ Order Cancellation & Loss Analysis\n\n"
        "- **Total Cancelled Orders:** {cancelled_count:,} ({cancellation_rate:.2f}% of all orders)\n"
        "- **Estimated Revenue Impact:** ~{lost_revenue}\n\n"
        "**Actionable Advice:** Most cancellations occur before courier pickup. "
        "Streamlining order confirmation times and verifying customer addresses can significantly reduce this attrition."
    ),
    "fallback_pandas": (
        "### 🔍 Analysis Result for: *\"{query}\"*\n\n"
        "{summary_text}\n\n"
        "{data_preview}"
    )
}
