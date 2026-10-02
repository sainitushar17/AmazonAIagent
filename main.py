"""
main.py
Central Entry Point for the Autonomous Amazon Sales Data Analyst System.
Supports Web Server mode, Interactive CLI mode, and Automated Report Generation.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Ensure safe UTF-8 output on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure local directories are in python search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from helper import load_dataset, get_available_datasets, format_currency
from backend.models import dataset_store
from backend.orchestrater import orchestrater
import backend.function as fn

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")


def print_banner():
    banner = r"""

    """
    print(banner)                   


def run_cli_mode():
    """Runs interactive conversational terminal analyst."""
    print_banner()
    print("🚀 Initializing Autonomous Sales Analyst in Terminal Mode...\n")

    # Load dataset
    df = dataset_store.get_data()
    if df.empty:
        csv_path = os.getenv("DATASET_CSV_PATH", "dataset/csv/amazon_sales_report.csv")
        df = load_dataset(csv_path)
        dataset_store.set_data(df, csv_path)

    kpis = fn.calculate_kpis(df)
    print(f"📊 Dataset Loaded: {len(df):,} total records")
    print(f"💰 Gross Revenue: {kpis['formatted_revenue']} | Orders: {kpis['total_orders']:,} | AOV: {kpis['formatted_aov']}")
    print(f"⚠️ Cancellation Rate: {kpis['cancellation_rate']}% | Top Category: {kpis['top_category']}\n")

    print("Type your questions in simple English (or type 'exit' to quit).")
    print("Example questions:")
    print(" - 'Which are the top 5 best selling categories by revenue?'")
    print(" - 'Show me monthly sales trend'")
    print(" - 'What is our order cancellation rate and lost revenue?'")
    print(" - 'Compare Amazon fulfillment vs Merchant'\n" + "-"*72)

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye! Happy selling on Amazon.")
                break

            print("\n🤖 Analyst: Processing dataset figures...\n")
            result = orchestrater.plan_and_execute(user_input)

            # Print narrative
            print(result.get("answer", ""))

            # Mention chart if generated
            if result.get("chart_url"):
                print(f"\n📊 Visualization generated and saved: {result.get('chart_url')}")

            # Print follow-up suggestions
            suggestions = result.get("suggestions", [])
            if suggestions:
                print("\n💡 Suggested Follow-ups:")
                for idx, s in enumerate(suggestions[:3], 1):
                    print(f"   {idx}. {s}")

            print("\n" + "-"*72)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting CLI mode.")
            break


def run_report_mode():
    """Generates an executive standalone markdown analysis and saves charts."""
    print_banner()
    print("📊 Generating Autonomous Amazon Sales Report...\n")

    csv_path = os.getenv("DATASET_CSV_PATH", "dataset/csv/amazon_sales_report.csv")
    df = load_dataset(csv_path)
    dataset_store.set_data(df, csv_path)

    kpis = fn.calculate_kpis(df)
    cat_res = fn.analyze_category_performance(df)
    trend_res = fn.analyze_sales_trend(df)
    cancel_res = fn.analyze_cancellations(df)
    ful_res = fn.analyze_fulfillment_methods(df)
    geo_res = fn.analyze_geographic_distribution(df)

    output_file = os.path.join(CURRENT_DIR, "outputs", "executive_sales_report.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 📈 Autonomous Amazon Sales Performance Report\n\n")
        f.write(f"- **Gross Revenue:** {kpis['formatted_revenue']}\n")
        f.write(f"- **Total Orders:** {kpis['total_orders']:,}\n")
        f.write(f"- **Average Order Value:** {kpis['formatted_aov']}\n")
        f.write(f"- **Cancellation Rate:** {kpis['cancellation_rate']}%\n\n")
        f.write("## 1. Category Revenue Performance\n")
        f.write(cat_res['summary'] + "\n\n")
        f.write("## 2. Sales Trend & Growth\n")
        f.write(trend_res['summary'] + "\n\n")
        f.write("## 3. Order Cancellations & Operational Risks\n")
        f.write(cancel_res['summary'] + "\n\n")
        f.write("## 4. Fulfillment Channel Breakdown\n")
        f.write(ful_res['summary'] + "\n\n")
        f.write("## 5. Geographical Distribution\n")
        f.write(geo_res['summary'] + "\n\n")

    print(f"✅ Full report generated successfully at: {output_file}")


def run_web_server():
    """Starts the Flask web application."""
    print_banner()
    from backend.app import app
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")

    print(f"🌐 Autonomous Analyst Web Server starting on: http://{host}:{port}")
    print(f"📊 Access the interactive dashboard, chat analyst, and file uploader in your browser!")
    print(f"Press CTRL+C to stop the server.\n")

    app.run(host=host, port=port, debug=False)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Amazon Sales Data Analyst")
    parser.add_argument("--cli", action="store_true", help="Run interactive terminal CLI analyst")
    parser.add_argument("--report", action="store_true", help="Generate one-shot standalone executive report")
    parser.add_argument("--serve", action="store_true", help="Run web application server (default)")
    parser.add_argument("--port", type=int, default=5000, help="Web server port (default: 5000)")

    args = parser.parse_args()

    if args.cli:
        run_cli_mode()
    elif args.report:
        run_report_mode()
    else:
        run_web_server()


if __name__ == "__main__":
    main()
