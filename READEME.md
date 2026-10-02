# 📊 Autonomous E-Commerce Amazon Sales Data Analyst

An intelligent **Autonomous Data Analysis System** built in Python and modern Web technologies for the **E-Commerce Amazon Sales Report**. It answers any question asked in **simple English language**, computes key business metrics, generates visual charts on demand, and supports uploading datasets across **CSV**, **JSON**, and **Image folders**.

---

## 🌟 Key Features

1. **Natural Language Q&A in Simple English**:
   - Ask complex business questions without writing code or SQL:
     - *"What is our total revenue and how many orders were placed?"*
     - *"Which are the top 5 best-selling categories by revenue?"*
     - *"Show me monthly sales trend"*
     - *"What is the cancellation rate and how much revenue was lost?"*
     - *"Compare Amazon fulfillment vs Merchant fulfillment performance"*
     - *"Which states and cities generate the highest sales volume?"*
     - *"What are the most popular product sizes?"*
     - *"What percentage of orders are B2B vs retail B2C?"*
2. **Autonomous Analysis & Visualization**:
   - Automatically computes KPIs (Gross Revenue, Total Orders, Average Order Value, Cancellation Rate, Top Categories, Top Cities).
   - Dynamically generates Seaborn/Matplotlib charts and serves them directly into the conversation.
3. **Multi-Format Dataset Ingestion**:
   - Upload new datasets in **CSV** (transaction logs), **JSON** (structured orders/catalogs), or **Images** (catalog photos, promotional visuals).
4. **Offline + Hybrid LLM Architecture**:
   - Works **100% offline out-of-the-box** using an autonomous statistical intent and aggregation engine (no paid API key required).
   - Supports optional LLM keys (OpenAI GPT-4o / Google Gemini) in `.env` for elevated conversational summaries.
5. **Interactive Web Dashboard & CLI**:
   - Responsive web dashboard with live chat, KPI cards, quick-question buttons, and drag-and-drop file upload.
   - Interactive terminal CLI mode (`python main.py --cli`) to query directly in the VS Code terminal.

---

## 🗂️ Project Directory Structure

```text
amazon_sales_autonomous_analyst/
│
├── .env                     # Configuration (ports, paths, optional LLM keys)
├── helper.py                # Dataset loaders, cleaning, currency formatting, file upload handlers
├── main.py                  # Main entry point (Web server, interactive CLI, report generator)
├── README.md                # Project documentation and guide
├── READEME.md               # User alias documentation
├── requirements.txt         # Python dependencies
├── text.py                  # Natural language templates, system prompts, sample questions
│
├── dataset/                 # Dataset folder supporting CSV, JSON, and Images
│   ├── csv/                 # Amazon Sales Report CSV files
│   │   └── amazon_sales_report.csv
│   ├── json/                # JSON structured catalogs & orders
│   │   └── amazon_sales_sample.json
│   └── images/              # Catalog and diagram images
│       └── sample_product.png
│
├── frontend/                # Frontend User Interface & Node integration
│   ├── templates/           # HTML templates (Jinja2)
│   │   └── index.html       # Full responsive dashboard & chat UI
│   ├── src/                 # Stylesheet source
│   │   └── style.css        # Modern Amazon-themed CSS styles
│   ├── js/                  # JavaScript frontend logic
│   │   └── app.js           # Chat dispatch, chart rendering, dropzone uploads
│   ├── read_node.js         # Node.js dataset reader & optional static server
│   └── package.json         # Node.js scripts for running read_node
│
├── backend/                 # Backend analytical core & REST API
│   ├── models.py            # In-memory dataset store, session history, chat models
│   ├── schema.py            # Pydantic validation schemas (requests, responses, KPIs)
│   ├── app.py               # Flask RESTful API endpoints & static serving
│   ├── function.py          # Domain-specific analytical & chart functions
│   └── orchestrater.py      # Autonomous agent orchestrator & intent planner
│
└── outputs/                 # Generated chart PNGs and executive reports
```

---

## 🚀 Getting Started in VS Code

### Step 1: Open the Project in VS Code
1. Open **VS Code**.
2. Go to **File** ➡️ **Open Folder...**
3. Select this project directory:
   `C:\Users\256262\.gemini\antigravity\scratch\amazon_sales_autonomous_analyst`
4. Set this folder as your active workspace.

### Step 2: Install Dependencies
Open the VS Code Terminal (`Ctrl + ~`) and run:
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Autonomous Data Analyst

#### Option A: Web Application (Recommended)
Run the web application:
```powershell
python main.py
```
Then open your browser at **http://127.0.0.1:5000**.
- You will see the **executive KPI dashboard** at the top.
- Chat with the analyst in the **Chat Interface** on the left.
- Click any **Quick Insights** on the right sidebar.
- Click **Upload Data** to upload any new CSV, JSON, or Image.

#### Option B: Interactive Terminal CLI
To chat directly with the analyst inside your terminal:
```powershell
python main.py --cli
```

#### Option C: One-Shot Autonomous Report
To generate a comprehensive markdown report with charts saved to `outputs/`:
```powershell
python main.py --report
```

---

## ⚡ Using the Node.js Dataset Reader (`read_node.js`)

If you want to use Node.js to inspect dataset nodes (CSV, JSON, images):
1. In the VS Code terminal:
```powershell
cd frontend
node read_node.js
```
Or run the optional Node static server:
```powershell
node read_node.js --serve
```

---

## 💬 Sample Questions to Ask in Simple English

| Question Category | Example English Query |
| :--- | :--- |
| **High-Level KPIs** | *"What is our total revenue and how many orders were placed?"* |
| **Top Categories** | *"Which are the top 5 best selling categories by revenue?"* |
| **Sales Trend** | *"Show me monthly sales and order volume trend."* |
| **Cancellations** | *"What is our order cancellation rate and how much revenue was lost?"* |
| **Fulfillment** | *"Compare Amazon fulfillment vs Merchant fulfillment performance."* |
| **Geography** | *"Which states and cities generate the highest sales volume?"* |
| **Sizing** | *"What are the most popular product sizes in our catalog?"* |
| **B2B vs B2C** | *"What percentage of our orders come from B2B buyers compared to B2C?"* |
| **Product SKUs** | *"What are the top 10 best-selling SKUs by quantity sold?"* |
| **Specific Filter** | *"How much revenue was generated in Mumbai?"* or *"Sales for Kurta"* |

---

## ⚙️ Configuration (`.env`)

Configure port or add optional LLM API keys:
```env
PORT=5000
HOST=127.0.0.1
DATASET_CSV_PATH=dataset/csv/amazon_sales_report.csv
DATASET_JSON_PATH=dataset/json/amazon_sales_sample.json
DATASET_IMAGES_PATH=dataset/images
OUTPUT_DIR=outputs

# Optional LLM API Key (Works offline if left blank)
OPENAI_API_KEY=
GEMINI_API_KEY=
```

---

## 🛡️ License
MIT License. Created for Autonomous E-Commerce Data Analytics.
