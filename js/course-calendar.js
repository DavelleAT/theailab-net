// Shared course-calendar data: week start dates, recess ranges, and week
// titles. Used by journey-map.js (homepage map) and this-week-card.js
// (sitewide "This Week" rail card) so there is exactly one copy of this
// data, not one per consumer. Keep in sync with weeks/week-NN.html and the
// official Kenyon academic calendar — this will silently go stale otherwise.
(function () {
  var WEEK_START_DATES = [
    "2026-08-27", // Week 1
    "2026-09-01", // Week 2
    "2026-09-08", // Week 3
    "2026-09-15", // Week 4
    "2026-09-22", // Week 5
    "2026-09-29", // Week 6
    "2026-10-06", // Week 7 (single session, October Break)
    "2026-10-13", // Week 8
    "2026-10-20", // Week 9
    "2026-10-27", // Week 10
    "2026-11-03", // Week 11
    "2026-11-10", // Week 12
    "2026-11-17", // Week 13
    "2026-12-01", // Week 14 (after Thanksgiving Recess)
    "2026-12-08"  // Week 15
  ];

  var WEEK_TITLES = [
    "Course Introduction",
    "Shell Fundamentals and Dotfiles",
    "Dive into Claude Code CLI",
    "CLAUDE.md and Slash Commands",
    "Agent Skills, Subagents, and MCP",
    "Hooks Architecture and Guardrails",
    "Multi-Agent Orchestration Fundamentals",
    "Comparative Agent Harnesses",
    "Harness Integration and Debugging",
    "MP3 Demos and the Spec-Driven Development Landscape",
    "GitHub as the AI-SDLC Hub",
    "Observability, Cost, and Security",
    "Full-Cycle Capstone Work Session and MP4 Presentations",
    "Final Project Work Session and Poster Development",
    "Final Project Poster Presentations"
  ];

  var BREAKS = [
    { start: "2026-10-08", end: "2026-10-09", name: "October Break" },
    { start: "2026-11-21", end: "2026-11-29", name: "Thanksgiving Recess" }
  ];

  var ETHICS_WEEKS = [3, 8, 12];

  function currentWeekNumber(dateStr) {
    if (dateStr < WEEK_START_DATES[0]) return null;
    var week = null;
    for (var i = 0; i < WEEK_START_DATES.length; i++) {
      if (dateStr >= WEEK_START_DATES[i]) week = i + 1;
    }
    return week;
  }

  function activeBreak(dateStr) {
    for (var i = 0; i < BREAKS.length; i++) {
      if (dateStr >= BREAKS[i].start && dateStr <= BREAKS[i].end) return BREAKS[i];
    }
    return null;
  }

  function weekTitle(wk) {
    return WEEK_TITLES[wk - 1] || "";
  }

  window.CourseCalendar = {
    WEEK_START_DATES: WEEK_START_DATES,
    ETHICS_WEEKS: ETHICS_WEEKS,
    currentWeekNumber: currentWeekNumber,
    activeBreak: activeBreak,
    weekTitle: weekTitle,
    today: function () { return new Date().toISOString().slice(0, 10); }
  };
})();
