const DATA_URL = "data/headlines.json";
const REFRESH_MS = 10 * 60 * 1000; // 10 minutes, mirrors collector schedule
let allSources = [];
let countdownTimer = null;
let nextRefreshAt = null;

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
                ${esc(item.title)}
                ${item.time ? `<span class="headline-time">${esc(formatDate(item.time))}</span>` : ""}
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
  nextRefreshAt = Date.now() + REFRESH_MS;
  countdownTimer = setInterval(() => {
    const remain = Math.max(0, Math.round((nextRefreshAt - Date.now()) / 1000));
    const m = String(Math.floor(remain / 60)).padStart(2, "0");
    const s = String(remain % 60).padStart(2, "0");
    document.getElementById("countdown").textContent = `${m}:${s}`;
  }, 1000);
}

async function load() {
  try {
    const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    render(await response.json());
    document.getElementById("status").className = "alert alert-success border";
    document.getElementById("status").innerHTML =
      `<i class="bi bi-check-circle me-2"></i>সর্বশেষ শিরোনাম লোড হয়েছে — প্রতি ১০ মিনিটে অটো রিফ্রেশ চালু।`;
    startCountdown();
  } catch (error) {
    document.getElementById("status").className = "alert alert-danger border";
    document.getElementById("status").textContent =
      "ডেটা লোড করা যায়নি। GitHub Actions-এর সর্বশেষ run পরীক্ষা করুন।";
    console.error(error);
  }
}

document.getElementById("searchBox").addEventListener("input", applySearch);

load();
setInterval(load, REFRESH_MS);
