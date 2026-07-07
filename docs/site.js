(function () {
  "use strict";

  var allData = JSON.parse(document.getElementById("arena-data").textContent);

  var state = { cat: "text", sort: "rank", dir: 1, q: "", company: "" };

  var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
  var panel = document.getElementById("panel");
  var tbody = document.getElementById("tbody");
  var podium = document.getElementById("podium");
  var searchInput = document.getElementById("search");
  var companySelect = document.getElementById("company-filter");
  var resultCount = document.getElementById("result-count");

  /* ---------- Provider identity ---------- */

  var PROVIDER_DOMAINS = {
    "openai": "openai.com",
    "anthropic": "anthropic.com",
    "google": "google.com",
    "xai": "x.ai",
    "deepseek": "deepseek.com",
    "alibaba": "alibaba.com",
    "meta": "meta.com",
    "mistral": "mistral.ai",
    "mistral ai": "mistral.ai",
    "cohere": "cohere.com",
    "nvidia": "nvidia.com",
    "midjourney": "midjourney.com",
    "black forest labs": "blackforestlabs.ai",
    "stability ai": "stability.ai",
    "ideogram": "ideogram.ai",
    "reve": "reve.com",
    "microsoft ai": "microsoft.com",
    "bytedance": "bytedance.com",
    "baidu": "baidu.com",
    "tencent": "tencent.com",
    "moonshot": "moonshot.ai",
    "minimax": "minimax.io",
    "z.ai": "z.ai",
    "xiaomi": "mi.com",
    "luma ai": "lumalabs.ai",
    "recraft": "recraft.ai",
    "krea": "krea.ai",
    "runway": "runwayml.com",
    "leonardo ai": "leonardo.ai"
  };

  var PROVIDER_COLORS = {
    "anthropic": "#d97757",
    "openai": "#10a37f",
    "google": "#4285f4",
    "xai": "#3b3b3b",
    "meta": "#0866ff",
    "alibaba": "#ff6a00",
    "deepseek": "#4d6bfe",
    "z.ai": "#3859ff",
    "moonshot": "#16b8a6",
    "minimax": "#ee3f4d",
    "bytedance": "#325ab4",
    "baidu": "#2932e1",
    "xiaomi": "#ff6900",
    "tencent": "#0052d9",
    "nvidia": "#76b900",
    "microsoft ai": "#0078d4",
    "stability ai": "#9d4edd",
    "black forest labs": "#4a4a4a",
    "ideogram": "#14b8a6",
    "reve": "#f97316",
    "luma ai": "#6366f1",
    "recraft": "#333333",
    "krea": "#10b981",
    "hidream": "#8b5cf6",
    "leonardo ai": "#7c3aed",
    "runway": "#00c2a8",
    "pruna": "#f59e0b"
  };

  var FALLBACK_PALETTE = ["#e0655f", "#5f8fe0", "#5fb377", "#c98a3d", "#9a6fd0", "#4fa8b8", "#d06f9a", "#8a9a4f"];

  function providerKey(p) { return String(p).toLowerCase(); }

  function providerColor(p) {
    var key = providerKey(p);
    if (PROVIDER_COLORS[key]) return PROVIDER_COLORS[key];
    var h = 0;
    for (var i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) >>> 0;
    return FALLBACK_PALETTE[h % FALLBACK_PALETTE.length];
  }

  function providerLogoUrl(p) {
    var domain = PROVIDER_DOMAINS[providerKey(p)];
    if (!domain) return null;
    return "https://www.google.com/s2/favicons?domain=" + domain + "&sz=64";
  }

  function escapeText(s) {
    var div = document.createElement("div");
    div.textContent = String(s);
    return div.innerHTML;
  }

  function avatarHtml(provider) {
    // XSS対策: 企業名由来の文字列を onerror などの属性値に埋め込まない。
    // 頭文字フォールバックを最初からDOMに置いておき、ロゴ読込失敗時は
    // 定数文字列の onerror がクラスを外すだけでフォールバックが現れる。
    var logo = providerLogoUrl(provider);
    var color = providerColor(provider);
    var initial = escapeText(String(provider).charAt(0).toUpperCase());
    var img = logo
      ? '<img src="' + logo + '" alt="" loading="lazy" onerror="this.parentNode.classList.remove(\'has-logo\');this.remove()">'
      : "";
    return '<span class="avatar' + (logo ? " has-logo" : "") + '" style="--avatar-bg:' + color + '">' +
      '<span class="avatar-fallback">' + initial + "</span>" + img + "</span>";
  }

  /* ---------- Data helpers ---------- */

  function parseVotes(t) { return parseInt(String(t).replace(/,/g, ""), 10) || 0; }

  function rowsFor(cat) { return allData[cat] || []; }

  function ciLabel(ci) {
    // "±15程度" -> "±15"
    return String(ci).replace(/程度$/, "");
  }

  function deltaHtml(r) {
    // 前日比の順位変動。ビルド側でdeltaが付与されていない古いデータでも
    // そのまま動くよう、未定義はすべて「表示なし」に倒す。
    if (r.is_new) return '<span class="delta new">NEW</span>';
    if (r.delta === null || r.delta === undefined) return "";
    if (r.delta > 0) return '<span class="delta up">▲' + r.delta + "</span>";
    if (r.delta < 0) return '<span class="delta down">▼' + (-r.delta) + "</span>";
    return '<span class="delta same">－</span>';
  }

  /* ---------- Tab counts ---------- */

  document.querySelectorAll(".tab-count").forEach(function (el) {
    var cat = el.getAttribute("data-count");
    el.textContent = rowsFor(cat).length;
  });

  /* ---------- Podium ---------- */

  function renderPodium() {
    var top3 = rowsFor(state.cat).slice().sort(function (a, b) { return a.rank - b.rank; }).slice(0, 3);
    podium.innerHTML = top3.map(function (r, i) {
      var n = i + 1;
      return (
        '<article class="podium-card p' + n + '">' +
          '<div class="podium-head">' +
            '<span class="medal m' + n + '">' + n + "</span>" +
            deltaHtml(r) +
            '<span class="podium-votes">' + escapeText(r.votes_text) + "票</span>" +
          "</div>" +
          '<h2 class="podium-model">' + escapeText(r.model) + "</h2>" +
          '<div class="podium-provider">' + avatarHtml(r.provider) + "<span>" + escapeText(r.provider) + "</span></div>" +
          '<div class="podium-score">' + Math.round(r.score) +
            '<span class="ci">' + escapeText(ciLabel(r.ci_text)) + "</span>" +
          "</div>" +
        "</article>"
      );
    }).join("");
    podium.classList.toggle("dimmed", Boolean(state.q || state.company));
  }

  /* ---------- Companies ---------- */

  function populateCompanies() {
    var seen = {};
    var companies = [];
    rowsFor(state.cat).forEach(function (r) {
      if (!seen[r.provider]) {
        seen[r.provider] = true;
        companies.push(r.provider);
      }
    });
    companies.sort(function (a, b) { return a.localeCompare(b); });
    companySelect.innerHTML = '<option value="">すべての企業</option>';
    companies.forEach(function (c) {
      var opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      companySelect.appendChild(opt);
    });
  }

  /* ---------- Table ---------- */

  function sortValue(r, key) {
    if (key === "votes") return parseVotes(r.votes_text);
    return r[key];
  }

  function render() {
    var all = rowsFor(state.cat);
    var rows = all.slice();

    if (state.q) {
      var q = state.q.toLowerCase();
      rows = rows.filter(function (r) {
        return r.model.toLowerCase().indexOf(q) !== -1 ||
               r.provider.toLowerCase().indexOf(q) !== -1;
      });
    }
    if (state.company) {
      rows = rows.filter(function (r) { return r.provider === state.company; });
    }

    rows.sort(function (a, b) {
      return (sortValue(a, state.sort) - sortValue(b, state.sort)) * state.dir;
    });

    // Score bar range: computed over the whole category so bars stay comparable while filtering
    var scores = all.map(function (r) { return r.score; });
    var min = Math.min.apply(null, scores);
    var max = Math.max.apply(null, scores);
    var span = Math.max(max - min, 1);

    // aria-sort on headers
    document.querySelectorAll(".ranking-table th").forEach(function (th) {
      var btn = th.querySelector(".sort-btn");
      if (!btn) return;
      if (btn.getAttribute("data-sort") === state.sort) {
        th.setAttribute("aria-sort", state.dir === 1 ? "ascending" : "descending");
      } else {
        th.removeAttribute("aria-sort");
      }
    });

    resultCount.textContent = rows.length === all.length
      ? "全" + all.length + "件"
      : all.length + "件中 " + rows.length + "件を表示";

    if (!rows.length) {
      tbody.innerHTML =
        '<tr class="empty-row"><td colspan="4">' +
          '<p class="empty-title">該当するモデルがありません</p>' +
          "<p>検索条件や企業の絞り込みを変更してみてください。</p>" +
          '<button class="clear-filters" type="button">条件をクリア</button>' +
        "</td></tr>";
      tbody.querySelector(".clear-filters").addEventListener("click", clearFilters);
      return;
    }

    tbody.innerHTML = rows.map(function (r) {
      var medal = r.rank <= 3 ? " m" + r.rank : "";
      var pct = 8 + 92 * ((r.score - min) / span);
      return (
        "<tr>" +
          '<td class="rank-td"><span class="rank-cell' + medal + '">' + r.rank + "</span>" + deltaHtml(r) + "</td>" +
          "<td>" +
            '<div class="model">' + avatarHtml(r.provider) +
              '<div class="model-text">' +
                '<div class="model-name">' + escapeText(r.model) + "</div>" +
                '<div class="model-sub"><span class="provider-dot" style="background:' + providerColor(r.provider) + '"></span>' + escapeText(r.provider) + "</div>" +
              "</div>" +
            "</div>" +
          "</td>" +
          '<td class="score-cell">' +
            '<div class="score-num">' + Math.round(r.score) + '<span class="ci">' + escapeText(ciLabel(r.ci_text)) + "</span></div>" +
            '<div class="score-bar"><i style="width:' + pct.toFixed(1) + '%"></i></div>' +
          "</td>" +
          '<td class="votes-cell">' + escapeText(r.votes_text) + "</td>" +
        "</tr>"
      );
    }).join("");
  }

  function clearFilters() {
    state.q = "";
    state.company = "";
    searchInput.value = "";
    companySelect.value = "";
    renderPodium();
    render();
  }

  /* ---------- Tabs ---------- */

  function activateTab(tab, focus) {
    tabs.forEach(function (t) {
      t.classList.remove("active");
      t.setAttribute("aria-selected", "false");
      t.tabIndex = -1;
    });
    tab.classList.add("active");
    tab.setAttribute("aria-selected", "true");
    tab.tabIndex = 0;
    if (focus) tab.focus();

    panel.setAttribute("aria-labelledby", tab.id);
    state.cat = tab.getAttribute("data-cat");
    state.sort = "rank";
    state.dir = 1;
    state.q = "";
    state.company = "";
    searchInput.value = "";
    populateCompanies();
    renderPodium();
    render();
  }

  tabs.forEach(function (tab, i) {
    tab.addEventListener("click", function () { activateTab(tab, false); });
    tab.addEventListener("keydown", function (e) {
      var next = null;
      if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
      if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
      if (e.key === "Home") next = tabs[0];
      if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) {
        e.preventDefault();
        activateTab(next, true);
      }
    });
  });

  /* ---------- Sort ---------- */

  document.querySelectorAll(".sort-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.getAttribute("data-sort");
      if (state.sort === key) {
        state.dir *= -1;
      } else {
        state.sort = key;
        // Scores and votes are more interesting in descending order first
        state.dir = key === "rank" ? 1 : -1;
      }
      render();
    });
  });

  /* ---------- Filters ---------- */

  searchInput.addEventListener("input", function () {
    state.q = searchInput.value.trim();
    renderPodium();
    render();
  });

  companySelect.addEventListener("change", function () {
    state.company = companySelect.value;
    renderPodium();
    render();
  });

  /* ---------- Theme toggle ---------- */

  document.getElementById("theme-toggle").addEventListener("click", function () {
    var root = document.documentElement;
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
  });

  /* ---------- Init ---------- */

  populateCompanies();
  renderPodium();
  render();
})();
