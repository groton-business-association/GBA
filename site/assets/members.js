// Member directory: reads data/members.csv and data/categories.csv and renders a searchable list
// with a category and subcategory filter. Checking several categories shows members in any of them.
(function () {
  function parseCSV(text) {
    var rows = [], row = [], field = "", q = false;
    for (var i = 0; i < text.length; i++) {
      var c = text[i];
      if (q) {
        if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else { q = false; } }
        else field += c;
      } else if (c === '"') q = true;
      else if (c === ",") { row.push(field); field = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(field); rows.push(row); row = []; field = "";
      } else field += c;
    }
    if (field.length || row.length) { row.push(field); rows.push(row); }
    var head = rows.shift().map(function (h) { return h.trim().toLowerCase(); });
    return rows.filter(function (r) { return r.join("").trim(); }).map(function (r) {
      var o = {}; head.forEach(function (h, k) { o[h] = (r[k] || "").trim(); }); return o;
    });
  }

  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text) e.textContent = text;
    return e;
  }

  function safeUrl(u) {
    if (!u) return "";
    if (!/^https?:\/\//i.test(u)) u = "https://" + u;
    try { var p = new URL(u); return (p.protocol === "http:" || p.protocol === "https:") ? p.href : ""; } catch (e) { return ""; }
  }

  function splitCats(s) { return (s || "").split(";").map(function (x) { return x.trim(); }).filter(Boolean); }
  function leaf(path) { var p = path.split(" > "); return p[p.length - 1]; }
  function inCat(m, path) {
    return m.cats.some(function (c) { return c === path || c.indexOf(path + " > ") === 0; });
  }

  var list = document.getElementById("dir-list");
  var search = document.getElementById("dir-search");
  var tree = document.getElementById("cat-tree");
  var chosen = document.getElementById("cat-chosen");
  var clearBtn = document.getElementById("cat-clear");
  var count = document.getElementById("dir-count");
  var members = [], checked = [];
  // On phones, start with the category list closed so the members show first
  var panel = document.querySelector(".cat-panel");
  if (panel && window.matchMedia && window.matchMedia("(max-width: 899px)").matches) panel.open = false;

  function render() {
    var term = search.value.trim().toLowerCase();
    var shown = members.filter(function (m) {
      if (checked.length && !checked.some(function (p) { return inCat(m, p); })) return false;
      if (!term) return true;
      return [m.name, m.categories, m.specialty, m.description, m.town, m.contact].join(" ").toLowerCase().indexOf(term) !== -1;
    });

    chosen.textContent = checked.length
      ? "Showing members in: " + checked.map(leaf).join(", ")
      : "";
    clearBtn.hidden = !checked.length;

    list.innerHTML = "";
    count.textContent = shown.length === members.length
      ? members.length + " member businesses and organizations"
      : "Showing " + shown.length + " of " + members.length;
    if (!shown.length) {
      list.appendChild(el("li", { "class": "dir-empty" },
        "No members match. Clear the search box or uncheck a category."));
      return;
    }
    shown.forEach(function (m) {
      var card = el("li", { "class": "member" });
      var mark;
      if (m.logo && /^[a-z0-9._-]+\.(png|jpg|jpeg|webp|svg)$/i.test(m.logo)) {
        mark = el("img", { "class": "member-logo", src: "assets/logos/" + m.logo, alt: m.name + " logo", loading: "lazy" });
      } else {
        var words = m.name.replace(/^the\s+/i, "").replace(/[^A-Za-z0-9 ]/g, " ").split(/\s+/).filter(Boolean);
        mark = el("span", { "class": "member-logo member-initials", "aria-hidden": "true" },
          (words[0] ? words[0][0] : "") + (words[1] ? words[1][0] : ""));
      }
      card.appendChild(mark);
      var body = el("div", { "class": "member-body" });
      card.appendChild(body);

      var h = el("h3");
      var url = safeUrl(m.website);
      if (url) h.appendChild(el("a", { href: url, rel: "noopener", target: "_blank" }, m.name));
      else h.textContent = m.name;
      body.appendChild(h);

      var labels = m.specialty ? [m.specialty] : m.cats.map(leaf);
      var line = labels.slice(0, 3).join(", ") + (labels.length > 3 ? ", and more" : "");
      line = [line, m.town].filter(Boolean).join(". ");
      if (line) body.appendChild(el("p", { "class": "cat" }, line));
      if (m.description) body.appendChild(el("p", { "class": "desc" }, m.description));
      var c = el("p", { "class": "contact" });
      if (m.contact) c.appendChild(el("span", {}, m.contact));
      if (m.email) c.appendChild(el("a", { href: "mailto:" + m.email }, m.email));
      if (m.phone) c.appendChild(el("a", { href: "tel:" + m.phone.replace(/[^0-9+]/g, "") }, m.phone));
      if (c.childNodes.length) body.appendChild(c);
      list.appendChild(card);
    });
  }

  function buildTree(paths) {
    // paths are "Parent", "Parent > Child", "Parent > Child > Grandchild", in Jeff's order
    var ul = el("ul", { "class": "cat-list" });
    var nodes = {};
    paths.forEach(function (p, i) {
      var parts = p.split(" > ");
      var n = members.filter(function (m) { return inCat(m, p); }).length;
      var li = el("li", { "class": "cat-item depth-" + (parts.length - 1) });
      var id = "cat-" + i;
      var box = el("input", { type: "checkbox", id: id, value: p });
      var lab = el("label", { "for": id });
      lab.appendChild(box);
      lab.appendChild(document.createTextNode(" " + parts[parts.length - 1] + " "));
      lab.appendChild(el("span", { "class": "cat-n" }, "(" + n + ")"));
      li.appendChild(lab);
      var parent = parts.length > 1 ? nodes[parts.slice(0, -1).join(" > ")] : null;
      if (parent) {
        var sub = parent.querySelector(":scope > ul");
        if (!sub) { sub = el("ul", { "class": "cat-sub" }); parent.appendChild(sub); }
        sub.appendChild(li);
      } else {
        ul.appendChild(li);
      }
      nodes[p] = li;
      box.addEventListener("change", function () {
        checked = Array.prototype.map.call(tree.querySelectorAll("input:checked"), function (b) { return b.value; });
        render();
      });
    });
    tree.innerHTML = "";
    tree.appendChild(ul);
  }

  function fetchText(url, fallback) {
    if (location.protocol === "file:" && fallback) return Promise.resolve(fallback);
    return fetch(url, { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .catch(function (e) { if (fallback) return fallback; throw e; });
  }

  Promise.all([
    fetchText(window.GBA.membersCsv, window.GBA_MEMBERS_CSV),
    fetchText("data/categories.csv", window.GBA_CATEGORIES_CSV)
  ]).then(function (res) {
    members = parseCSV(res[0]).filter(function (m) { return m.name && !/^(no|n|false|0)$/i.test(m.active || "yes"); });
    members.forEach(function (m) { m.cats = splitCats(m.categories); });
    members.sort(function (a, b) {
      var x = a.name.replace(/^the\s+/i, "").toLowerCase(), y = b.name.replace(/^the\s+/i, "").toLowerCase();
      return x < y ? -1 : x > y ? 1 : 0;
    });
    var paths = parseCSV(res[1]).map(function (r) { return r.category; }).filter(Boolean);
    // include any category a member uses that is missing from the category file
    members.forEach(function (m) { m.cats.forEach(function (c) { if (paths.indexOf(c) === -1) paths.push(c); }); });
    buildTree(paths);
    render();
  }).catch(function () {
    count.textContent = "";
    list.innerHTML = "";
    list.appendChild(el("li", { "class": "dir-empty" },
      "The member list did not load. Refresh the page. If it still does not appear, contact the GBA through the Contact page."));
  });

  search.addEventListener("input", render);
  clearBtn.addEventListener("click", function () {
    Array.prototype.forEach.call(tree.querySelectorAll("input:checked"), function (b) { b.checked = false; });
    checked = [];
    render();
  });
})();
