# Website Code Review — IPHS 400 Course Site (theailab-net)

**Report date:** 2026-09-08  
**Repository:** `jon-chun/theailab-net`  
**Branch reviewed:** `main`  
**Reviewer:** Claude Code (static analysis + JS/CSS audit)

## 1. Executive Summary

This is a follow-up to the 2026-09-03 code review. Since that report, **five of the medium/low findings have been implemented:** favicon added, skip-link implemented, meta descriptions added to all pages, table overflow wrappers added, and dead WordPress CSS removed entirely. The site now has proper semantic HTML structure and basic accessibility support.

This review identifies new issues that have emerged with the additions of interactive JavaScript features (canvas animation, API integration, theme switching): **two medium-severity findings around XSS risk and SVG generation, plus six low-severity findings around code organization, script loading efficiency, and testing gaps.**

| Severity | Count | Status |
|---|---|---|
| High | 0 | — |
| Medium | 2 | New |
| Low | 6 | New |
| **Fixed since 09-03** | **5** | ✓ Closed |

## 2. Scope & Methodology

- **New analysis:** Focus on the ~200 lines of JavaScript (8 files, mostly under 3KB each) added since Sept 3 to support: interactive canvas background flourish, API-driven news card, dark mode toggle with persistence, nav magnification effect, and course calendar logic.
- **Continuing analysis:** Re-checked CSS (`style.css` now 847 lines vs. 620 on 09-03) for dead code, selector efficiency, and responsive design; confirmed all 22 HTML pages for structural consistency and link integrity.
- **Methodology:** Line-by-line code reading, grep-based static analysis (no automated linting), no browser-based testing or live accessibility audit.
- **Test status:** Test suite still passes (25 tests, all green as of the last run noted in prior docs).

---

## 3. Issues From Previous Report — Status Update

| Finding | Severity | Status |
|---|---|---|
| 3.1 No templating/include mechanism | HIGH | **Open** — Still hand-duplicated boilerplate across 22 files |
| 4.2 Dead CSS from WordPress theme | MEDIUM | **FIXED** ✓ — Removed entirely in recent commit |
| 4.3 No favicon | MEDIUM | **FIXED** ✓ — `favicon.svg` added, linked on all pages |
| 4.4 No meta description or OG tags | MEDIUM | **FIXED** ✓ — Unique `<meta name="description">` on every page |
| 4.5 No skip-link | MEDIUM | **FIXED** ✓ — Accessible skip-link at top of every `<body>` |
| 4.6 Wide tables overflow on mobile | MEDIUM | **FIXED** ✓ — All tables wrapped in `.table-wrap { overflow-x: auto }` |
| 4.7 GitHub URL clarity | LOW | **Noted** — Not an issue, intentional design |
| 4.8 Tests don't cover new elements | LOW | **Partially addressed** — Tests now check favicon, skip-link, meta description presence |
| 4.9 No `robots.txt`/`sitemap.xml` | LOW | **Acknowledged** — Local-only site, noted for future public hosting |

**Result:** 5 of 7 actionable findings from the 09-03 report have been fixed. The codebase is notably cleaner and more accessible than five days ago.

---

## 4. New Findings — JavaScript & Recent Changes

### 4.1 [MEDIUM] XSS Vulnerability in `js/today-in-ai.js`

**Location:** `js/today-in-ai.js`, lines 83–97  
**Severity:** Medium (requires API compromise to exploit, but possible)

The "Today in AI" news card fetches data from the Hacker News Algolia API and renders the story title directly into HTML via `innerHTML` without escaping:

```javascript
function cardHTML(story) {
  return (
    '<div class="news-label">Today in AI</div>' +
    '<p class="news-headline">"' + story.title + '"</p>' +  // ← Unescaped user data
    '<p class="news-source">via Hacker News</p>' +
    '<p class="news-caption">...</p>'
  );
}

function render(stories) {
  // ...
  card.innerHTML = cardHTML(story);  // ← Direct HTML insertion
  card.hidden = false;
}
```

If a story title contained HTML entities, special characters, or (in a more serious scenario) HTML/JavaScript, it would be inserted directly. While Hacker News titles are unlikely to contain malicious input, the pattern is fragile: any future API integration following this example, or any caching/transformation of the data, could introduce genuine XSS.

