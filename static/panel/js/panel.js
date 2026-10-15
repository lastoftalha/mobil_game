/* Bitasarımlazım — yönetim paneli etkileşimleri */
(function () {
  "use strict";

  var P = window.PANEL || {};
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function post(url, body, isJson) {
    var opts = { method: "POST", headers: { "X-CSRFToken": P.csrf, "X-Requested-With": "XMLHttpRequest" }, credentials: "same-origin" };
    if (isJson) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body || {}); }
    else if (body) { opts.body = body; }
    return fetch(url, opts).then(function (r) { return r.json().then(function (j) { if (!r.ok) throw j; return j; }); });
  }
  function toast(text, type) {
    var wrap = $(".toasts");
    if (!wrap) { wrap = document.createElement("div"); wrap.className = "toasts"; document.body.appendChild(wrap); }
    var t = document.createElement("div");
    t.className = "toast toast--" + (type || "success");
    t.innerHTML = '<svg class="ico"><use href="#i-' + (type === "error" ? "triangle-alert" : "circle-check") + '"/></svg><span></span><button type="button" class="icon-btn" data-dismiss aria-label="Kapat"><svg class="ico"><use href="#i-x"/></svg></button>';
    $("span", t).textContent = text;
    wrap.appendChild(t);
    bindToast(t);
  }
  var TR = { "ç": "c", "ğ": "g", "ı": "i", "i̇": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u" };
  function slugify(s) {
    return (s || "").toLocaleLowerCase("tr").replace(/[çğıöşüâîû]/g, function (c) { return TR[c] || c; })
      .normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9\s-]/g, "").trim()
      .replace(/[\s_-]+/g, "-").replace(/^-+|-+$/g, "");
  }

  /* Kenar menü (mobil) */
  $$("[data-sidebar-toggle]").forEach(function (b) { b.addEventListener("click", function () { document.body.classList.toggle("sidebar-open"); }); });
  $$("[data-sidebar-close]").forEach(function (b) { b.addEventListener("click", function () { document.body.classList.remove("sidebar-open"); }); });

  /* Bildirimler */
  function bindToast(t) {
    var close = function () { t.style.transition = "opacity .25s, transform .25s"; t.style.opacity = "0"; t.style.transform = "translateY(8px)"; setTimeout(function () { t.remove(); }, 260); };
    var btn = $("[data-dismiss]", t);
    if (btn) btn.addEventListener("click", close);
    setTimeout(close, t.classList.contains("toast--error") ? 9000 : 5000);
  }
  $$(".toast").forEach(bindToast);

  /* Onay isteyen işlemler */
  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-confirm]");
    if (el && !window.confirm(el.getAttribute("data-confirm"))) { e.preventDefault(); e.stopPropagation(); }
  }, true);

  /* Filtre seçince formu gönder */
  $$("[data-autosubmit]").forEach(function (s) { s.addEventListener("change", function () { s.form.submit(); }); });

  /* Sekmeler */
  $$("[data-tabs]").forEach(function (root) {
    var tabs = $$(".tab", root), panels = $$("[data-tab-panel]", root), input = $("[data-tab-input]", root);
    if (!tabs.length) return;
    function open(key) {
      tabs.forEach(function (t) { t.classList.toggle("is-active", t.getAttribute("data-tab") === key); });
      panels.forEach(function (p) { p.hidden = p.getAttribute("data-tab-panel") !== key; });
      if (input) input.value = key;
      if (root.hasAttribute("data-tab-hash")) history.replaceState(null, "", "#" + key);
    }
    tabs.forEach(function (t) { t.addEventListener("click", function () { open(t.getAttribute("data-tab")); }); });
    var withError = tabs.filter(function (t) { return t.classList.contains("has-error"); })[0];
    var hash = location.hash.slice(1);
    if (withError) open(withError.getAttribute("data-tab"));
    else if (hash && tabs.some(function (t) { return t.getAttribute("data-tab") === hash; })) open(hash);
  });

  /* Anlık aç/kapat anahtarları */
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-toggle-url]");
    if (!btn) return;
    e.preventDefault();
    btn.classList.add("is-busy");
    post(btn.getAttribute("data-toggle-url")).then(function (j) {
      btn.classList.toggle("is-on", !!j.value);
      btn.setAttribute("aria-pressed", j.value ? "true" : "false");
      var row = btn.closest(".section-row");
      if (row) row.classList.toggle("is-off", !j.value);
    }).catch(function (err) {
      toast((err && err.error) || "İşlem yapılamadı.", "error");
    }).finally(function () { btn.classList.remove("is-busy"); });
  });

  /* Sürükle-bırak sıralama (liste ve bölümler) */
  if (window.Sortable) {
    $$("[data-sortable]").forEach(function (list) {
      window.Sortable.create(list, {
        handle: "[data-drag]", animation: 160, ghostClass: "sortable-ghost", chosenClass: "sortable-chosen",
        onEnd: function () {
          var ids = $$("[data-id]", list).filter(function (el) { return el.parentElement === list; }).map(function (el) { return el.getAttribute("data-id"); });
          post(list.getAttribute("data-reorder-url"), { ids: ids, offset: +(list.getAttribute("data-offset") || 0) }, true)
            .then(function () { toast("Sıralama kaydedildi."); })
            .catch(function () { toast("Sıralama kaydedilemedi.", "error"); });
        }
      });
    });
  }

  /* Toplu seçim */
  $$("[data-bulk-form]").forEach(function (form) {
    var all = $("[data-check-all]", form), checks = $$("[data-check]", form), bar = $("[data-bulkbar]", form), count = $("[data-bulk-count]", form);
    function update() {
      var n = checks.filter(function (c) { return c.checked; }).length;
      if (bar) bar.hidden = n === 0;
      if (count) count.textContent = n;
      if (all) all.checked = n > 0 && n === checks.length;
    }
    if (all) all.addEventListener("change", function () { checks.forEach(function (c) { c.checked = all.checked; }); update(); });
    checks.forEach(function (c) { c.addEventListener("change", update); });
  });

  /* Görsel / dosya yükleme alanları */
  function bindUpload(root) {
    var input = $('input[type="file"]', root);
    if (!input || input._bound) return;
    input._bound = true;
    var name = $("[data-upload-name]", root), preview = $("[data-upload-preview]", root), drop = input.closest(".upload__drop, .upload-bulk, .dropzone__area") || root;
    input.addEventListener("change", function () {
      var files = input.files;
      if (!files || !files.length) return;
      if (name) name.textContent = files.length > 1 ? files.length + " dosya seçildi" : files[0].name;
      if (preview && files[0].type.indexOf("image/") === 0) {
        var url = URL.createObjectURL(files[0]);
        preview.innerHTML = "";
        var img = document.createElement("img"); img.src = url; img.alt = ""; preview.appendChild(img);
      }
      markDirty(input);
    });
    ["dragenter", "dragover"].forEach(function (ev) { drop.addEventListener(ev, function () { drop.classList.add("is-drag"); }); });
    ["dragleave", "drop"].forEach(function (ev) { drop.addEventListener(ev, function () { drop.classList.remove("is-drag"); }); });
  }
  $$("[data-upload], .upload-bulk, [data-dropzone]").forEach(bindUpload);

  /* Renk seçici eşitleme */
  function bindColor(root) {
    var picker = $("[data-color-picker]", root), text = $("[data-color-text]", root);
    if (!picker || !text) return;
    picker.addEventListener("input", function () { text.value = picker.value.toUpperCase(); markDirty(text); });
    text.addEventListener("input", function () { if (/^#[0-9a-f]{6}$/i.test(text.value)) picker.value = text.value; });
  }
  $$(".color-field").forEach(bindColor);

  /* Slug otomatik doldurma */
  $$("form").forEach(function (form) {
    var source = $("[data-slug-source]", form), slug = $("[data-slug]", form);
    if (!source || !slug || slug.disabled) return;
    var auto = !slug.value;
    slug.addEventListener("input", function () { auto = !slug.value; });
    slug.addEventListener("blur", function () { if (slug.value) slug.value = slugify(slug.value); });
    source.addEventListener("input", function () { if (auto) slug.value = slugify(source.value); });
  });

  /* Karakter sayacı (SEO) */
  $$("[data-counter]").forEach(function (el) {
    var max = +el.getAttribute("data-counter");
    var label = el.closest(".field") && $(".field__label", el.closest(".field"));
    if (!label) return;
    var c = document.createElement("span"); c.className = "counter"; label.appendChild(c);
    function upd() { c.textContent = el.value.length + " / " + max; c.classList.toggle("is-over", el.value.length > max); }
    el.addEventListener("input", upd); upd();
  });

  /* Zengin metin editörü (Quill) */
  function cleanHtml(html) {
    html = (html || "").replace(/&nbsp;/g, " ").replace(/<p><br><\/p>/g, "").trim();
    return html === "<p></p>" ? "" : html;
  }
  function initRte(root) {
    if (root._quill || !window.Quill) return;
    var holder = $(".rte__editor", root), source = $(".rte__source", root), toggle = $("[data-rte-toggle]", root);
    var quill = new window.Quill(holder, {
      theme: "snow",
      placeholder: "Metni buraya yazın…",
      modules: {
        toolbar: {
          container: [[{ header: [2, 3, 4, false] }], ["bold", "italic", "underline", "strike"], [{ list: "ordered" }, { list: "bullet" }], ["blockquote", "link", "image"], ["clean"]],
          handlers: { image: function () { uploadImage(quill); } }
        }
      }
    });
    if (source.value) quill.clipboard.dangerouslyPasteHTML(source.value);
    quill.history.clear();
    root._quill = quill;
    quill.on("text-change", function (d, o, src) { if (src === "user") markDirty(source); });
    function sync() { if (!root.classList.contains("is-source")) source.value = quill.getText().trim() || quill.root.querySelector("img") ? cleanHtml(quill.getSemanticHTML()) : ""; }
    root._sync = sync;
    if (toggle) toggle.addEventListener("click", function () {
      if (root.classList.contains("is-source")) {
        quill.setContents([]);
        if (source.value) quill.clipboard.dangerouslyPasteHTML(source.value);
        root.classList.remove("is-source");
        source.hidden = true;
        toggle.lastChild.textContent = " HTML kaynağı";
      } else {
        sync();
        root.classList.add("is-source");
        source.hidden = false;
        toggle.lastChild.textContent = " Görsel düzenleyici";
      }
    });
    var form = root.closest("form");
    if (form) form.addEventListener("submit", sync);
  }
  function uploadImage(quill) {
    var input = document.createElement("input");
    input.type = "file"; input.accept = "image/*";
    input.onchange = function () {
      if (!input.files.length) return;
      var fd = new FormData(); fd.append("file", input.files[0]);
      toast("Görsel yükleniyor…");
      post(P.uploadUrl, fd).then(function (j) {
        var range = quill.getSelection(true);
        quill.insertEmbed(range ? range.index : quill.getLength(), "image", j.url, "user");
      }).catch(function (err) { toast((err && err.error) || "Görsel yüklenemedi.", "error"); });
    };
    input.click();
  }
  $$("[data-rte]").forEach(initRte);

  /* Alt öğeler (formset) */
  $$("[data-formset]").forEach(function (fs) {
    var prefix = fs.getAttribute("data-prefix");
    var list = $("[data-formset-list]", fs), tpl = $("[data-formset-template]", fs), total = $("#id_" + prefix + "-TOTAL_FORMS", fs);
    var count = $("[data-formset-count]", fs), empty = $("[data-formset-empty]", fs);
    function refresh() {
      var items = $$("[data-formset-item]", list).filter(function (i) { return !i.classList.contains("is-deleted"); });
      if (count) count.textContent = items.length;
      if (empty) empty.hidden = $$("[data-formset-item]", list).length > 0;
    }
    function bindItem(item) {
      $$("[data-fs-collapse]", item).forEach(function (b) { b.addEventListener("click", function () { item.classList.toggle("is-open"); }); });
      var del = $('input[name$="-DELETE"]', item);
      if (del) del.addEventListener("change", function () { item.classList.toggle("is-deleted", del.checked); if (del.checked) item.classList.remove("is-open"); refresh(); markDirty(del); });
      var title = $(".fs-item__title", item), first = $('.fs-item__body input[type="text"], .fs-item__body textarea', item);
      if (title && first && item.classList.contains("is-new")) first.addEventListener("input", function () { title.textContent = first.value || title.getAttribute("data-default") || title.textContent; });
      $$("[data-upload]", item).forEach(bindUpload);
      $$(".color-field", item).forEach(bindColor);
      $$("[data-rte]", item).forEach(initRte);
    }
    $$("[data-formset-item]", list).forEach(bindItem);
    var add = $("[data-formset-add]", fs);
    if (add && tpl && total) add.addEventListener("click", function () {
      var index = +total.value;
      var html = tpl.innerHTML.replace(/__prefix__/g, index);
      var wrap = document.createElement("div"); wrap.innerHTML = html.trim();
      var item = wrap.firstElementChild;
      list.appendChild(item);
      total.value = index + 1;
      bindItem(item);
      refresh();
      var firstInput = $(".fs-item__body input:not([type=hidden]), .fs-item__body textarea", item);
      if (firstInput) firstInput.focus();
      markDirty(total);
    });
    if (window.Sortable && list) window.Sortable.create(list, { handle: "[data-drag]", animation: 160, ghostClass: "sortable-ghost", onEnd: function () { markDirty(list); } });
    var form = fs.closest("form");
    if (form) form.addEventListener("submit", function () {
      $$("[data-formset-item]", list).forEach(function (item, i) {
        var order = $("[data-order]", item);
        if (order) order.value = i;
        if (item.classList.contains("is-new")) {
          var filled = $$(".fs-item__body input, .fs-item__body textarea, .fs-item__body select", item).some(function (el) {
            if (el.type === "hidden" || el.type === "checkbox") return false;
            if (el.type === "file") return el.files && el.files.length;
            return el.value.trim() !== "";
          });
          var del = $('input[name$="-DELETE"]', item);
          if (!filled && del) del.checked = true;
        }
      });
    });
    refresh();
  });

  /* Diyaloglar */
  $$("[data-open-dialog]").forEach(function (b) {
    b.addEventListener("click", function () { var d = document.getElementById(b.getAttribute("data-open-dialog")); if (d && d.showModal) d.showModal(); });
  });
  $$("dialog").forEach(function (d) {
    $$("[data-close-dialog]", d).forEach(function (b) { b.addEventListener("click", function () { d.close(); }); });
    d.addEventListener("click", function (e) { if (e.target === d) d.close(); });
  });

  /* Sabit metinler: arama ve varsayılana dönme */
  var snippetSearch = $("[data-snippet-search]");
  if (snippetSearch) snippetSearch.addEventListener("input", function () {
    var q = snippetSearch.value.toLocaleLowerCase("tr").trim();
    $$("[data-snippet-group]").forEach(function (g) {
      var visible = 0;
      $$("[data-snippet]", g).forEach(function (s) {
        var hit = !q || s.getAttribute("data-search").indexOf(q) > -1;
        s.classList.toggle("is-hidden", !hit);
        if (hit) visible++;
      });
      g.classList.toggle("is-hidden", visible === 0);
    });
  });
  $$("[data-snippet-reset]").forEach(function (b) {
    b.addEventListener("click", function () {
      var input = $(".input", b.closest("[data-snippet]"));
      input.value = input.getAttribute("data-default");
      markDirty(input);
    });
  });

  /* Kaydedilmemiş değişiklik uyarısı */
  var dirty = false;
  function markDirty(el) { if (el && el.closest && el.closest("form[data-unsaved]")) dirty = true; }
  $$("form[data-unsaved]").forEach(function (form) {
    form.addEventListener("input", function () { dirty = true; });
    form.addEventListener("change", function () { dirty = true; });
    form.addEventListener("submit", function () { dirty = false; });
  });
  window.addEventListener("beforeunload", function (e) { if (dirty) { e.preventDefault(); e.returnValue = ""; } });
})();
