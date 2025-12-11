# Usage Guide: Embeddable Semantic Search Widget

This guide shows how to embed a lightweight search widget that talks directly to this API deployment (`https://web-production-2d594.up.railway.app`). The widget uses the public `/search` endpoint and mirrors the Icelandic UI from the provided template while mapping fields to the API's response schema.

> The API can be secured with an `X-API-Key` header. If your deployment requires it, add the header in the `fetch` call as shown below.

## Quick embed (copy/paste)

Paste the following snippet into any HTML page. It renders a transparent search panel, fetches results from the API, and shows thumbnails, descriptions, and similarity scores. Update the `API_BASE` constant if you deploy the API elsewhere.

```html
<!-- K2 Leitavél - Myndefnisleit Embed (Transparent) -->
<div id="k2-search-app" class="k2-shell">
  <div class="k2-hero">
    <div class="k2-badge">
      <span class="k2-badge-icon">✦</span>
      Merkingaleit
    </div>
    <h2 class="k2-title">Finndu rétta myndefnið</h2>
    <p class="k2-subtitle">Textamiðuð leit með gervigreind</p>

    <div class="k2-searchbar">
      <input id="k2-input" type="search" placeholder="Leita (t.d. „sólsetur yfir hafi")" autocomplete="off" />
      <button id="k2-button">
        Leita
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </button>
    </div>

    <div class="k2-hints">
      <span class="k2-pill" data-query="næturmynd af borgarskyline">Borgarskyline</span>
      <span class="k2-pill" data-query="körfuboltaleikur í gangi">Íþróttir</span>
      <span class="k2-pill" data-query="drónaskot af fjöllum">Dróni</span>
      <span class="k2-pill" data-query="andlitsmynd með grunnri dýpt">Andlitsmynd</span>
    </div>
  </div>

  <div id="k2-status" class="k2-status"></div>
  <div id="k2-grid" class="k2-grid"></div>
</div>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap');

  :root {
    --k2-bg-card: rgba(255, 255, 255, 0.03);
    --k2-bg-input: rgba(255, 255, 255, 0.05);
    --k2-border: rgba(255, 255, 255, 0.1);
    --k2-border-hover: rgba(255, 255, 255, 0.2);
    --k2-accent: #9333ea;
    --k2-accent-glow: rgba(147, 51, 234, 0.3);
    --k2-text: #ffffff;
    --k2-text-muted: rgba(255, 255, 255, 0.6);
    --k2-radius: 12px;
  }

  .k2-shell {
    font-family: 'Sora', system-ui, -apple-system, sans-serif;
    color: var(--k2-text);
    background: transparent;
    padding: 40px;
    position: relative;
  }

  .k2-hero {
    position: relative;
    z-index: 1;
    margin-bottom: 24px;
  }

  .k2-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 100px;
    background: transparent;
    border: 1px solid var(--k2-border);
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.02em;
    color: var(--k2-text-muted);
  }

  .k2-badge-icon {
    color: var(--k2-accent);
    font-size: 10px;
  }

  .k2-title {
    margin: 20px 0 8px;
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, var(--k2-accent), #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .k2-subtitle {
    margin: 0 0 24px;
    color: var(--k2-text-muted);
    font-size: 15px;
    font-weight: 400;
  }

  .k2-searchbar {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .k2-searchbar input {
    flex: 1;
    min-width: 0;
    background: var(--k2-bg-input);
    border: 1px solid var(--k2-border);
    color: var(--k2-text);
    padding: 14px 18px;
    border-radius: var(--k2-radius);
    font-family: inherit;
    font-size: 15px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .k2-searchbar input::placeholder {
    color: var(--k2-text-muted);
  }

  .k2-searchbar input:focus {
    outline: none;
    border-color: var(--k2-accent);
    box-shadow: 0 0 0 3px var(--k2-accent-glow);
  }

  .k2-searchbar button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: transparent;
    color: var(--k2-text);
    border: 1px solid var(--k2-border);
    padding: 14px 24px;
    border-radius: var(--k2-radius);
    font-family: inherit;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .k2-searchbar button:hover {
    border-color: var(--k2-text);
    background: rgba(255, 255, 255, 0.05);
  }

  .k2-searchbar button svg {
    transition: transform 0.2s ease;
  }

  .k2-searchbar button:hover svg {
    transform: translateX(3px);
  }

  .k2-hints {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 16px;
  }

  .k2-pill {
    padding: 8px 14px;
    border-radius: 100px;
    background: transparent;
    color: var(--k2-text-muted);
    border: 1px solid var(--k2-border);
    cursor: pointer;
    font-size: 13px;
    font-weight: 400;
    transition: all 0.2s ease;
  }

  .k2-pill:hover {
    color: var(--k2-text);
    border-color: var(--k2-border-hover);
    background: rgba(255, 255, 255, 0.03);
  }

  .k2-status {
    min-height: 20px;
    font-size: 13px;
    color: var(--k2-text-muted);
    margin: 8px 0;
    position: relative;
    z-index: 1;
  }

  .k2-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 20px;
    margin-top: 20px;
    position: relative;
    z-index: 1;
  }

  .k2-card {
    position: relative;
    background: var(--k2-bg-card);
    border: 1px solid var(--k2-border);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.25s ease;
    backdrop-filter: blur(10px);
  }

  .k2-card:hover {
    border-color: var(--k2-border-hover);
    transform: translateY(-4px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  }

  .k2-thumb {
    width: 100%;
    height: 180px;
    object-fit: cover;
    background: rgba(255, 255, 255, 0.02);
  }

  .k2-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .k2-name {
    font-weight: 600;
    font-size: 14px;
    color: var(--k2-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .k2-desc {
    font-size: 13px;
    color: var(--k2-text-muted);
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .k2-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: var(--k2-text-muted);
    margin-top: 4px;
  }

  .k2-chip {
    padding: 4px 10px;
    border-radius: 100px;
    background: rgba(147, 51, 234, 0.15);
    border: 1px solid rgba(147, 51, 234, 0.3);
    color: #c084fc;
    font-size: 11px;
    font-weight: 500;
  }

  .k2-similarity {
    font-weight: 500;
  }

  .k2-skeleton {
    height: 280px;
    border-radius: 16px;
    background: linear-gradient(90deg,
      rgba(255,255,255,0.02) 0%,
      rgba(255,255,255,0.06) 50%,
      rgba(255,255,255,0.02) 100%
    );
    background-size: 200% 100%;
    animation: k2-shimmer 1.5s ease-in-out infinite;
    border: 1px solid var(--k2-border);
  }

  @keyframes k2-shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .k2-empty {
    grid-column: 1 / -1;
    text-align: center;
    padding: 60px 20px;
    color: var(--k2-text-muted);
    font-size: 14px;
  }

  @media (max-width: 640px) {
    .k2-shell {
      padding: 24px 16px;
    }
    .k2-searchbar {
      flex-direction: column;
    }
    .k2-searchbar button {
      width: 100%;
      justify-content: center;
    }
    .k2-title {
      font-size: 26px;
    }
  }
</style>

<script>
(() => {
  const API_BASE = "https://web-production-2d594.up.railway.app";
  const input = document.getElementById("k2-input");
  const button = document.getElementById("k2-button");
  const grid = document.getElementById("k2-grid");
  const status = document.getElementById("k2-status");
  const pills = document.querySelectorAll(".k2-pill");

  const params = {
    search_type: "combined",
    limit: 24,
    threshold: 0,
    file_type: "image"
  };

  function setStatus(msg, isError = false) {
    status.textContent = msg || "";
    status.style.color = isError ? "#f87171" : "var(--k2-text-muted)";
  }

  function renderSkeletons(count = 8) {
    grid.innerHTML = "";
    Array.from({ length: count }).forEach(() => {
      const div = document.createElement("div");
      div.className = "k2-skeleton";
      grid.appendChild(div);
    });
  }

  function renderEmpty() {
    grid.innerHTML = '<div class="k2-empty">Engar niðurstöður enn. Prófaðu aðra leit.</div>';
  }

  function renderItems(items) {
    grid.innerHTML = "";
    items.forEach(item => {
      const card = document.createElement("div");
      card.className = "k2-card";

      const img = document.createElement("img");
      img.className = "k2-thumb";
      img.loading = "lazy";
      img.src = item.thumbnail_url || item.storage_url;
      img.alt = item.description || item.filename;

      const body = document.createElement("div");
      body.className = "k2-body";

      const name = document.createElement("div");
      name.className = "k2-name";
      name.textContent = item.filename;

      const desc = document.createElement("div");
      desc.className = "k2-desc";
      desc.textContent = item.description || "Engin lýsing";

      const meta = document.createElement("div");
      meta.className = "k2-meta";

      const chip = document.createElement("div");
      chip.className = "k2-chip";
      chip.textContent = item.file_type === "video" ? "Myndband" : "Mynd";

      const sim = document.createElement("div");
      sim.className = "k2-similarity";
      sim.textContent = item.similarity_score != null
        ? `${(item.similarity_score * 100).toFixed(1)}%`
        : "–";

      meta.appendChild(chip);
      meta.appendChild(sim);

      body.appendChild(name);
      body.appendChild(desc);
      body.appendChild(meta);

      card.appendChild(img);
      card.appendChild(body);
      grid.appendChild(card);
    });
  }

  async function search() {
    const q = input.value.trim();
    if (!q) { setStatus("Skrifaðu leit til að byrja."); renderEmpty(); return; }

    renderSkeletons();
    setStatus("Leita...");

    try {
      const searchParams = new URLSearchParams({
        query: q,
        search_type: params.search_type,
        limit: String(params.limit),
        threshold: String(params.threshold),
        file_type: params.file_type
      });

      const res = await fetch(`${API_BASE}/search?${searchParams.toString()}`, {
        headers: {
          // Uncomment and set if your deployment requires a key:
          // 'X-API-Key': 'your-api-key'
        }
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (!data.results || data.results.length === 0) {
        renderEmpty();
        setStatus("Engar niðurstöður fundust.");
        return;
      }

      renderItems(data.results);
      setStatus(`Fann ${data.results.length} niðurstöður.`);
    } catch (err) {
      console.error(err);
      renderEmpty();
      setStatus("Leit tókst ekki. Athugaðu API slóð eða lykil.", true);
    }
  }

  button.addEventListener("click", search);
  input.addEventListener("keydown", e => { if (e.key === "Enter") search(); });
  pills.forEach(p => p.addEventListener("click", () => {
    input.value = p.dataset.query;
    input.focus();
  }));

  renderEmpty();
})();
</script>
```

### Notes
- The widget reads thumbnails from `thumbnail_url` (falling back to `storage_url`). Ensure your Supabase bucket exposes public URLs or adjust `_get_public_url` in `services/supabase_service.py`.
- The API defaults to `search_type=combined`, `limit=24`, and `file_type=image` for the embed. Adjust those defaults in the `params` object.
- If you have CORS restrictions, set the `CORS_ORIGINS` environment variable when deploying the API (see `main.py`).

## API compatibility

The embed calls the `GET /search` endpoint that wraps the `TextSearchRequest` model, so it understands the same query parameters (`query`, `search_type`, `limit`, `threshold`, `file_type`, `decade`). See `README.md` for more endpoint details.
