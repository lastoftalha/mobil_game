/* Bitasarımlazım — ön yüz etkileşimleri (bağımlılıksız) */
(function () {
  "use strict";

  var doc = document.documentElement;
  doc.classList.remove("no-js");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function storageGet(key) { try { return window.localStorage.getItem(key); } catch (e) { return null; } }
  function storageSet(key, val) { try { window.localStorage.setItem(key, val); } catch (e) { /* yoksay */ } }

  /* Header: kaydırınca küçül */
  var header = $(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 40); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* Mobil menü */
  var burger = $(".burger");
  var mobileMenu = $("#mobile-menu");
  if (burger && mobileMenu) {
    var setMenu = function (open) {
      document.body.classList.toggle("menu-open", open);
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      mobileMenu.setAttribute("aria-hidden", open ? "false" : "true");
    };
    burger.addEventListener("click", function () { setMenu(!document.body.classList.contains("menu-open")); });
    $$("a", mobileMenu).forEach(function (a) { a.addEventListener("click", function () { setMenu(false); }); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });
    window.addEventListener("resize", function () { if (window.innerWidth > 1080) setMenu(false); });
  }

  /* Görünür olunca animasyon */
  var revealEls = $$(".reveal, .split-line, .step, [data-count]");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        if (entry.target.hasAttribute("data-count")) countUp(entry.target);
        io.unobserve(entry.target);
      });
    }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* Sayaç: "600+", "4,8/5", "%80" gibi değerlerdeki ilk sayıyı sayar */
  function countUp(el) {
    var raw = el.getAttribute("data-count") || el.textContent;
    var m = raw.match(/(\d+(?:[.,]\d+)?)/);
    if (!m) return;
    var target = parseFloat(m[1].replace(",", "."));
    var decimals = (m[1].split(/[.,]/)[1] || "").length;
    var sep = m[1].indexOf(",") > -1 ? "," : ".";
    var prefix = raw.slice(0, m.index), suffix = raw.slice(m.index + m[1].length);
    var start = null, dur = 1600;
    function frame(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      var val = (target * eased).toFixed(decimals).replace(".", sep);
      el.textContent = prefix + val + suffix;
      if (p < 1) window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);
  }

  /* Hero slaytları */
  $$(".hero-slides").forEach(function (wrap) {
    var slides = $$(".slide", wrap);
    var bars = $$(".hero-slides__bars i", wrap);
    var caption = $(".hero-slides__text", wrap);
    if (slides.length < 2) return;
    var i = 0;
    setInterval(function () {
      slides[i].classList.remove("is-active");
      if (bars[i]) bars[i].classList.remove("is-active");
      i = (i + 1) % slides.length;
      slides[i].classList.add("is-active");
      if (bars[i]) bars[i].classList.add("is-active");
      if (caption) caption.textContent = slides[i].getAttribute("data-caption") || "";
    }, 4200);
  });

  /* Dönen kelimeler (hizmetler) */
  $$("[data-wheel]").forEach(function (root) {
    var words = $$(".wheel__word", root);
    var panels = $$(".capabilities__panel [data-index]", root);
    var dots = $$(".capabilities__dots button", root);
    if (!words.length) return;
    var n = words.length, current = 0, timer = null;
    function cls(idx) {
      var d = (idx - current + n) % n;
      if (d === 0) return "is-active";
      if (d === 1) return "is-next";
      if (d === n - 1) return "is-prev";
      if (d === 2 && n > 4) return "is-next2";
      if (d === n - 2 && n > 4) return "is-prev2";
      return "";
    }
    function render() {
      words.forEach(function (w, idx) {
        w.className = "wheel__word " + cls(idx);
        w.setAttribute("aria-hidden", idx === current ? "false" : "true");
      });
      panels.forEach(function (p) { p.hidden = +p.getAttribute("data-index") !== current; });
      dots.forEach(function (d, idx) { d.classList.toggle("is-active", idx === current); });
    }
    function go(idx) { current = (idx + n) % n; render(); }
    function play() { stop(); if (!reduceMotion) timer = setInterval(function () { go(current + 1); }, 2800); }
    function stop() { if (timer) clearInterval(timer); timer = null; }
    words.forEach(function (w, idx) { w.addEventListener("click", function () { go(idx); play(); }); });
    dots.forEach(function (d, idx) { d.addEventListener("click", function () { go(idx); play(); }); });
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", play);
    render();
    play();
  });

  /* Yatay kaydırıcı butonları */
  $$("[data-slider]").forEach(function (root) {
    var track = $(".slider__track", root);
    if (!track) return;
    function step() { var c = track.children[0]; return c ? c.getBoundingClientRect().width + 20 : 300; }
    $$("[data-slide]", root).forEach(function (btn) {
      btn.addEventListener("click", function () {
        track.scrollBy({ left: step() * (+btn.getAttribute("data-slide")), behavior: reduceMotion ? "auto" : "smooth" });
      });
    });
  });

  /* Filtreler (portföy, galeri) */
  $$("[data-filter-group]").forEach(function (root) {
    var chips = $$("[data-filter]", root);
    var items = $$("[data-cat]", root);
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var f = chip.getAttribute("data-filter");
        chips.forEach(function (c) { c.classList.toggle("is-active", c === chip); c.setAttribute("aria-pressed", c === chip ? "true" : "false"); });
        items.forEach(function (it) { it.classList.toggle("is-hidden", f !== "*" && it.getAttribute("data-cat") !== f); });
      });
    });
  });

  /* Lightbox */
  var lightbox = null;
  function buildLightbox() {
    lightbox = document.createElement("div");
    lightbox.className = "lightbox";
    lightbox.setAttribute("role", "dialog");
    lightbox.setAttribute("aria-modal", "true");
    lightbox.innerHTML =
      '<button class="lightbox__btn lightbox__close" aria-label="Kapat"><svg class="ico"><use href="#i-x"/></svg></button>' +
      '<button class="lightbox__btn lightbox__prev" aria-label="Önceki"><svg class="ico"><use href="#i-chevron-left"/></svg></button>' +
      '<figure><img alt=""><figcaption class="lightbox__cap"></figcaption></figure>' +
      '<button class="lightbox__btn lightbox__next" aria-label="Sonraki"><svg class="ico"><use href="#i-chevron-right"/></svg></button>';
    document.body.appendChild(lightbox);
    return lightbox;
  }
  $$("[data-lightbox]").forEach(function (group) {
    group.addEventListener("click", function (e) {
      var link = e.target.closest("a[data-full]");
      if (!link) return;
      e.preventDefault();
      var links = $$("a[data-full]", group).filter(function (a) { return !a.closest(".is-hidden"); });
      var idx = links.indexOf(link);
      var lb = lightbox || buildLightbox();
      var img = $("img", lb), cap = $(".lightbox__cap", lb);
      function show(i) {
        idx = (i + links.length) % links.length;
        img.src = links[idx].getAttribute("data-full");
        img.alt = links[idx].getAttribute("data-caption") || "";
        cap.textContent = links[idx].getAttribute("data-caption") || "";
      }
      function close() { lb.classList.remove("is-open"); document.removeEventListener("keydown", onKey); link.focus(); }
      function onKey(ev) {
        if (ev.key === "Escape") close();
        if (ev.key === "ArrowRight") show(idx + 1);
        if (ev.key === "ArrowLeft") show(idx - 1);
      }
      $(".lightbox__close", lb).onclick = close;
      $(".lightbox__next", lb).onclick = function () { show(idx + 1); };
      $(".lightbox__prev", lb).onclick = function () { show(idx - 1); };
      lb.onclick = function (ev) { if (ev.target === lb) close(); };
      document.addEventListener("keydown", onKey);
      show(idx);
      lb.classList.add("is-open");
      $(".lightbox__close", lb).focus();
    });
  });

  /* Hizmet satırlarında imleci takip eden görsel */
  var rows = $$("[data-preview]");
  if (rows.length && window.matchMedia("(hover: hover)").matches) {
    var preview = document.createElement("div");
    preview.className = "hover-preview";
    preview.innerHTML = "<img alt=''>";
    document.body.appendChild(preview);
    var pimg = $("img", preview);
    rows.forEach(function (row) {
      row.addEventListener("mouseenter", function () {
        var src = row.getAttribute("data-preview");
        if (!src) return;
        pimg.src = src;
        preview.classList.add("is-on");
      });
      row.addEventListener("mouseleave", function () { preview.classList.remove("is-on"); });
      row.addEventListener("mousemove", function (e) {
        preview.style.left = e.clientX + 170 + "px";
        preview.style.top = e.clientY + "px";
      });
    });
  }

  /* Görsel bandı paralaks */
  var bands = $$(".image-band [data-parallax]");
  if (bands.length && !reduceMotion) {
    var ticking = false;
    var update = function () {
      bands.forEach(function (el) {
        var r = el.parentElement.getBoundingClientRect();
        var p = (r.top + r.height / 2 - window.innerHeight / 2) / window.innerHeight;
        p = Math.max(-1, Math.min(1, p));
        el.style.transform = "translateY(" + (p * -8).toFixed(2) + "%)";
      });
      ticking = false;
    };
    window.addEventListener("scroll", function () { if (!ticking) { ticking = true; window.requestAnimationFrame(update); } }, { passive: true });
    update();
  }

  /* Video oynat/durdur */
  $$("[data-video-toggle]").forEach(function (btn) {
    var video = btn.parentElement.querySelector("video");
    if (!video) return;
    btn.addEventListener("click", function () {
      if (video.paused) { video.play(); btn.classList.remove("is-paused"); } else { video.pause(); btn.classList.add("is-paused"); }
    });
  });

  /* Bildirimler */
  $$(".toast").forEach(function (t) {
    var btn = $("button", t);
    var hide = function () { t.style.transition = "opacity .3s"; t.style.opacity = "0"; setTimeout(function () { t.remove(); }, 300); };
    if (btn) btn.addEventListener("click", hide);
    setTimeout(hide, 7000);
  });

  /* Çerez bandı */
  var cookieBar = $(".cookie-bar");
  if (cookieBar && storageGet("cookie-ok") !== "1") {
    setTimeout(function () { cookieBar.classList.add("is-visible"); document.body.classList.add("cookie-visible"); }, 800);
    $("[data-cookie-ok]", cookieBar).addEventListener("click", function () {
      storageSet("cookie-ok", "1");
      cookieBar.classList.remove("is-visible");
      document.body.classList.remove("cookie-visible");
    });
  }
})();
