"""
backend/app.py
Flask Web Application & REST API Server for Autonomous Amazon Sales Analysis.
Serves the web dashboard, Q&A chat interface, dataset upload endpoints, and visualization charts.
"""

import os
import sys
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Ensure root directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from helper import load_dataset, get_available_datasets, save_uploaded_file, format_currency
from backend.models import dataset_store, conversation_manager, ChatMessage
from backend.schema import QueryRequest, ChatRequest
from backend.orchestrater import orchestrater
import backend.function as fn
from text import SAMPLE_QUESTIONS

load_dotenv(os.path.join(ROOT_DIR, ".env"))
logger = logging.getLogger(__name__)

# Template and static paths
TEMPLATE_DIR = os.path.join(ROOT_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "frontend")
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")
DATASET_IMG_DIR = os.path.join(ROOT_DIR, "dataset", "images")

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)
app.config['MAX_CONTENT_LENGTH'] = 250 * 1024 * 1024  # 250 MB max file upload
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True


# Initialize default dataset on startup
def init_dataset():
    csv_path = os.getenv("DATASET_CSV_PATH", os.path.join(ROOT_DIR, "dataset", "csv", "amazon_sales_report.csv"))
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(ROOT_DIR, csv_path)
    df = load_dataset(csv_path)
    dataset_store.set_data(df, csv_path)
    logger.info(f"Initialized DatasetStore with {len(df):,} records.")

init_dataset()


@app.route('/')
def index():
    """Serves the main interactive dashboard and chat analyst UI."""
    return render_template('index.html', sample_questions=SAMPLE_QUESTIONS)


@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    """Returns top-level KPI metrics."""
    df = dataset_store.get_data()
    kpis = fn.calculate_kpis(df)
    return jsonify({"status": "success", "kpis": kpis, "records": len(df)})


@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """Autonomous Chat Analyst endpoint.
    Accepts user query/message along with optional dataset schema and context constraints.
    Payload: { query, schema, context, conversation_id }
    """
    raw_data = request.get_json(silent=True) or {}

    # Validate with Pydantic ChatRequest
    try:
        chat_req = ChatRequest(**raw_data)
    except Exception as e:
        logger.warning(f"ChatRequest validation fallback due to: {e}")
        chat_req = ChatRequest(
            query=raw_data.get("query"),
            message=raw_data.get("message"),
            schema_info=raw_data.get("schema") or raw_data.get("schema_info"),
            context=raw_data.get("context"),
            conversation_id=raw_data.get("conversation_id", "default_session")
        )

    query_text = (chat_req.query or chat_req.message or "").strip()
    session_id = chat_req.conversation_id or "default_session"
    schema_info = chat_req.schema_info
    context = chat_req.context

    if not query_text:
        return jsonify({
            "status": "error",
            "message": "Please provide a 'query' or 'message' in your request."
        }), 400

    # Record user message in conversation history
    conversation_manager.add_message(session_id, ChatMessage(sender="user", text=query_text))

    # Autonomous Orchestration with query, schema, and context
    result = orchestrater.plan_and_execute(
        query=query_text,
        schema_info=schema_info,
        context=context
    )

    # Record agent response in conversation history
    agent_msg = ChatMessage(
        sender="analyst",
        text=result.get("answer", ""),
        intent=result.get("intent", ""),
        chart_url=result.get("chart_url"),
        data_table=result.get("data_table"),
        suggestions=result.get("suggestions")
    )
    conversation_manager.add_message(session_id, agent_msg)

    return jsonify(result)


@app.route('/api/query', methods=['POST'])
def query_agent():
    """Natural Language English Q&A query endpoint (backwards-compatible with /api/chat)."""
    data = request.get_json(silent=True) or {}
    query_text = (data.get("query") or data.get("message") or "").strip()
    schema_info = data.get("schema") or data.get("schema_info")
    context = data.get("context")
    session_id = data.get("conversation_id", "default_session")

    if not query_text:
        return jsonify({"status": "error", "message": "Please provide a query."}), 400

    # Record user message
    conversation_manager.add_message(session_id, ChatMessage(sender="user", text=query_text))

    # Autonomous Orchestration
    result = orchestrater.plan_and_execute(
        query=query_text,
        schema_info=schema_info,
        context=context
    )

    # Record agent response
    agent_msg = ChatMessage(
        sender="analyst",
        text=result.get("answer", ""),
        intent=result.get("intent", ""),
        chart_url=result.get("chart_url"),
        data_table=result.get("data_table"),
        suggestions=result.get("suggestions")
    )
    conversation_manager.add_message(session_id, agent_msg)

    return jsonify(result)


