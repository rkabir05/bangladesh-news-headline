const DATA_URL = "data/headlines.json";
const REFRESH_MS = 5 * 60 * 1000;

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
  const sources = payload.sources || [];
  document.getElementById("updatedAt").textContent = formatDate(payload.updated_at);

  const good = sources.filter(s => s.count >= 10).length;
  document.getElementById("summary").textContent =
    `${sources.length} পোর্টাল · ${payload.summary?.total_headlines || 0} headline · ${good}টি পোর্টালে ১০+`;

  document.getElementById("sources").innerHTML = sources.map(site => `
    <div class="col-12 col-md-6 col-xl-4 col-xxl-3" id="source-${esc(site.source)}">
      <article class="source-card">
        <div class="source-head">
          <h2 class="source-name h6">${esc(site.source)}</h2>
          <span class="source-count">${site.count}টি</span>
        </div>
        <ul class="headlines">
          ${(site.headlines || []).map(item => `
            <li>
              <a href="${esc(item.url)}" target="_blank" rel="noopener noreferrer">
                ${esc(item.title)}
                ${item.time ? `<span class="headline-time">${esc(item.time)}</span>` : ""}
              </a>
            </li>
          `).join("")}
        </ul>
      </article>
    </div>
  `).join("");

  document.getElementById("status").className =
    "alert alert-success border";
  document.getElementById("status").innerHTML =
    `<i class="bi bi-check-circle me-2"></i> সর্বশেষ ডেটা সফলভাবে লোড হয়েছে।`;
}

async function load() {
  try {
    const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    render(await response.json());
  } catch (error) {
    document.getElementById("status").className =
      "alert alert-danger border";
    document.getElementById("status").textContent =
      "বর্তমান headline data লোড করা যায়নি। GitHub Actions-এর সর্বশেষ run পরীক্ষা করুন।";
    console.error(error);
  }
}

load();
setInterval(load, REFRESH_MS);
