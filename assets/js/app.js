const DATA_URL = "data/headlines.json";
const REFRESH_MS = 10 * 60 * 1000; // collector publishes new data every 10 minutes
const PROBE_MS = 60 * 1000; // cheap HEAD check every minute — keeps mobile views fresh
const FETCH_TIMEOUT_MS = 15 * 1000;
const PROBE_TIMEOUT_MS = 8 * 1000;
const HIDDEN_PROBE_WINDOW_MS = 5 * 60 * 1000; // pause probing 5 min after the page is fully hidden

let allSources = [];
let countdownTimer = null;
let nextCheckAt = null;
let probing = false;
let lastTag = null; // ETag/Last-Modified of the JSON currently rendered
let dataUpdatedAt = null; // payload.updated_at of the currently rendered data
let staleUntil = 0; // while hidden: timestamp after which background probing pauses

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[c]));
}

function formatDate(value) {
  if (!value) return "অজানা";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("bn-BD", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function render(payload) {
  allSources = payload.sources || [];
  dataUpdatedAt = payload.updated_at || null;
  document.getElementById("updatedAt").textContent = formatDate(payload.updated_at);
  updateSummary();
  paintCards(allSources);
}

function updateSummary() {
  const total = allSources.reduce((sum, s) => sum + (s.count || 0), 0);
  const good = allSources.filter(s => (s.count || 0) >= 10).length;
  document.getElementById("summary").textContent =
    `${allSources.length} পোর্টাল · ${total} শিরোনাম · ${good}টি পোর্টালে ১০+`;
}

function paintCards(sources) {
  document.getElementById("sources").innerHTML = sources.map(site => `
    <div class="col-12 col-md-6 col-xl-4 col-xxl-3">
      <article class="source-card">
        <div class="source-head">
          <h2 class="source-name h6">
            <a class="stretched-host" href="${esc(site.url)}" target="_blank" rel="noopener noreferrer">${esc(site.source)}</a>
          </h2>
          <span class="source-count">${site.count}টি</span>
        </div>
        <ul class="headlines">
          ${(site.headlines || []).map(item => `
            <li>
              <a href="${esc(item.url)}" target="_blank" rel="noopener noreferrer">
                ${item.image ? `<img class="headline-thumb" src="${esc(item.image)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">` : ""}
                <span class="headline-body">
                  ${esc(item.title)}
                  ${item.time ? `<span class="headline-time">${esc(formatDate(item.time))}</span>` : ""}
                </span>
              </a>
            </li>
          `).join("") || `<li class="p-3 small text-secondary">কোনো শিরোনাম পাওয়া যায়নি</li>`}
        </ul>
      </article>
    </div>
  `).join("");
}

function applySearch() {
  const term = document.getElementById("searchBox").value.trim().toLowerCase();
  if (!term) return paintCards(allSources);
  paintCards(allSources
    .map(site => ({
      ...site,
      headlines: (site.headlines || []).filter(h => h.title.toLowerCase().includes(term)),
    }))
    .filter(site => site.headlines.length > 0));
}

function startCountdown() {
  clearInterval(countdownTimer);
  nextCheckAt = Date.now() + PROBE_MS;
  countdownTimer = setInterval(() => {
    const remain = Math.max(0, Math.round((nextCheckAt - Date.now()) / 1000));
    const m = String(Math.floor(remain / 60)).padStart(2, "0");
    const s = String(remain % 60).padStart(2, "0");
    document.getElementById("countdown").textContent = `${m}:${s}`;
  }, 1000);
}

function isDataStale() {
  if (!dataUpdatedAt) return false;
  const updated = new Date(dataUpdatedAt).getTime();
  if (Number.isNaN(updated)) return true;
  // Collector runs every 10 minutes; give it a small grace period.
  return Date.now() - updated > REFRESH_MS + 90 * 1000;
}

function setStatus(kind, html) {
  const el = document.getElementById("status");
  el.className = `alert alert-${kind} border`;
  el.innerHTML = html;
}

function cacheTagOf(response) {
  return response.headers.get("ETag") || response.headers.get("Last-Modified");
}

async function load() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const response = await fetch(`${DATA_URL}?t=${Date.now()}`, {
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    lastTag = cacheTagOf(response);
    render(payload);
    startCountdown();
    setStatus("success",
      `<i class="bi bi-check-circle me-2"></i>সর্বশেষ শিরোনাম লোড হয়েছে — মিনিটে মিনিটে আপডেট-চেক চলছে, অ্যাপে ফিরে এলে সঙ্গে সঙ্গে নতুন ডেটা নেওয়া হয়।`);
  } catch (error) {
    setStatus("danger",
      "ডেটা লোড করা যায়নি — এক মিনিটের মধ্যে আবার চেষ্টা হবে। GitHub Actions-এর সর্বশেষ run পরীক্ষা করুন।");
    console.error(error);
  } finally {
    clearTimeout(timer);
  }
}

// Cheap change-check: has data/headlines.json changed since we rendered it?
// Mobile browsers suspend JS timers while the phone is locked or the tab is in
// the background, so a plain setInterval never fires there. Instead we probe
// every minute while visible AND immediately whenever the page becomes visible
// again — that is what actually pulls fresh headlines on phones.
async function probe() {
  if (probing || document.visibilityState !== "visible") return;
  if (Date.now() < staleUntil) return;
  probing = true;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);
  try {
    const response = await fetch(`${DATA_URL}?t=${Date.now()}`, {
      method: "HEAD",
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const tag = cacheTagOf(response);
    if (!tag || tag !== lastTag) {
      // New data published (or the server gives no cache tags) — full reload.
      await load();
    } else {
      startCountdown();
      if (isDataStale()) {
        setStatus("warning",
          "সার্ভারে এখনো নতুন ডেটা আসেনি (GitHub Actions চলছে বা দেরি হচ্ছে) — পরের চেকে আবার দেখা হবে।");
      }
    }
  } catch {
    startCountdown(); // network hiccup — retry on the next tick
  } finally {
    clearTimeout(timer);
    probing = false;
  }
}

function handleVisible() {
  staleUntil = 0;
  // Coming back from the background is the trigger — never trust timers here.
  probe();
}

function handleHidden() {
  staleUntil = Date.now() + HIDDEN_PROBE_WINDOW_MS;
}

document.getElementById("searchBox").addEventListener("input", applySearch);

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") handleVisible();
  else handleHidden();
});
window.addEventListener("pageshow", event => {
  // Back/forward cache restore resurfaces the old DOM with dead timers.
  if (event.persisted) handleVisible();
});
window.addEventListener("online", handleVisible);

load();
setInterval(probe, PROBE_MS);
setInterval(load, REFRESH_MS); // safety net: force a full refresh every cycle