@app.route('/api/upload', methods=['POST'])
def upload_dataset():
    """Handles uploading CSV, JSON, or Image datasets."""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Empty filename."}), 400

    filename = secure_filename(file.filename)
    success, message, saved_path = save_uploaded_file(file, filename)

    if not success:
        return jsonify({"success": False, "message": message}), 400

    ext = os.path.splitext(filename)[1].lower()
    records_count = None
    cols = []

    # If CSV or JSON, reload dataset store with new file
    if ext in ['.csv', '.json']:
        new_df = load_dataset(saved_path)
        dataset_store.set_data(new_df, saved_path)
        records_count = len(new_df)
        cols = list(new_df.columns)
        message += f" - Loaded {records_count:,} records into memory!"

    return jsonify({
        "success": True,
        "message": message,
        "filename": filename,
        "file_type": ext.replace('.', '').upper(),
        "records_count": records_count,
        "columns": cols
    })


@app.route('/api/datasets', methods=['GET'])
def list_datasets():
    """Lists available files in the dataset folder."""
    files = get_available_datasets()
    active_path = dataset_store.active_file_path or ""
    active_filename = os.path.basename(active_path) if active_path else "None"
    return jsonify({
        "status": "success",
        "active_dataset": active_filename,
        "files": files,
        "metadata": dataset_store.metadata
    })


@app.route('/api/switch-dataset', methods=['POST'])
def switch_dataset():
    """Switches active dataset to another available file."""
    data = request.get_json() or {}
    filepath = data.get("filepath", "").strip()

    if not filepath or not os.path.exists(filepath):
        return jsonify({"success": False, "message": "File not found."}), 404

    new_df = load_dataset(filepath)
    dataset_store.set_data(new_df, filepath)
    return jsonify({
        "success": True,
        "message": f"Switched dataset to {os.path.basename(filepath)} ({len(new_df):,} records).",
        "records": len(new_df)
    })


@app.route('/api/summary', methods=['GET'])
def generate_summary_report():
    """Generates an autonomous comprehensive executive summary."""
    df = dataset_store.get_data()
    if df.empty:
        return jsonify({"status": "error", "message": "No dataset loaded."}), 400

    kpis = fn.calculate_kpis(df)
    cat_res = fn.analyze_category_performance(df, top_n=5)
    trend_res = fn.analyze_sales_trend(df)
    cancel_res = fn.analyze_cancellations(df)

    report_markdown = (
        f"# 📈 Autonomous Amazon Sales Performance Report\n\n"
        f"### 1. Key Performance Indicators\n"
        f"- **Total Gross Revenue:** {kpis['formatted_revenue']}\n"
        f"- **Total Order Volume:** {kpis['total_orders']:,} orders\n"
        f"- **Units Sold:** {kpis['total_qty']:,} units\n"
        f"- **Average Order Value (AOV):** {kpis['formatted_aov']}\n"
        f"- **Order Cancellation Rate:** {kpis['cancellation_rate']}%\n"
        f"- **Top Contributing Category:** {kpis['top_category']}\n\n"
        f"### 2. Category Revenue Concentration\n"
        f"{cat_res['summary']}\n\n"
        f"### 3. Sales Trajectory & Seasonality\n"
        f"{trend_res['summary']}\n\n"
        f"### 4. Operational Risk & Cancellations\n"
        f"{cancel_res['summary']}\n"
    )

    return jsonify({
        "status": "success",
        "report_markdown": report_markdown,
        "kpis": kpis,
        "charts": [cat_res.get("chart_url"), trend_res.get("chart_url"), cancel_res.get("chart_url")]
    })


@app.route('/outputs/<path:filename>')
def serve_output_file(filename):
    """Serves generated chart PNGs from outputs/."""
    return send_from_directory(OUTPUT_DIR, filename)


@app.route('/dataset/images/<path:filename>')
def serve_dataset_image(filename):
    """Serves images from dataset/images/."""
    return send_from_directory(DATASET_IMG_DIR, filename)


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    logger.info(f"Starting Autonomous Amazon Sales Analyst server on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