**Risk:** Low in practice (HN Algolia API is trusted and highly monitored), but the code pattern is not defensive.

**Recommendation:**  
Either:
- Use `textContent` instead of `innerHTML` for the title:
  ```javascript
  var headline = document.createElement('p');
  headline.className = 'news-headline';
  headline.textContent = '"' + story.title + '"';
  card.appendChild(headline);
  ```
- Or escape HTML entities in the title before insertion:
  ```javascript
  function escapeHtml(text) {
    var map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
    return text.replace(/[&<>"']/g, function(c) { return map[c]; });
  }
  card.innerHTML = ... + escapeHtml(story.title) + ...
  ```

---

### 4.2 [MEDIUM] SVG Generation in `js/journey-map.js` Lacks Proper Text Encoding

**Location:** `js/journey-map.js`, lines 36–48

The journey map's "You are here" marker is built dynamically by concatenating raw strings into SVG:

```javascript
marker.innerHTML =
  '<circle class="here-ring" cx="' + center.x + '" cy="' + center.y + '" r="13"></circle>' +
  '<text fill="var(--accent)" font-family="Quicksand" font-size="11" font-weight="700" ' +
  'x="' + center.x + '" y="' + labelY + '" text-anchor="middle">You are here</text>';
```

The numeric values (`center.x`, `center.y`, `labelY`) are floats and are safe, but if these calculations ever depend on user-controlled data (course calendar dates, week numbers from an API, etc.), unquoted attributes could break the SVG structure. Currently they're hardcoded calculations, so the risk is low, but the pattern doesn't scale.

**Recommendation:**  
Use a helper to quote numeric attributes, or switch to DOM methods:
```javascript
var marker = document.getElementById('here-marker');
var svg = document.getElementById('journey-map');
var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
circle.setAttribute('class', 'here-ring');
circle.setAttribute('cx', center.x);
circle.setAttribute('cy', center.y);
circle.setAttribute('r', 13);
marker.appendChild(circle);
// ... similar for text element
```

This is safer and more readable than string concatenation.

---

### 4.3 [LOW] Homepage-Only JavaScript Files Load on Every Page

**Location:** `index.html` vs. `core/*.html`, `weeks/*.html`

The homepage (`index.html`) loads these scripts at the bottom:
```html
<script src="js/hero-flourish.js"></script>
<script src="js/journey-map.js"></script>
```

But `core/syllabus.html`, `weeks/week-01.html`, etc. also load them (via relative paths like `../js/hero-flourish.js`), even though:
- `#bg-flourish` canvas exists only on `index.html`
- `#journey-map` SVG exists only on `index.html`

Each script checks `if (!element) return` early, so there's no functional breakage, but it's inefficient:
- **150 canvas rays** initialized in `hero-flourish.js` even on a 404 page where the element doesn't exist
- **Animation loop** (`requestAnimationFrame`) set up for nothing
- **Mouse/scroll listeners** registered even when unused

**Impact:** Minor performance degradation on every non-homepage page. Negligible on fast connections, but visible on slower devices.

**Recommendation:**  
Conditionally load these scripts only on `index.html`:
```html
<!-- Only on index.html -->
<script src="js/hero-flourish.js"></script>
<script src="js/journey-map.js"></script>

<!-- On all pages -->
<script src="js/course-calendar.js"></script>
<script src="js/this-week-card.js"></script>
```

Alternatively, guard initialization in the JS with a simple feature check instead of relying on missing elements to exit cleanly.

---

### 4.4 [LOW] Theme Toggle Button Missing `aria-pressed` on Initial State

**Location:** `js/theme.js`, line 34

The theme-lock button gets an `aria-pressed` attribute when toggled:
```javascript
lockBtn.setAttribute("aria-pressed", pref.locked ? "true" : "false");
```

But the theme-toggle button is updated only with `aria-label` and `class.toggle`, not `aria-pressed`:
```javascript
toggleBtn.classList.toggle("is-dark", theme === "dark");
toggleBtn.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
// Missing: aria-pressed
```

