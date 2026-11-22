(() => {
  "use strict";
  const $ = (sel, el = document) => el.querySelector(sel);
  const enc = encodeURIComponent;

  // Создание элемента. Данные из БД всегда попадают в DOM через textContent / текстовые узлы (без innerHTML).
  function h(tag, props = {}, ...kids) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (v === undefined || v === null || v === false) continue;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k === "value") e.value = v;
      else if (k === "checked") e.checked = true;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) e.append(kid);
    return e;
  }

  async function api(path, opts) {
    const r = await fetch(path, opts);
    if (!r.ok) {
      let msg = `Ошибка ${r.status}`;
      try {
        const j = await r.json();
        if (j.error) msg = j.error;
        else if (typeof j.detail === "string") msg = j.detail;
      } catch (_) { /* тело не JSON */ }
      throw new Error(msg);
    }
    return r;
  }
  const getJSON = async (p) => (await api(p)).json();
  const postJSON = (p, body) =>
    api(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

  // ---------- форматирование ----------
  const NUM = /^-?\d+(\.\d+)?$/;
  const isNumLike = (v) =>
    typeof v === "number" || (typeof v === "string" && NUM.test(v) && !(v.length > 1 && v[0] === "0" && v[1] !== "."));
  function colIsNumeric(rows, i) {
    let seen = false;
    for (const r of rows) {
      const v = r[i];
      if (v === null) continue;
      if (!isNumLike(v)) return false;
      seen = true;
    }
    return seen;
  }
  function showVal(v) {
    if (v === null || v === undefined) return "";
    if (typeof v === "string" && /^-?\d+\.\d+$/.test(v)) return v.replace(/\.?0+$/, "");
    return String(v);
  }

  // ---------- меню ----------
  async function buildMenu() {
    const nav = $("#menu");
    try {
      const menu = await getJSON("/api/menu");
      nav.replaceChildren();
      for (const sec of menu) {
        const det = h("details", { class: "sec" }, h("summary", { text: sec.title }));
        for (const g of sec.groups) {
          const ul = h("ul");
          for (const q of g.queries) {
            ul.append(h("li", {}, h("button", { class: "qbtn", type: "button", title: q.kind || "", onclick: () => openQuery(q.id) }, q.title)));
          }
          det.append(h("div", { class: "group" }, h("div", { class: "gtitle", text: g.title }), ul));
        }
        nav.append(det);
      }
    } catch (e) {
      nav.replaceChildren(h("div", { class: "error", text: "Не удалось загрузить меню: " + e.message }));
    }
  }

  $("#menu-search").addEventListener("input", (ev) => {
    const t = ev.target.value.trim().toLowerCase();
    for (const det of document.querySelectorAll("#menu details.sec")) {
      let any = false;
      for (const g of det.querySelectorAll(".group")) {
        let gany = false;
        for (const li of g.querySelectorAll("li")) {
          const ok = !t || li.textContent.toLowerCase().includes(t);
          li.hidden = !ok;
          if (ok) gany = true;
        }
        g.hidden = !gany;
        if (gany) any = true;
      }
      det.hidden = !any;
      if (t) det.open = any;
    }
  });

  // ---------- вкладки ----------
  const tabs = [];
  let activeId = null;
  let seq = 0;

  function activate(id) {
    activeId = id;
    for (const t of tabs) {
      const on = t.id === id;
      t.btn.classList.toggle("active", on);
      t.btn.setAttribute("aria-selected", String(on));
      t.panel.hidden = !on;
    }
    $("#welcome").hidden = tabs.length > 0;
    const cur = tabs.find((x) => x.id === id);
    if (cur) cur.btn.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  function closeTab(id) {
    const i = tabs.findIndex((t) => t.id === id);
    if (i < 0) return;
    const [t] = tabs.splice(i, 1);
    t.btn.remove();
    t.panel.remove();
    if (activeId === id) {
      const next = tabs[i] || tabs[i - 1];
      activate(next ? next.id : null);
    } else {
      activate(activeId);
    }
  }

  // Каждое открытие запроса создаёт НОВУЮ вкладку (можно открыть один и тот же запрос с разными параметрами).
  async function openQuery(qid) {
    const id = ++seq;
    const panel = h("section", { class: "panel", hidden: true }, h("div", { class: "loading", text: "Загрузка…" }));
    const label = h("span", { class: "tlabel", text: "…" });
    const close = h("button", {
      class: "tclose", type: "button", title: "Закрыть вкладку", "aria-label": "Закрыть вкладку",
      onclick: (ev) => { ev.stopPropagation(); closeTab(id); },
    }, "×");
    const btn = h("div", {
      class: "tab", role: "tab", tabindex: "0", onclick: () => activate(id),
      onkeydown: (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); activate(id); } },
    }, label, close);
    $("#tabs").append(btn);
    $("#panels").append(panel);
    const entry = { id, qid, btn, panel };
    tabs.push(entry);
    activate(id);
    try {
      const meta = await getJSON(`/api/queries/${enc(qid)}`);
      if (!panel.isConnected) return; // вкладку уже закрыли
      const same = tabs.filter((t) => t.qid === qid && t.id !== id).length;
      label.textContent = same ? `${meta.title} (${same + 1})` : meta.title;
      btn.title = `${meta.section} › ${meta.title}`;
      buildPanel(meta, panel);
    } catch (e) {
      label.textContent = "Ошибка";
      panel.replaceChildren(h("div", { class: "error", text: e.message }));
    }
  }

  // ---------- содержимое вкладки ----------
  function paramControl(meta, v, controls, ready, run) {
    const wrap = h("div", { class: "param" });
    const lab = h("label", { text: v.label });
    const onEnter = (ev) => { if (ev.key === "Enter") run(); };
    if (v.type === "date") {
      const inp = h("input", { type: "date", value: v.default || "", onkeydown: onEnter });
      controls[v.name] = () => inp.value;
      wrap.append(lab, inp);
    } else if (v.type === "multiselect") {
      const list = h("div", { class: "mslist" }, h("div", { class: "loading", text: "Загрузка списка…" }));
      const setAll = (on) => list.querySelectorAll("input[type=checkbox]").forEach((i) => { i.checked = on; });
      const bar = h("div", { class: "msbar" },
        h("button", { type: "button", class: "link", onclick: () => setAll(true) }, "Все"),
        h("button", { type: "button", class: "link", onclick: () => setAll(false) }, "Снять"));
      controls[v.name] = () => [...list.querySelectorAll("input[type=checkbox]:checked")].map((i) => i.value);
      ready.push(
        getJSON(`/api/queries/${enc(meta.id)}/options/${enc(v.name)}`)
          .then((opts) => {
            list.replaceChildren(...opts.map((o) =>
              h("label", { class: "opt" }, h("input", { type: "checkbox", value: String(o.value), checked: true }), String(o.label ?? o.value))));
          })
          .catch((e) => list.replaceChildren(h("div", { class: "error", text: e.message }))));
      wrap.append(lab, h("div", { class: "ms" }, bar, list));
    } else {
      const inp = h("input", { type: "text", maxlength: "200", value: v.default || "", onkeydown: onEnter });
      controls[v.name] = () => inp.value;
      wrap.append(lab, inp);
    }
    return wrap;
  }

  function buildPanel(meta, panel) {
    const state = { cols: [], rows: [], numeric: [], text: [], sortCol: -1, sortDir: 1, filter: "", res: null };
    const controls = {};
    const ready = [];
    let busy = false;

    const status = h("span", { class: "status" });
    const msg = h("div", { class: "msg error", hidden: true });
    const result = h("div", { class: "result" });
    const btnRun = h("button", { class: "primary", type: "button", onclick: () => run() }, "Показать");
    const btnXls = h("button", { type: "button", onclick: () => exportXlsx() }, "Скачать Excel");
    const form = h("div", { class: "params" }, meta.variables.map((v) => paramControl(meta, v, controls, ready, run)));

    panel.replaceChildren(...[
      h("h2", { text: meta.title }),
      h("div", { class: "crumbs", text: [meta.section, meta.group].filter(Boolean).join(" › ") }),
      meta.description
        ? h("details", { class: "desc", open: true }, h("summary", { text: "Описание" }), h("pre", { text: meta.description }))
        : null,
      meta.variables.length ? form : null,
      h("div", { class: "toolbar" }, btnRun, btnXls, status),
      msg,
      result,
    ].filter(Boolean));

    const params = () => {
      const p = {};
      for (const [n, get] of Object.entries(controls)) p[n] = get();
      return p;
    };
    const setBusy = (on, text) => {
      busy = on;
      btnRun.disabled = on;
      btnXls.disabled = on;
      status.textContent = text || "";
    };
    const showError = (text) => { msg.textContent = text; msg.hidden = !text; };

    async function run() {
      if (busy) return;
      showError("");
      setBusy(true, "Выполняется…");
      try {
        await Promise.all(ready);
        const r = await (await postJSON(`/api/queries/${enc(meta.id)}/run`, { params: params() })).json();
        state.cols = r.columns;
        state.rows = r.rows;
        state.res = r;
        state.sortCol = -1;
        state.sortDir = 1;
        state.filter = "";
        state.numeric = r.columns.map((_, i) => colIsNumeric(r.rows, i));
        state.text = r.rows.map((row) => row.map(showVal).join("\u0001").toLowerCase());
        renderResult();
        setBusy(false, "");
      } catch (e) {
        result.replaceChildren();
        showError(e.message);
        setBusy(false, "");
      }
    }

    function renderResult() {
      const info = h("div", { class: "info" });
      const flt = h("input", {
        type: "search", placeholder: "Фильтр по таблице…", autocomplete: "off",
        oninput: (ev) => { state.filter = ev.target.value; renderBody(); },
      });
      const tbody = h("tbody");
      const ths = state.cols.map((c, i) =>
        h("th", {
          class: state.numeric[i] ? "num" : "", title: "Сортировать",
          onclick: () => {
            if (state.sortCol === i) state.sortDir *= -1;
            else { state.sortCol = i; state.sortDir = 1; }
            renderBody();
          },
        }, c, h("span", { class: "arrow" })));
      const table = h("table", {}, h("thead", {}, h("tr", {}, ths)), tbody);
      result.replaceChildren(
        h("div", { class: "rbar" }, flt, info),
        h("div", { class: "tablewrap" }, table));

      function renderBody() {
        const f = state.filter.trim().toLowerCase();
        let idx = state.rows.map((_, i) => i);
        if (f) idx = idx.filter((i) => state.text[i].includes(f));
        if (state.sortCol >= 0) {
          const c = state.sortCol, num = state.numeric[c], d = state.sortDir;
          idx.sort((a, b) => {
            const x = state.rows[a][c], y = state.rows[b][c];
            if (x === null) return y === null ? 0 : 1; // пустые значения всегда внизу
            if (y === null) return -1;
            const cmp = num ? parseFloat(x) - parseFloat(y) : String(x).localeCompare(String(y), "ru", { numeric: true });
            return cmp * d;
          });
        }
        const frag = document.createDocumentFragment();
        for (const i of idx) {
          const tr = document.createElement("tr");
          state.rows[i].forEach((v, c) => {
            const td = document.createElement("td");
            td.textContent = showVal(v);
            if (state.numeric[c]) td.className = "num";
            tr.append(td);
          });
          frag.append(tr);
        }
        tbody.replaceChildren(frag);
        ths.forEach((th, i) => { th.querySelector(".arrow").textContent = state.sortCol === i ? (state.sortDir === 1 ? "▲" : "▼") : ""; });
        const r = state.res;
        let text = `Показано ${idx.length} из ${state.rows.length} строк · ${r.elapsed_ms} мс`;
        info.classList.toggle("warn", r.truncated);
        if (r.truncated) text += ` · достигнут лимит ${r.row_limit} строк: показаны не все данные (уточните параметры или скачайте Excel)`;
        if (!state.rows.length) text = `Нет строк · ${r.elapsed_ms} мс`;
        info.textContent = text;
      }
      renderBody();
    }

    async function exportXlsx() {
      if (busy) return;
      showError("");
      setBusy(true, "Формируется файл…");
      try {
        await Promise.all(ready);
        const r = await postJSON(`/api/queries/${enc(meta.id)}/export`, { params: params() });
        const blob = await r.blob();
        const m = /filename\*=UTF-8''([^;]+)/i.exec(r.headers.get("Content-Disposition") || "");
        const name = m ? decodeURIComponent(m[1]) : "export.xlsx";
        const url = URL.createObjectURL(blob);
        const a = h("a", { href: url, download: name });
        document.body.append(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 10000);
        setBusy(false, `Файл сформирован: ${name}`);
      } catch (e) {
        showError(e.message);
        setBusy(false, "");
      }
    }

    if (meta.variables.length === 0) run(); // запросы без параметров выполняются сразу
  }

  buildMenu();
})();
