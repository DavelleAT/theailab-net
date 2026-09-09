// "You are here" marker for the homepage course arc.
//
// Scoped to index.html, the only page carrying the arc. Week and break dates
// come from the shared window.CourseCalendar (js/course-calendar.js) so this
// file holds no calendar data of its own. The "This Week" rail card that used
// to be populated from here is handled sitewide by js/this-week-card.js.
//
// Phase 4 (2026-09-09): the arc is a week index rather than the original SVG
// dot path, so marking the current week is a class and a label on one row
// instead of positioning a circle in SVG coordinate space.

(function () {
  function mark(row, text) {
    row.classList.add("is-current");
    var tag = document.createElement("span");
    tag.className = "arc-here";
    tag.textContent = text;
    // Ahead of the phase tag, so the row reads number, title, marker, phase.
    row.insertBefore(tag, row.querySelector(".arc-phase"));
  }

  function init() {
    var arc = document.getElementById("journey-map");
    var CC = window.CourseCalendar;
    if (!arc || !CC) return;

    var todayStr = CC.today();
    var wk = CC.currentWeekNumber(todayStr);
    if (!wk) return; // semester hasn't started yet

    // During a recess there is no current week to stand in, so the marker
    // points at the week the course resumes on instead.
    var brk = CC.activeBreak(todayStr);
    var target = brk ? (wk + 1 <= 15 ? wk + 1 : null) : wk;
    if (!target) return;

    var row = arc.querySelector('.arc-week[data-week="' + target + '"]');
    if (!row) return;

    mark(row, brk ? "Next up" : "You are here");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
