/* Dark mode (P3-1): resolves and applies the theme before paint. Loaded
   synchronously in <head>, before css/style.css, on every page. Exposes
   window.__theme so js/theme.js can wire up the toggle/lock buttons without
   duplicating this logic. Boundaries are fixed at 7am/7pm local time. */
(function () {
  var KEY = "theme-pref";

  function dayBoundaries(base) {
    var out = [];
    for (var offset = -1; offset <= 1; offset++) {
      var d = new Date(base.getFullYear(), base.getMonth(), base.getDate() + offset);
      out.push(new Date(d.getFullYear(), d.getMonth(), d.getDate(), 7, 0, 0, 0).getTime());
      out.push(new Date(d.getFullYear(), d.getMonth(), d.getDate(), 19, 0, 0, 0).getTime());
    }
    return out.sort(function (a, b) { return a - b; });
  }

  function nextTwoBoundaries(now) {
    var t = now.getTime();
    var future = dayBoundaries(now).filter(function (ts) { return ts > t; });
    return [future[0], future[1]];
  }

  function autoTheme(now) {
    var h = now.getHours();
    return (h >= 19 || h < 7) ? "dark" : "light";
  }

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function save(pref) {
    try {
      if (pref === null) localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, JSON.stringify(pref));
    } catch (e) {
      /* storage unavailable (private mode, etc.) — theme just won't persist */
    }
  }

  function resolve() {
    var now = new Date();
    var pref = load();
    if (pref) {
      if (pref.locked) return pref.theme;
      if (now.getTime() < pref.expiresAt) return pref.theme;
      save(null); // override expired at the second boundary crossing — back to auto
    }
    return autoTheme(now);
  }

  function apply(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }

  apply(resolve());

  /* Scroll-reveal gate (Phase 4). Set here rather than in js/motion.js because
     motion.js runs at the end of <body>: by then the page has painted, so
     adding the class there would show every block and then hide it again to
     animate in. Gating on IntersectionObserver support and the reduced-motion
     preference means the class is only ever present when the reveals can
     actually run — otherwise the CSS leaves everything in its final state. */
  try {
    if (window.IntersectionObserver &&
        !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.documentElement.classList.add("js-motion");
    }
  } catch (e) {
    /* no matchMedia — skip reveals, content renders unanimated */
  }

  window.__theme = {
    load: load,
    save: save,
    autoTheme: autoTheme,
    nextTwoBoundaries: nextTwoBoundaries,
    resolve: resolve,
    apply: apply
  };
})();
