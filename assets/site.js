(function () {
  "use strict";

  var dataEl = document.getElementById("arena-data");
  var allData = JSON.parse(dataEl.textContent);

  var state = { cat: "text", sort: "rank", dir: 1, q: "", company: "" };

  var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
  var panels = {};
  document.querySelectorAll(".panel").forEach(function (p) {
    panels[p.id] = p;
  });
  var searchInput = document.getElementById("search");
  var companySelect = document.getElementById("company-filter");

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
    "reve": "reve.com"
  };

  function providerLogoUrl(provider) {
    var domain = PROVIDER_DOMAINS[String(provider).toLowerCase()];
    if (!domain) return null;
    return "https://www.google.com/s2/favicons?domain=" + domain + "&sz=32";
  }

  function escapeText(s) {
    var div = document.createElement("div");
    div.textContent = String(s);
    return div.innerHTML;
  }

  function currentTable() {
    return document.querySelector('.ranking-table[data-cat="' + state.cat + '"]');
  }

  function populateCompanies() {
    var rows = allData[state.cat] || [];
    var seen = {};
    var companies = [];
    rows.forEach(function (r) {
      if (!seen[r.provider]) {
        seen[r.provider] = true;
        companies.push(r.provider);
      }
    });
    companySelect.innerHTML = '<option value="">すべての企業</option>';
    companies.forEach(function (c) {
      var opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      companySelect.appendChild(opt);
    });
  }

  function render() {
    var table = currentTable();
    if (!table) return;
    var tbody = table.querySelector("tbody");
    var rows = (allData[state.cat] || []).slice();

    if (state.q) {
      var q = state.q.toLowerCase();
      rows = rows.filter(function (r) {
        return r.model.toLowerCase().indexOf(q) !== -1;
      });
    }
    if (state.company) {
      rows = rows.filter(function (r) { return r.provider === state.company; });
    }
    rows.sort(function (a, b) { return (a[state.sort] - b[state.sort]) * state.dir; });

    tbody.innerHTML = "";
    rows.forEach(function (r, idx) {
      var detailId = "detail-" + state.cat + "-" + idx;

      var logoUrl = providerLogoUrl(r.provider);
      var logoHtml = logoUrl
        ? '<img src="' + logoUrl + '" alt="" width="16" height="16" loading="lazy" class="provider-logo" onerror="this.remove()">'
        : "";

      var tr = document.createElement("tr");
      tr.className = "row";
      tr.innerHTML =
        '<td data-label="順位">' + r.rank + "</td>" +
        '<td data-label="モデル"><span class="model-cell">' + logoHtml + "<span>" + escapeText(r.model) + "</span></span></td>" +
        '<td data-label="スコア">' + r.score + "</td>" +
        '<td data-label="提供企業"><span class="badge">' + escapeText(r.provider) + "</span></td>" +
        '<td class="chevron-col"><button class="chevron-btn" type="button" aria-expanded="false" aria-controls="' +
        detailId +
        '"><i class="chevron" aria-hidden="true"></i><span class="sr-only">詳細を表示</span></button></td>';

      var detail = document.createElement("tr");
      detail.className = "detail-row";
      detail.id = detailId;
      detail.hidden = true;
      var td = document.createElement("td");
      td.colSpan = 5;
      td.innerHTML =
        '<p class="detail-text">順位の振れ幅: ' +
        escapeText(r.ci_text) +
        "(数値が小さいほど順位の信頼度が高いことを示します)</p>" +
        '<p class="detail-text">投票数: ' +
        escapeText(r.votes_text) +
        "票</p>";
      detail.appendChild(td);

      tr.addEventListener("click", function () {
        var expanding = detail.hidden;
        detail.hidden = !expanding;
        tr.querySelector(".chevron-btn").setAttribute("aria-expanded", String(expanding));
        tr.classList.toggle("expanded", expanding);
      });

      tbody.appendChild(tr);
      tbody.appendChild(detail);
    });
  }

  function activateTab(tab) {
    tabs.forEach(function (t) {
      t.classList.remove("active");
      t.setAttribute("aria-selected", "false");
      t.tabIndex = -1;
    });
    tab.classList.add("active");
    tab.setAttribute("aria-selected", "true");
    tab.tabIndex = 0;
    tab.focus();

    Object.keys(panels).forEach(function (id) { panels[id].classList.add("hidden"); });
    var panel = document.getElementById(tab.getAttribute("aria-controls"));
    if (panel) panel.classList.remove("hidden");

    state.cat = tab.getAttribute("data-cat");
    state.q = "";
    state.company = "";
    searchInput.value = "";
    populateCompanies();
    render();
  }

  tabs.forEach(function (tab, i) {
    tab.addEventListener("click", function () { activateTab(tab); });
    tab.addEventListener("keydown", function (e) {
      var next = null;
      if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
      if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
      if (e.key === "Home") next = tabs[0];
      if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) {
        e.preventDefault();
        activateTab(next);
      }
    });
  });

  document.querySelectorAll(".sort-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.getAttribute("data-sort");
      if (state.sort === key) {
        state.dir *= -1;
      } else {
        state.sort = key;
        state.dir = 1;
      }
      render();
    });
  });

  searchInput.addEventListener("input", function () {
    state.q = searchInput.value;
    render();
  });
  companySelect.addEventListener("change", function () {
    state.company = companySelect.value;
    render();
  });

  populateCompanies();
  render();
})();
