/**
 * frontend/read_node.js
 * Node.js Dataset Reader and Frontend Static Server utility.
 * Reads CSV, JSON, and Image dataset nodes from disk, inspects schemas,
 * and prints detailed node summaries.
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

// Paths
const BASE_DIR = path.resolve(__dirname, '..');
const DATASET_DIR = path.join(BASE_DIR, 'dataset');
const CSV_DIR = path.join(DATASET_DIR, 'csv');
const JSON_DIR = path.join(DATASET_DIR, 'json');
const IMG_DIR = path.join(DATASET_DIR, 'images');

/**
 * Reads dataset nodes from disk and prints structured inspection
 */
function readDatasetNodes() {
  console.log('====================================================');
  console.log('🚀 [Node.js Dataset Reader] Inspecting Dataset Nodes');
  console.log('====================================================\n');

  // 1. Read JSON Nodes
  if (fs.existsSync(JSON_DIR)) {
    const jsonFiles = fs.readdirSync(JSON_DIR).filter(f => f.endsWith('.json'));
    console.log(`📁 Found ${jsonFiles.length} JSON node file(s):`);

    jsonFiles.forEach(file => {
      const fullPath = path.join(JSON_DIR, file);
      const stat = fs.statSync(fullPath);
      try {
        const rawContent = fs.readFileSync(fullPath, 'utf8');
        const parsed = JSON.parse(rawContent);
        const nodeCount = Array.isArray(parsed) ? parsed.length : Object.keys(parsed).length;
        console.log(`  📄 [JSON] ${file} | Size: ${(stat.size / 1024).toFixed(1)} KB | Nodes/Records: ${nodeCount}`);
        
        if (Array.isArray(parsed) && parsed.length > 0) {
          const sampleKeys = Object.keys(parsed[0]).slice(0, 6).join(', ');
          console.log(`     Sample Attributes: [${sampleKeys}...]`);
        }
      } catch (err) {
        console.error(`     ❌ Error parsing ${file}:`, err.message);
      }
    });
  }

  // 2. Read CSV Nodes
  if (fs.existsSync(CSV_DIR)) {
    const csvFiles = fs.readdirSync(CSV_DIR).filter(f => f.endsWith('.csv'));
    console.log(`\n📁 Found ${csvFiles.length} CSV node file(s):`);

    csvFiles.forEach(file => {
      const fullPath = path.join(CSV_DIR, file);
      const stat = fs.statSync(fullPath);
      console.log(`  📊 [CSV] ${file} | Size: ${(stat.size / (1024 * 1024)).toFixed(2)} MB`);
      
      // Read first 2 lines to extract headers
      const fd = fs.openSync(fullPath, 'r');
      const buffer = Buffer.alloc(1024);
      fs.readSync(fd, buffer, 0, 1024, 0);
      fs.closeSync(fd);
      
      const snippet = buffer.toString('utf8');
      const headerLine = snippet.split('\n')[0];
      if (headerLine) {
        console.log(`     Headers: ${headerLine.substring(0, 90)}...`);
      }
    });
  }

  // 3. Read Image Nodes
  if (fs.existsSync(IMG_DIR)) {
    const imgFiles = fs.readdirSync(IMG_DIR).filter(f => /\.(png|jpg|jpeg|svg|webp)$/i.test(f));
    console.log(`\n📁 Found ${imgFiles.length} Image node file(s):`);
    imgFiles.forEach(file => {
      const fullPath = path.join(IMG_DIR, file);
      const stat = fs.statSync(fullPath);
      console.log(`  🖼️ [IMAGE] ${file} | Size: ${(stat.size / 1024).toFixed(1)} KB`);
    });
  }

  console.log('\n✅ [Node.js Dataset Reader] Finished reading all nodes successfully.\n');
}

/**
 * Optional Node.js HTTP Server to serve static frontend
 */
function startNodeServer(port = 3000) {
  const FRONTEND_DIR = __dirname;
  const MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.json': 'application/json'
  };

  const server = http.createServer((req, res) => {
    let reqUrl = req.url.split('?')[0];
    if (reqUrl === '/') reqUrl = '/templates/index.html';

    let filePath = path.join(FRONTEND_DIR, reqUrl);
    // Support static paths
    if (reqUrl.startsWith('/static/')) {
      filePath = path.join(FRONTEND_DIR, reqUrl.replace('/static/', ''));
    }

    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found - To use backend API, run: python main.py');
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Error loading file');
        return;
      }
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(data);
    });
  });

  server.listen(port, () => {
    console.log(`🌐 Optional Node static server running at http://localhost:${port}`);
    console.log(`👉 Note: The full autonomous API and analysis engine runs via Python: python main.py`);
  });
}

// Execute reader immediately
readDatasetNodes();

// If --serve flag passed, start Node static server
if (process.argv.includes('--serve')) {
  startNodeServer();
}