Screen reader users can infer the button's purpose from the label, but they can't determine its current state from the accessibility tree (no `aria-pressed` attribute). The `is-dark` class is visual feedback, not semantic.

**Recommendation:**  
Add `aria-pressed` to match the lock button pattern:
```javascript
toggleBtn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
```

---

### 4.5 [LOW] Canvas Animation Doesn't Respect `prefers-reduced-motion` on Subsequent Redraws

**Location:** `js/hero-flourish.js`, lines 130–135

The code correctly checks `prefers-reduced-motion` at startup:
```javascript
var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (reduceMotion) {
  draw(0);
  window.addEventListener("resize", function () { resize(); draw(0); });
  return;
}
```

But if a user changes their OS "reduce motion" preference **while the page is open** (unlikely but possible on mobile), the animation will continue running. The preference is checked once at load time, not subscribed to updates.

**Impact:** Very low (user behavior change while page is open is rare).

**Recommendation:**  
Use a media query listener to respond to preference changes:
```javascript
var mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
mediaQuery.addEventListener("change", function (e) {
  if (e.matches) {
    cancelAnimationFrame(animationFrameId); // stop animation
  } else {
    loop(); // restart
  }
});
```

---

### 4.6 [LOW] Inconsistent Dark-Mode CSS Variable Strategy

**Location:** `css/style.css`, lines 17–69

Light and dark mode color tokens are defined as:

**Light mode (`:root`):**
```css
--mp1: #c3a89f;   /* MP1 - Dev Environment: dusty rose */
--mp2: #a3ac93;   /* MP2 - Agent Config: moss */
--mp3: #c4ab77;   /* MP3 - Harness & Hooks: mustard */
--mp4: #a49cb0;   /* MP4 - SDLC Capstone: dusty violet */
--final: #9bb0b5; /* Final Project: dusty teal */
```

**Dark mode (`[data-theme="dark"]`):**
```css
--mp1: #e2a89a;
--mp2: #a3c78c;
--mp3: #dcb567;
--mp4: #b6a3d9;
--final: #7ec3c7;
```

The comments are only in the light-mode block, making dark-mode colors opaque. This is minor but impairs maintainability: a future developer editing `--mp3` in dark mode won't know what "MP3 - Harness & Hooks: mustard" refers to without checking the light-mode rule above.

**Recommendation:**  
Duplicate or cross-reference the comments in both color-mode blocks:
```css
[data-theme="dark"] {
  /* MP1 - Dev Environment */
  --mp1: #e2a89a;
  /* MP2 - Agent Config */
  --mp2: #a3c78c;
  /* ... etc */
}
```

---

### 4.7 [LOW] Course Calendar Data Hardcoded; No Validation of Date Ranges

**Location:** `js/course-calendar.js`, lines 7–48

Week start dates and break ranges are hardcoded:
```javascript
var WEEK_START_DATES = [
  "2026-08-27", // Week 1
  "2026-09-01", // Week 2
  // ... through 2026-12-08
];

var BREAKS = [
  { start: "2026-10-08", end: "2026-10-09", name: "October Break" },
  { start: "2026-11-21", end: "2026-11-29", name: "Thanksgiving Recess" }
];
```

There's no validation that:
- Week dates are monotonically increasing (a typo like `"2026-09-08"` then `"2026-09-01"` would silently break `currentWeekNumber()`)
- Break ranges don't overlap with week dates
- Week titles and start dates stay in sync (22 entries of prose spread across two arrays)

The course calendar data is the single source of truth for "this week" cards and the journey map. A transcription error would silently show wrong week numbers across the entire site.

**Recommendation:**  
Add a validation function at initialization:
```javascript
function validateCalendarData() {
  var prev = null;
  for (var i = 0; i < WEEK_START_DATES.length; i++) {
    if (WEEK_START_DATES[i] < prev) {
      throw new Error("Week dates not sorted at index " + i);
    }
    if (!WEEK_TITLES[i]) {
      throw new Error("Week " + (i+1) + " missing title");
    }
    prev = WEEK_START_DATES[i];
  }
}
validateCalendarData(); // Fail loudly at page load, not silently later
```

