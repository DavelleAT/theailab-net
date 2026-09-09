/* Scroll-reveal and header motion (Phase 4).
 *
 * Targets are selected here rather than marked up by hand in all 22 pages, so
 * the motion layer stays in one file and page templates carry no animation
 * attributes. The paired CSS lives under "Motion" in css/style.css and is
 * gated behind .js-motion on <html>, which js/theme-init.js sets before first
 * paint when IntersectionObserver exists and the visitor has not asked for
 * reduced motion. If that class is absent, every rule here is inert and the
 * page renders in its finished state.
 */
(function () {
  var root = document.documentElement;
  if (!root.classList.contains("js-motion")) return;

  /* Blocks that rise into view. Order is irrelevant; the stagger is computed
     per parent below, so siblings cascade and unrelated regions do not. */
  var SELECTORS = [
    ".home-lead",
    ".arc-band",
    ".arc-list li",
    ".week-progress",
    ".session-meta",
    ".content-section",
    ".ethics-thread",
    ".week-nav",
    ".news-card",
    ".here-card",
    ".section",
    ".page-content > h2",
    ".page-content > h3",
    ".page-content > p",
    ".page-content > .table-wrap",
    ".item-list li"
  ];

  /* Past this many siblings the stagger stops accumulating — a 20th child would
     otherwise sit on a delay long enough to read as broken rather than staged. */
  var MAX_STAGGER = 12;

  function tag() {
    var counters = [];
    var parents = [];

    SELECTORS.forEach(function (sel) {
      var nodes = document.querySelectorAll(sel);
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        if (el.hasAttribute("data-reveal")) continue;

        var parent = el.parentNode;
        var idx = parents.indexOf(parent);
        if (idx === -1) {
          parents.push(parent);
          counters.push(0);
          idx = parents.length - 1;
        }

        var step = counters[idx];
        counters[idx] = step + 1;

        el.setAttribute("data-reveal", "");
        el.style.setProperty("--i", Math.min(step, MAX_STAGGER));
      }
    });
  }

  function reveal(el) {
    el.classList.add("is-visible");
    el.addEventListener("transitionend", function onDone(e) {
      if (e.target !== el || e.propertyName !== "opacity") return;
      el.classList.add("is-settled");
      el.removeEventListener("transitionend", onDone);
    });
  }

  function observeReveals() {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        reveal(entry.target);
        io.unobserve(entry.target);
      });
    }, {
      /* Negative bottom margin holds the reveal until the block is properly in
         the viewport rather than firing on the first pixel to cross the edge. */
      rootMargin: "0px 0px -10% 0px",
      threshold: 0.01
    });

    var targets = document.querySelectorAll("[data-reveal]");
    for (var i = 0; i < targets.length; i++) io.observe(targets[i]);
  }

  /* The progress bar and the phase band scale rather than fade, so they key off
     .is-visible on their own container instead of [data-reveal]. */
  function observeBars() {
    var bars = document.querySelectorAll(".week-progress, .arc-band");
    if (!bars.length) return;

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        io.unobserve(entry.target);
      });
    }, { threshold: 0.25 });

    for (var i = 0; i < bars.length; i++) io.observe(bars[i]);
  }

  function heroIn() {
    var h1 = document.querySelector(".hero h1");
    if (!h1) return;
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        h1.classList.add("is-visible");
      });
    });
  }

  /* Header gains its border and blur once the page has moved at all. Reads
     through rAF so a fast scroll does not queue a class write per event. */
  function stickyHeader() {
    var header = document.querySelector(".site-header");
    if (!header) return;
    var ticking = false;

    function update() {
      header.classList.toggle("is-scrolled", window.scrollY > 12);
      ticking = false;
    }

    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }, { passive: true });

    update();
  }

  function init() {
    try {
      tag();
      observeReveals();
      observeBars();
      heroIn();
      stickyHeader();
    } catch (e) {
      /* Never leave content stranded at opacity 0 because the motion layer
         broke. Dropping the class restores the unanimated rendering. */
      root.classList.remove("js-motion");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
