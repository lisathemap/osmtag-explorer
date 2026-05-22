/**
 * highlight.js — fetch and render highlighted tag stats from /api/highlight
 */

(function () {
  "use strict";

  const ENDPOINT = "/api/highlight";

  function buildParams(key, q, value, area) {
    const p = new URLSearchParams({ key, q });
    if (value) p.set("value", value);
    if (area) p.set("area", area);
    return p.toString();
  }

  function renderRow(row) {
    const tr = document.createElement("tr");
    if (row.matched) tr.classList.add("hl-match");
    const keyTd = document.createElement("td");
    keyTd.innerHTML = row.key_html || row.key;
    const valTd = document.createElement("td");
    valTd.innerHTML = row.value_html || (row.value ?? "");
    const cntTd = document.createElement("td");
    cntTd.textContent = row.count.toLocaleString();
    tr.appendChild(keyTd);
    tr.appendChild(valTd);
    tr.appendChild(cntTd);
    return tr;
  }

  function renderResults(container, data) {
    container.innerHTML = "";
    const info = document.createElement("p");
    info.className = "hl-info";
    info.textContent = `${data.matched} of ${data.total} results match "${data.query}"`;
    container.appendChild(info);

    const table = document.createElement("table");
    table.className = "hl-table";
    const thead = table.createTHead();
    const hRow = thead.insertRow();
    ["Key", "Value", "Count"].forEach((h) => {
      const th = document.createElement("th");
      th.textContent = h;
      hRow.appendChild(th);
    });
    const tbody = table.createTBody();
    data.results.forEach((row) => tbody.appendChild(renderRow(row)));
    container.appendChild(table);
  }

  async function fetchHighlight(key, q, value, area, container, errorEl) {
    errorEl.textContent = "";
    container.innerHTML = "<p>Loading…</p>";
    try {
      const resp = await fetch(`${ENDPOINT}?${buildParams(key, q, value, area)}`);
      const data = await resp.json();
      if (!resp.ok) {
        errorEl.textContent = data.error || "Unknown error";
        container.innerHTML = "";
        return;
      }
      renderResults(container, data);
    } catch (err) {
      errorEl.textContent = "Network error: " + err.message;
      container.innerHTML = "";
    }
  }

  function init() {
    const form = document.getElementById("hl-form");
    if (!form) return;
    const container = document.getElementById("hl-results");
    const errorEl = document.getElementById("hl-error");
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const key = form.elements["key"].value.trim();
      const q = form.elements["q"].value.trim();
      const value = (form.elements["value"]?.value || "").trim();
      const area = (form.elements["area"]?.value || "").trim();
      if (key && q) fetchHighlight(key, q, value, area, container, errorEl);
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