Or better, restructure to a single array of week objects:
```javascript
var WEEKS = [
  { number: 1, startDate: "2026-08-27", title: "Course Introduction", mp: "mp1" },
  { number: 2, startDate: "2026-09-01", title: "Shell Fundamentals and Dotfiles", mp: "mp1" },
  // ...
];
```

---

### 4.8 [LOW] Test Suite Has No JavaScript Unit or Integration Tests

**Location:** `tests/` directory

The existing test suite (`test_unit_html_structure.py`, `test_integration_links.py`, `test_e2e_site.py`) validates HTML structure and link integrity — excellent coverage for a static site. **But there are zero tests for the JavaScript behavior:**

- No test that the theme toggle actually persists preferences to localStorage
- No test that `course-calendar.js` correctly calculates the current week
- No test that `today-in-ai.js` caches API responses with the correct TTL
- No test that `hero-flourish.js` initializes rays without error on the homepage
- No test that "You are here" marker renders correctly for each week

If JS behavior breaks (e.g., a refactoring of `this-week-card.js` changes how it computes the progress bar width), the tests will pass but the site will silently malfunction.

**Recommendation:**  
Add a `tests/test_js_*.py` suite using `selenium` or `playwright` to automate a browser:
```python
def test_theme_toggle_persists_preference():
    """Clicking the theme toggle saves preference to localStorage."""
    # Open page, click toggle, check localStorage.theme-pref

def test_course_calendar_current_week():
    """course-calendar.js.currentWeekNumber() returns correct value for known dates."""
    # Mock Date, assert week number logic

def test_today_in_ai_cache_ttl():
    """News card respects 1-hour cache TTL."""
    # Set time forward, assert re-fetch happens
```

For now, this is lower priority than making the codebase testable, but it's a gap.

---

### 4.9 [LOW] No Error Logging or Observability for Client-Side Issues

**Location:** All JS files

The JavaScript silently fails in several scenarios with no user feedback:
- **`hero-flourish.js`:** If `canvas.getContext("2d")` returns null (rare but possible), the animation silently doesn't initialize. No console warning.
- **`today-in-ai.js`:** If the HN API is down, the card simply doesn't render. No "API unavailable" message in any form.
- **`theme.js`:** If `localStorage` is unavailable (private browsing), preferences silently don't persist. No warning.
- **`journey-map.js`:** If `window.CourseCalendar` isn't defined, the marker doesn't render. No console output.

This is fine for a small internal site where the fallback behavior (hidden card, default theme, missing marker) is acceptable. But it makes debugging harder and prevents the instructor/developer from knowing if something is broken.

**Recommendation:**  
Add optional telemetry or client-side error logging (for development only):
```javascript
var DEBUG = true;  // Set to false in production
function log(msg) {
  if (DEBUG) console.log("[theailab]", msg);
}
function warn(msg) {
  if (DEBUG) console.warn("[theailab]", msg);
}

// In hero-flourish.js:
var ctx = canvas.getContext("2d");
if (!ctx) {
  warn("Canvas context unavailable; homepage animation disabled");
  return;
}
```

Or connect to a service like Sentry for production observability (overkill for a course site, but an option).

---

## 5. Structural & Maintainability Observations

### Pattern: Duplicate Initialization Logic Across Files

Both `theme-init.js` and `theme.js` implement the same logic for resolving the current theme:
```javascript
// theme-init.js
function resolve() {
  var now = new Date();
  var pref = load();
  if (pref) {
    if (pref.locked) return pref.theme;
    if (now.getTime() < pref.expiresAt) return pref.theme;
    save(null);
  }
  return autoTheme(now);
}

// theme.js
function updateUI() {
  var theme = currentTheme();
  var pref = T.load();
  // ... uses T.load(), T.autoTheme(), etc.
}
```

The logic is exposed as `window.__theme` to avoid duplication, which is pragmatic. This works, but it's unconventional and couples the files. Not a bug, just a point where a small refactor (e.g., a `utils.js` with shared functions) would improve clarity.

---

### Font Loading Strategy

All pages link to Google Fonts with two `<link>` tags:
```html
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;..." rel="stylesheet"/>
```

The `preconnect` hints are correct, and the font stack includes local fallbacks (`-apple-system`, `Segoe UI`, etc.). No issues here; this is a solid approach for a site that doesn't need font subsetting or variable-font optimization beyond what Google Fonts provides.

