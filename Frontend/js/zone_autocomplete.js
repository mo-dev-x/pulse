const ZONE_TYPE_EMOJIS = {
  academic: "📚",
  sports: "⚽",
  dining: "🍽️",
  residence: "🏠",
  social: "👥",
  other: "📍",
};

function initZoneAutocomplete(inputId, resultsId, onSelect) {
  const input = document.getElementById(inputId);
  const resultsContainer = document.getElementById(resultsId);
  if (!input || !resultsContainer) return null;

  let debounceTimer = null;
  let selectedZone = null;

  input.addEventListener("input", () => {
    const query = input.value.trim();
    selectedZone = null;
    clearTimeout(debounceTimer);

    if (query.length < 2) {
      hideZoneResults(resultsContainer);
      return;
    }

    debounceTimer = setTimeout(async () => {
      const zones = await searchZones(query);
      renderZoneResults(zones, resultsContainer, (zone) => {
        selectedZone = zone;
        input.value = zone.name;
        hideZoneResults(resultsContainer);
        if (typeof onSelect === "function") onSelect(zone);
      });
    }, 250);
  });

  document.addEventListener("click", (event) => {
    if (!input.contains(event.target) && !resultsContainer.contains(event.target)) {
      hideZoneResults(resultsContainer);
    }
  });

  return {
    getSelectedZone() {
      return selectedZone;
    },
    clearSelection() {
      selectedZone = null;
      input.value = "";
      hideZoneResults(resultsContainer);
    },
  };
}

async function searchZones(query) {
  const baseUrl = window.PULSE_API_BASE || "https://pulse-backend.up.railway.app";
  
  try {
    const response = await fetch(`${baseUrl}/api/zones/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) return [];
    const payload = await response.json();
    return Array.isArray(payload.zones) ? payload.zones : [];
  } catch (error) {
    console.warn("Zone search failed:", error);
    return [];
  }
}

function renderZoneResults(zones, container, onSelect) {
  if (!zones.length) {
    container.innerHTML = '<div class="zone-result empty">No zones found</div>';
    container.style.display = "block";
    return;
  }

  container.innerHTML = zones
    .map((zone) => {
      const type = zone.zone_type || zone.type || "other";
      return `
        <button type="button" class="zone-result" data-zone-id="${zone.id}">
          <span class="zone-result-name">${ZONE_TYPE_EMOJIS[type] || "📍"} ${escapeZoneHtml(zone.name)}</span>
          <span class="zone-result-meta">${escapeZoneHtml(zone.description || "")}</span>
        </button>
      `;
    })
    .join("");

  container.style.display = "block";
  container.querySelectorAll(".zone-result[data-zone-id]").forEach((element) => {
    element.addEventListener("click", () => {
      const zoneId = Number(element.dataset.zoneId);
      const zone = zones.find((item) => item.id === zoneId);
      if (zone) onSelect(zone);
    });
  });
}

function hideZoneResults(container) {
  container.innerHTML = "";
  container.style.display = "none";
}

function escapeZoneHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
