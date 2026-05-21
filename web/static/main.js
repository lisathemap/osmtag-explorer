"use strict";

const searchBtn = document.getElementById("search-btn");
const resultsSection = document.getElementById("results");
const errorBox = document.getElementById("error-box");
const errorMsg = document.getElementById("error-msg");
const summary = document.getElementById("summary");
const resultsBody = document.getElementById("results-body");

function showError(msg) {
  errorBox.hidden = false;
  resultsSection.hidden = true;
  errorMsg.textContent = msg;
}

function clearUI() {
  errorBox.hidden = true;
  resultsSection.hidden = true;
  resultsBody.innerHTML = "";
  summary.textContent = "";
}

function buildBar(percent) {
  const filled = Math.round(percent / 5);
  return "█".repeat(filled) + "░".repeat(20 - filled);
}

async function fetchStats() {
  clearUI();
  const key = document.getElementById("key").value.trim();
  const value = document.getElementById("value").value.trim();
  const area = document.getElementById("area").value.trim();
  const topN = document.getElementById("top_n").value;

  if (!key) {
    showError("Please enter a tag key.");
    return;
  }

  const params = new URLSearchParams({ key, top_n: topN });
  if (value) params.set("value", value);
  if (area) params.set("area", area);

  searchBtn.disabled = true;
  searchBtn.textContent = "Loading…";

  try {
    const resp = await fetch(`/api/stats?${params}`);
    const data = await resp.json();

    if (!resp.ok) {
      showError(data.error || "Unknown error.");
      return;
    }

    summary.textContent = `Total occurrences: ${data.total.toLocaleString()}`;
    data.results.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.label}</td>
        <td>${row.count.toLocaleString()}</td>
        <td>${row.percent.toFixed(1)}%</td>
        <td><span class="bar">${buildBar(row.percent)}</span></td>
      `;
      resultsBody.appendChild(tr);
    });
    resultsSection.hidden = false;
  } catch (err) {
    showError("Network error: " + err.message);
  } finally {
    searchBtn.disabled = false;
    searchBtn.textContent = "Search";
  }
}

searchBtn.addEventListener("click", fetchStats);
document.addEventListener("keydown", e => {
  if (e.key === "Enter") fetchStats();
});