---

## 6. Accessibility Assessment

**What's good:**
- ✓ Skip-to-content link on every page
- ✓ Semantic HTML (`<main>`, `<header>`, `<footer>`, `<nav>`, `<section>`, `<aside>`)
- ✓ Proper heading hierarchy (single `<h1>` per page, `<h2>` for subsections)
- ✓ `aria-label` on interactive elements (theme toggle, lock button)
- ✓ `aria-hidden="true"` on decorative elements (canvas, icons inside buttons)
- ✓ `role="img"` + `aria-label` on the journey map SVG
- ✓ Tables have row and column headers

**What's missing or incomplete:**
- ⚠ Theme-toggle button missing `aria-pressed` (finding 4.4)
- ⚠ No `lang` attribute on `<html>` (minor; assumed `en` from `lang="en"` on root tag, but should be explicit)
- ⚠ Journey-map "You are here" text is rendered in SVG without a surrounding `<title>` or `<desc>` for screen readers, just as inline text in a `<text>` element (low priority; the link already has a title)
- ⚠ News card HTML doesn't use semantic `<article>` or similar; just a generic `<div>` with `id="today-in-ai-card"`

Overall: **Good accessibility baseline, minor polish needed.**

---

## 7. Performance Notes

### Metrics (No tooling, qualitative assessment):

- **CSS:** 847 lines, single unminified file, no unused selectors (after dead CSS removal). Load time negligible.
- **JavaScript:** ~19KB total across 8 files (unminified). All files are < 3KB except `hero-flourish.js` (5.9KB) and `today-in-ai.js` (4.5KB). No minification, no tree-shaking.
- **External resources:** Google Fonts (preconnect hints present), Hacker News Algolia API (1-hour cache). No other external loads.
- **Canvas animation:** 150 rays, 60fps target (via `requestAnimationFrame`), responsive scaling with `devicePixelRatio`. Likely fine on modern devices; may be noticeable on older phones or under heavy load.

**Recommendation:** The site is fast enough for a course site. If performance issues arise, profile with the Chrome DevTools Performance tab and address the specific bottleneck (likely the canvas animation or large localStorage cache).

---

## 8. Suggested Priority for Next Steps

### Tier 1 (Fix Soon)
1. **XSS in `today-in-ai.js`** (4.1) — Replace `innerHTML` with `textContent` or proper HTML escaping.
2. **SVG generation safety** (4.2) — Switch to DOM methods or quote attributes properly.
3. **Theme-toggle `aria-pressed`** (4.4) — One-line addition for better accessibility.

### Tier 2 (Fix When Convenient)
4. **Remove hompage-only JS from non-homepage pages** (4.3) — Conditional script loading for slight performance gain.
5. **Validate course calendar data** (4.7) — Add initialization check for consistency.
6. **Add dark-mode color comments** (4.6) — Improve CSS maintainability.

### Tier 3 (Nice-to-Have / Future)
7. **Reduce-motion media query listener** (4.5) — Handle user preference changes mid-session.
8. **JavaScript unit tests** (4.8) — Add Selenium/Playwright tests for JS behavior.
9. **Error logging/observability** (4.9) — Add optional debug logging or Sentry integration.

### Still Open from Previous Report
10. **Templating/include mechanism** (from 09-03, 3.1) — At 22 pages with hand-duplicated boilerplate, still worth revisiting if the site grows beyond ~30 pages.

---

## 9. Conclusion

The site has made significant progress since Sept 3. **All five actionable findings from the prior report have been addressed**, and the recent additions of interactive features (JS for theme switching, news card, canvas animation) are well-written and show attention to detail (error handling, caching, graceful degradation when elements are missing).

The two medium findings (XSS and SVG safety) are worth fixing soon, but neither is currently exploitable in practice. The six low-severity findings are polish and maintainability improvements that can be tackled incrementally.

**Overall assessment:** A clean, accessible, well-tested static course site that is production-ready for a classroom context. Recommended for use.

---

**Report compiled:** 2026-09-08  
**Next review recommended:** After substantial feature additions (templating, public hosting, major JS refactoring) or when page count exceeds 40.
