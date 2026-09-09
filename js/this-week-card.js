// "This Week" rail card — sitewide (all 22 pages). Uses the shared
// window.CourseCalendar (js/course-calendar.js) so week dates/titles have
// exactly one source of truth, whether or not the page has the homepage's
// journey map. See docs/design-spec_phase3_website-revision_v1_20260903.md
// Part 2.5.
(function () {
  function render(card, opts) {
    if (!opts) {
      card.hidden = true;
      card.innerHTML = "";
      return;
    }
    card.hidden = false;
    if (opts.onBreak) {
      card.innerHTML =
        '<div class="here-week">On break</div>' +
        '<div class="here-title">' + opts.breakName + "</div>" +
        (opts.nextWeek
          ? '<a class="here-link" href="' + opts.prefix + 'weeks/week-' +
            String(opts.nextWeek).padStart(2, "0") + '.html">Go to Week ' + opts.nextWeek + "</a>"
          : "");
    } else {
      var pct = Math.round((opts.week / 15) * 100);
      card.innerHTML =
        '<div class="here-week">Week ' + opts.week + " of 15</div>" +
        '<div class="here-title">' + opts.title + "</div>" +
        '<div class="here-bar"><div class="here-bar-fill" style="width:' + pct + '%"></div></div>' +
        '<a class="here-link" href="' + opts.prefix + 'weeks/week-' +
        String(opts.week).padStart(2, "0") + '.html">Go to this week</a>';
    }
  }

  function init() {
    var card = document.getElementById("here-card");
    var CC = window.CourseCalendar;
    if (!card || !CC) return;

    // Pages inside core/ or weeks/ link to weeks/ as "../weeks/...";
    // index.html links to it directly as "weeks/...".
    var prefix = location.pathname.indexOf("/core/") !== -1 || location.pathname.indexOf("/weeks/") !== -1
      ? "../"
      : "";

    var todayStr = CC.today();
    var wk = CC.currentWeekNumber(todayStr);
    if (!wk) {
      render(card, null); // semester hasn't started yet
      return;
    }

    var brk = CC.activeBreak(todayStr);
    if (brk) {
      var nextWk = wk + 1 <= 15 ? wk + 1 : null;
      render(card, { onBreak: true, breakName: brk.name, nextWeek: nextWk, prefix: prefix });
    } else {
      render(card, { week: wk, title: CC.weekTitle(wk), prefix: prefix });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
