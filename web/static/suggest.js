/**
 * Autocomplete / tag suggestion UI for osmtag-explorer.
 */

(function () {
  "use strict";

  const MIN_CHARS = 1;
  const DEBOUNCE_MS = 250;

  let debounceTimer = null;

  function debounce(fn, delay) {
    return function (...args) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  async function fetchSuggestions(query, key = "") {
    const params = new URLSearchParams({ q: query });
    if (key) params.set("key", key);
    const resp = await fetch(`/api/suggest?${params.toString()}`);
    if (!resp.ok) return [];
    const data = await resp.json();
    return data.suggestions || [];
  }

  function renderDropdown(input, suggestions) {
    let dropdown = input.parentElement.querySelector(".suggest-dropdown");
    if (!dropdown) {
      dropdown = document.createElement("ul");
      dropdown.className = "suggest-dropdown";
      input.parentElement.appendChild(dropdown);
    }
    dropdown.innerHTML = "";
    if (suggestions.length === 0) {
      dropdown.style.display = "none";
      return;
    }
    suggestions.forEach((s) => {
      const li = document.createElement("li");
      li.textContent = s.label;
      li.addEventListener("mousedown", (e) => {
        e.preventDefault();
        input.value = s.label;
        dropdown.style.display = "none";
        input.dispatchEvent(new Event("change"));
      });
      dropdown.appendChild(li);
    });
    dropdown.style.display = "block";
  }

  function attachSuggest(input, keyInput = null) {
    const handler = debounce(async () => {
      const q = input.value.trim();
      const key = keyInput ? keyInput.value.trim() : "";
      if (q.length < MIN_CHARS && !key) {
        const dd = input.parentElement.querySelector(".suggest-dropdown");
        if (dd) dd.style.display = "none";
        return;
      }
      const suggestions = await fetchSuggestions(q, key);
      renderDropdown(input, suggestions);
    }, DEBOUNCE_MS);

    input.addEventListener("input", handler);
    input.addEventListener("blur", () => {
      setTimeout(() => {
        const dd = input.parentElement.querySelector(".suggest-dropdown");
        if (dd) dd.style.display = "none";
      }, 150);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const tagInput = document.getElementById("tag-query");
    const keyInput = document.getElementById("key-input");
    if (tagInput) attachSuggest(tagInput, keyInput || null);
  });

  window.osmSuggest = { attachSuggest, fetchSuggestions };
})();
