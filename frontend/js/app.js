/**
 * frontend/js/app.js
 * Client-side controller for Autonomous Amazon Sales Data Analyst
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const queryInput = document.getElementById("queryInput");
  const sendBtn = document.getElementById("sendBtn");
  const uploadModal = document.getElementById("uploadModal");
  const openUploadBtn = document.getElementById("openUploadBtn");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const fileDropzone = document.getElementById("fileDropzone");
  const fileInput = document.getElementById("fileInput");
  const uploadStatus = document.getElementById("uploadStatus");
  const activeDatasetName = document.getElementById("activeDatasetName");

  // KPI Value Elements
  const kpiRevenue = document.getElementById("kpiRevenue");
  const kpiOrders = document.getElementById("kpiOrders");
  const kpiAOV = document.getElementById("kpiAOV");
  const kpiCancellation = document.getElementById("kpiCancellation");
  const kpiCategory = document.getElementById("kpiCategory");
  const kpiCity = document.getElementById("kpiCity");

  // Load Initial KPIs and active datasets
  fetchKPIs();
  fetchDatasetsInfo();

  // Handle Chat Form Submit
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    submitUserQuery(query);
  });

  // Handle Suggestion Button Clicks in Top-Right
  const suggestionsContainer = document.getElementById("suggestionsContainer");
  if (suggestionsContainer) {
    suggestionsContainer.addEventListener("click", (e) => {
      const btn = e.target.closest(".suggestion-btn");
      if (!btn) return;
      const q = btn.getAttribute("data-query");
      if (q) {
        queryInput.value = q;
        submitUserQuery(q);
      }
    });
  }

  // Handle Modal Open/Close
  if (openUploadBtn) {
    openUploadBtn.addEventListener("click", () => {
      uploadModal.style.display = "flex";
      uploadStatus.style.display = "none";
    });
  }

  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
      uploadModal.style.display = "none";
    });
  }

  window.addEventListener("click", (e) => {
    if (e.target === uploadModal) {
      uploadModal.style.display = "none";
    }
  });

  // Handle Drag & Drop Upload
  if (fileDropzone) {
    fileDropzone.addEventListener("click", () => fileInput.click());

    fileDropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      fileDropzone.classList.add("dragover");
    });

    fileDropzone.addEventListener("dragleave", () => {
      fileDropzone.classList.remove("dragover");
    });

    fileDropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      fileDropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
      }
    });
  }

  /**
   * Submits a user question to the Autonomous Analyst API
   */
  async function submitUserQuery(text) {
    // Append user message
    appendMessage("user", text);
    queryInput.value = "";
    queryInput.focus();

    // Append loading spinner message
    const loadingId = "loader_" + Date.now();
    appendLoading(loadingId);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });

      const data = await response.json();
      removeLoading(loadingId);

      if (response.ok && data.status === "success") {
        appendMessage("analyst", data.answer, data.chart_url, data.data_table, data.suggestions);
        if (data.suggestions && data.suggestions.length > 0) {
          updateTopRightSuggestions(data.suggestions);
        }
      } else {
        appendMessage(
          "analyst",
          data.message || data.answer || "⚠️ An error occurred while processing your request.",
          null,
          null,
          ["What is our total revenue?", "Which are the top 5 best selling categories?"]
        );
      }
    } catch (err) {
      removeLoading(loadingId);
      appendMessage("analyst", "⚠️ Network error connecting to backend analyst server: " + err.message);
    }
  }

  /**
   * Appends a message bubble into the chat feed
   */
  function appendMessage(sender, markdownText, chartUrl = null, dataTable = null, suggestions = []) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    // Format basic Markdown headers, bold, bullets
    let formattedHtml = markdownText
      .replace(/### (.*?)\n/g, "<h3>$1</h3>")
      .replace(/## (.*?)\n/g, "<h2>$1</h2>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\n- (.*?)(?=\n|$)/g, "<li>$1</li>")
      .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
      .replace(/\n\n/g, "<br><br>");

    bubble.innerHTML = formattedHtml;

    // Attach Chart if available
    if (chartUrl) {
      const chartContainer = document.createElement("div");
      chartContainer.className = "chart-container";
      chartContainer.innerHTML = `
        <a href="${chartUrl}" target="_blank" title="Click to view full size">
          <img src="${chartUrl}" alt="Analysis Visualization" loading="lazy" />
        </a>
        <div class="chart-caption">📊 Auto-generated visualization • Click image to expand</div>
      `;
      bubble.appendChild(chartContainer);
    }

    // Attach Data Table if available
    if (dataTable && dataTable.length > 0 && typeof dataTable[0] === "object") {
      const tableWrapper = document.createElement("div");
      tableWrapper.className = "data-table-wrapper";
      const table = document.createElement("table");
      table.className = "data-table";

      const headers = Object.keys(dataTable[0]);
      let tableHtml = "<thead><tr>" + headers.map((h) => `<th>${capitalize(h)}</th>`).join("") + "</tr></thead><tbody>";

      dataTable.slice(0, 10).forEach((row) => {
        tableHtml += "<tr>" + headers.map((h) => `<td>${row[h] !== undefined ? row[h] : ""}</td>`).join("") + "</tr>";
      });
      tableHtml += "</tbody>";
      table.innerHTML = tableHtml;
      tableWrapper.appendChild(table);
      bubble.appendChild(tableWrapper);
    }

    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendLoading(id) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message analyst";
    msgDiv.id = id;
    msgDiv.innerHTML = `
      <div class="message-bubble" style="display: flex; align-items: center; gap: 10px; color: #666;">
        <span class="status-dot"></span>
        <span>Autonomous Analyst is crunching dataset figures and synthesizing insights...</span>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  /**
   * Fetches KPI summary from API
   */
  async function fetchKPIs() {
    try {
      const res = await fetch("/api/kpis");
      const json = await res.json();
      if (json.status === "success" && json.kpis) {
        const k = json.kpis;
        if (kpiRevenue) kpiRevenue.innerText = k.formatted_revenue || "₹0.00";
        if (kpiOrders) kpiOrders.innerText = (k.total_orders || 0).toLocaleString();
        if (kpiAOV) kpiAOV.innerText = k.formatted_aov || "₹0.00";
        if (kpiCancellation) kpiCancellation.innerText = (k.cancellation_rate || 0) + "%";
        if (kpiCategory) kpiCategory.innerText = k.top_category || "N/A";
        if (kpiCity) kpiCity.innerText = k.top_city || "N/A";
      }
    } catch (e) {
      console.warn("Could not load KPIs:", e);
    }
  }

  /**
   * Fetches Active Dataset Info
   */
  async function fetchDatasetsInfo() {
    try {
      const res = await fetch("/api/datasets");
      const json = await res.json();
      if (json.status === "success") {
        if (activeDatasetName) {
          activeDatasetName.innerText = json.active_dataset || "amazon_sales_report.csv";
        }
      }
    } catch (e) {
      console.warn("Could not load dataset info:", e);
    }
  }

  /**
   * Upload file to /api/upload
   */
  async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append("file", file);

    uploadStatus.style.display = "block";
    uploadStatus.className = "upload-status";
    uploadStatus.innerText = `Uploading and parsing ${file.name}...`;

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.success) {
        uploadStatus.className = "upload-status success";
        uploadStatus.innerText = `✅ ${data.message}`;

        // Reload KPIs and metadata
        fetchKPIs();
        fetchDatasetsInfo();

        // Notify in chat
        appendMessage(
          "analyst",
          `🎉 **New Dataset Activated:** \`${data.filename}\` (${data.file_type}).\n` +
            (data.records_count ? `- **Records loaded:** ${data.records_count.toLocaleString()}\n` : "") +
            `You can now ask questions directly on this updated data!`
        );

        setTimeout(() => {
          uploadModal.style.display = "none";
        }, 2000);
      } else {
        uploadStatus.className = "upload-status error";
        uploadStatus.innerText = `❌ ${data.message}`;
      }
    } catch (err) {
      uploadStatus.className = "upload-status error";
      uploadStatus.innerText = `❌ Upload failed: ${err.message}`;
    }
  }

  function updateTopRightSuggestions(suggestions) {
    if (!suggestionsContainer || !suggestions || !suggestions.length) return;
    suggestionsContainer.innerHTML = "";
    suggestions.slice(0, 5).forEach((q) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "suggestion-btn";
      btn.setAttribute("data-query", q);
      btn.innerText = q;
      suggestionsContainer.appendChild(btn);
    });
  }

  function capitalize(str) {
    return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
});
