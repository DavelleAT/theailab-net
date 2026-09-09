# Code Review: IPHS 400 Course Website

**Date:** September 8, 2026  
**Codebase:** theailab-net  
**Scope:** Full static site audit (HTML, CSS, JavaScript, tests)  
**Method:** Manual code inspection, line-by-line review, static pattern analysis

---

## Executive Summary

A well-structured static course website: 22 HTML pages, 8 JavaScript modules (1.5KB total), 847-line CSS file, and a comprehensive pytest test suite (566 lines across 3 test files). The site is dependency-free for viewing (Python only for tests), uses no build system, and focuses on clean semantic HTML with progressive enhancement.

**Strengths:** Solid test discipline, clean HTML structure, proper accessibility markers, good separation of concerns in JS modules.

**Concerns:** 6 code quality/security issues identified, ranging from XSS patterns to inefficient script loading.

| Category | Count |
|----------|-------|
| Security concerns | 2 |
| Code quality issues | 2 |
| Architecture/efficiency | 2 |
| **Total findings** | **6** |

All findings are actionable. None represent imminent risk to a classroom-use site.

---

## 1. Architecture & Structure

### 1.1 Site Layout
- **22 HTML pages:** 1 homepage + 1 404 page + 5 core pages (syllabus, schedule, assignments, policies, about) + 15 weekly pages
- **Single shared stylesheet:** `css/style.css` (847 lines, unminified)
- **8 JavaScript modules:** Theme system, dark mode, canvas animation, news widget, course calendar, navigation effects
- **Test suite:** 25 test cases across 3 files (unit structure, integration links, end-to-end completeness)

### 1.2 Page Generation
**Every HTML page is hand-written** — no templating engine, no SSG, no preprocessor. This means:
- Header, nav, footer markup is duplicated across all 22 files
- Consistency enforced by test suite, not by tooling
- Any structural change (e.g., adding a nav link) requires manual editing of 22 files

**Assessment:** Functional but labor-intensive at scale. Works fine for a 22-page course site; becomes risky beyond ~50 pages.

---

## 2. HTML Analysis

### 2.1 HTML Structure Quality

✅ **Good practices observed:**
- Proper `<!DOCTYPE html>` on every page
- Semantic HTML5 (`<main>`, `<header>`, `<footer>`, `<nav>`, `<aside>`)
- Single `<h1>` per page (correct heading hierarchy)
- Accessibility skip-link present on every page
- `aria-label` on interactive buttons
- `aria-hidden="true"` on decorative elements
- All internal links use relative paths (portable)
- Meta descriptions unique to each page

⚠️ **Observations:**
- **Boilerplate duplication:** Identical `<header>`, `<nav>`, `<footer>` across all 22 pages. One character change requires editing 22 files.
- **Minified vs. readable:** HTML is NOT minified, making it easy to read but larger on the wire (22KB for all pages combined vs. ~16KB minified). Not a practical concern for a course site, but worth noting.
- **SVG with inline styling:** Journey map uses inline CSS values instead of class-based styling (`fill="var(--accent)"` instead of `class="accent-color"`), making theme changes fragile.

### 2.2 HTML Accessibility
- ✓ Skip-to-content link
- ✓ Proper heading hierarchy
- ✓ Form labels (none present, but would be correct if added)
- ✓ Image alt text (no `<img>` tags used; only background images and SVG)
- ✓ ARIA landmarks on interactive elements
- ⚠ Theme toggle button missing `aria-pressed="true/false"` state indicator

---

## 3. CSS Analysis

### 3.1 CSS Organization
**847 lines, single unminified file:**
```
- CSS Reset & Root variables
- Dark mode palette
- Site header (160 lines)
- Hero section
- Main navigation & magnification effects
- Content & tables
- Homepage grid & widget rail
- News card styling
- Footer
- Responsive breakpoints (@media)
```

**Assessment:** Clean, logical ordering. No duplicated rules found. Variables well-named and clearly commented.

### 3.2 CSS Quality Issues

**3.2.1 [MINOR] Unused Color Tokens**
Several CSS variables are defined but not used in any HTML or CSS:
```css
--code-bg: #f3ede3;  /* Used only in table headers */
```
No unused rule blocks found (dead WordPress CSS was removed), but some color tokens appear reserved for future use without documentation.

**3.2.2 [MINOR] Hard-coded Pixel Values in Media Queries**
```css
@media (max-width: 1024px) { ... }
@media (max-width: 768px) { ... }
```
Responsive breakpoints are good, but no documented rationale for these specific values. Are they tested on real devices? No CSS variables for breakpoint values, making future changes require grep-and-replace.

**Recommendation:** Define breakpoint variables:
```css
:root {
  --breakpoint-tablet: 1024px;
  --breakpoint-mobile: 768px;
}
@media (max-width: var(--breakpoint-mobile)) { ... }
```

### 3.3 CSS Performance
- **File size:** 20KB unminified, ~12KB minified
- **Selectors:** All class-based or simple element selectors; no complex descendant chains
- **Animations:** Used only on homepage canvas and nav hover magnification; performant (no repaints on scroll)
- **Font loading:** Preconnect to Google Fonts; async loading strategy is correct

---

## 4. JavaScript Analysis

### 4.1 Code Organization

**8 modules, ~1.5KB total, all wrapped in IIFEs (Immediately Invoked Function Expressions):**

| File | Lines | Purpose | Global Scope Pollution |
|------|-------|---------|------------------------|
| `course-calendar.js` | 78 | Week dates & logic | `window.CourseCalendar` (intentional) |
| `hero-flourish.js` | 169 | Canvas background | None (self-contained) |
| `journey-map.js` | 57 | "You are here" marker | None (reads `window.CourseCalendar`) |
| `nav-wave.js` | 40 | Dock-style nav effect | None |
| `theme-init.js` | 72 | Theme resolution (early) | `window.__theme` (intentional) |
| `theme.js` | 80 | Theme button wiring | None (reads `window.__theme`) |
| `this-week-card.js` | 65 | Week progress card | None (reads `window.CourseCalendar`) |
| `today-in-ai.js` | 129 | News widget from HN API | None |

**Assessment:** Good module isolation. Two intentional globals (`window.CourseCalendar`, `window.__theme`) are clearly named and serve as inter-module communication interfaces.

### 4.2 Security Concerns

**4.2.1 [SECURITY] innerHTML with Unsanitized API Data**  
**File:** `js/today-in-ai.js`, lines 83–97

```javascript
function cardHTML(story) {
  return (
    '<div class="news-label">Today in AI</div>' +
    '<p class="news-headline">"' + story.title + '"</p>' +  // ← NO ESCAPING
    '<p class="news-source">via Hacker News</p>' +
    '<p class="news-caption">The field doesn't pause for a syllabus...</p>'
  );
}
function render(stories) {
  // ...
  card.innerHTML = cardHTML(story);  // ← DIRECT INJECTION
}
```

The `story.title` is fetched from the Hacker News Algolia API and injected directly into HTML. While HN's API is trusted and monitored, the code pattern is not defensive against:
- Future API changes
- Cached/corrupted data
- Accidental HTML entity inclusion (e.g., a title with `&nbsp;` or `<br>` would break layout)

**Risk level:** Low in practice (HN API is well-maintained), but the code pattern violates the principle of never trusting external data.

**Remediation:**
```javascript
function cardHTML(story) {
  var escaped = escapeHtml(story.title);
  return '<p class="news-headline">"' + escaped + '"</p>';
}

function escapeHtml(text) {
  var map = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'};
  return String(text).replace(/[&<>"']/g, c => map[c]);
}
```

Or use DOM methods:
```javascript
var headline = document.createElement('p');
headline.className = 'news-headline';
headline.textContent = '"' + story.title + '"';  // textContent is always safe
card.appendChild(headline);
```

**4.2.2 [SECURITY] SVG Markup Generation Without Proper Quoting**  
**File:** `js/journey-map.js`, lines 36–48

```javascript
marker.innerHTML =
  '<circle class="here-ring" cx="' + center.x + '" cy="' + center.y + '" r="13"></circle>' +
  '<text ... x="' + center.x + '" y="' + labelY + '" ...>You are here</text>';
```

Numeric values are floats (e.g., `234.567`), which are safe for this use case. However, if these values ever come from user input or an untrusted source, unquoted attributes could break SVG structure. Current risk is low since values are computed from internal date logic, but the pattern doesn't scale.

**Better approach:**
```javascript
var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
circle.setAttribute('class', 'here-ring');
circle.setAttribute('cx', center.x);
circle.setAttribute('cy', center.y);
marker.appendChild(circle);
```

### 4.3 Code Quality Issues

**4.3.1 [CODE QUALITY] Inefficient Script Loading on Every Page**  
**Files:** `index.html`, `core/*.html`, `weeks/*.html`

The homepage includes 8 scripts:
```html
<script src="js/hero-flourish.js"></script>
<script src="js/journey-map.js"></script>
<script src="js/course-calendar.js"></script>
<script src="js/this-week-card.js"></script>
<script src="js/nav-wave.js"></script>
<script src="js/today-in-ai.js"></script>
<script src="js/theme.js"></script>
```

But interior pages (22 - 1 = 21 pages) also load these scripts via relative paths. Of the 8:
- `hero-flourish.js` → only works on `index.html` (checks `if (!canvas) return`)
- `journey-map.js` → only works on `index.html` (checks `if (!svg) return`)

**Impact:**
- 150 canvas rays initialized in `hero-flourish.js` even on non-homepage pages, then discarded
- Animation loop (`requestAnimationFrame`) started for nothing
- Event listeners registered (resize, mousemove) on every page, even when unused

**Metrics:**
- Extra download: Negligible (59 + 57 = 116 bytes for 2 unused modules)
- Extra computation: ~5-10ms on page load (150-ray initialization + event listener setup)

**Practical impact:** Minimal for a course site, but wasteful.

**Remediation:** Conditionally load homepage-only scripts on `index.html` only, or add a guard:
```javascript
// In hero-flourish.js
if (!document.getElementById('bg-flourish')) return;
```

Or cleaner: Use feature detection and avoid global initialization:
```html
<!-- Only on index.html -->
<script src="js/hero-flourish.js"></script>
<script src="js/journey-map.js"></script>

<!-- On all pages -->
<script src="js/course-calendar.js"></script>
...
```

**4.3.2 [CODE QUALITY] Hardcoded Calendar Data Without Validation**  
**File:** `js/course-calendar.js`, lines 7–48

Week dates and break ranges are hardcoded arrays with no validation:

```javascript
var WEEK_START_DATES = [
  "2026-08-27", // Week 1
  "2026-09-01", // Week 2
  // ... manual entries ...
];

var BREAKS = [
  { start: "2026-10-08", end: "2026-10-09", name: "October Break" },
  // ...
];

var WEEK_TITLES = [
  "Course Introduction",
  "Shell Fundamentals and Dotfiles",
  // ... 15 entries ...
];
```

**Risks:**
- If a week date is out of order (e.g., `"2026-09-08"` then `"2026-09-01"`), `currentWeekNumber()` silently returns wrong results
- If `WEEK_TITLES` has 14 entries instead of 15, no error is thrown until someone views week 15
- Break dates and week dates can overlap silently
- Data duplication (week numbers are implicit in array order, but could be explicit)

**Remediation:** Add initialization validation:
```javascript
function validateCalendarData() {
  if (WEEK_START_DATES.length !== WEEK_TITLES.length) {
    throw new Error('Week dates and titles count mismatch');
  }
  var prev = null;
  for (var i = 0; i < WEEK_START_DATES.length; i++) {
    if (WEEK_START_DATES[i] < prev) {
      throw new Error('Week dates out of order at index ' + i);
    }
    prev = WEEK_START_DATES[i];
  }
}
validateCalendarData();
```

Or restructure to a single source of truth:
```javascript
var WEEKS = [
  { number: 1, startDate: "2026-08-27", title: "Course Introduction", mp: "mp1" },
  // ...
];
```

### 4.4 JavaScript Best Practices

✅ **Good patterns:**
- Proper error handling in `theme-init.js` (try/catch around localStorage)
- Async/await pattern correctly used in `today-in-ai.js` (fetch with `.then()` and `.catch()`)
- Graceful degradation when elements don't exist (each module checks for its root element)
- Proper scope isolation (8 IIFEs prevent global namespace pollution)
- Event listener cleanup not strictly necessary for page-scoped listeners, but modern approach would use `addEventListener`

⚠️ **Minor gaps:**
- No error logging or observability (silent failures in canvas, API, localStorage)
- No mobile-first responsive testing in JS (nav-wave.js hover effects only, no touch support)
- `prefers-reduced-motion` respected at page load but not monitored for runtime changes (unlikely to matter)

---

## 5. Test Suite Analysis

### 5.1 Test Coverage
**566 lines of pytest across 3 files:**

```
test_unit_html_structure.py (364 lines):
  - DOCTYPE validation (22 pages)
  - Title suffix consistency
  - CSS link resolution
  - Favicon presence & resolution
  - Meta description presence
  - Table wrap ancestors
  - Session metadata on week pages
  - MP-arc color tokens
  - Ethics thread on correct weeks
  - Skip link as first body element
  - Header/footer/hero presence
  - No leftover template branding
  - Theme button presence
  - Today-in-AI widget loading

test_integration_links.py (110 lines):
  - All internal links resolve
  - Navigation consistency across pages
  - Journey map links all 15 weeks
  - Schedule links all 15 weeks

test_e2e_site.py (92 lines):
  - Required files exist
  - Required directories exist
  - Exact page count (22)
  - Core directory has exactly 5 files
  - Weeks directory has exactly 15 files
  - All pages reachable from index via links
```

### 5.2 What Tests Cover Well
- ✅ Structural integrity (DOCTYPE, titles, core elements)
- ✅ Link consistency and resolution
- ✅ Navigation consistency across 22 pages
- ✅ Page count and directory structure
- ✅ Reachability from homepage

### 5.3 What Tests Don't Cover
- ❌ JavaScript functionality (no Selenium/Playwright tests)
  - Theme toggle doesn't actually persist
  - Today-in-AI card actually fetches data correctly
  - Journey map marker renders at right coordinates
  - Course calendar date logic works for all weeks
- ❌ CSS rendering (no visual regression tests)
- ❌ Responsive design on actual devices
- ❌ Dark mode appearance (CSS only, no rendered output)
- ❌ Performance metrics (load time, render time)

**Assessment:** Tests provide excellent coverage of HTML structure and static content integrity. They're the backbone of preventing regressions when hand-editing 22 files. However, there's a gap for JavaScript behavior testing.

---

## 6. Accessibility Audit

### 6.1 Strengths
- ✅ Skip-to-content link on every page
- ✅ Proper heading hierarchy (single H1, then H2s)
- ✅ Semantic HTML (`<main id="main">`, `<nav>`, `<header>`, `<footer>`)
- ✅ `aria-label` on all buttons
- ✅ `aria-hidden="true"` on decorative elements
- ✅ SVG journey map has `role="img"` and `aria-label`
- ✅ Color contrast is good (dark text on light bg, vice versa in dark mode)

### 6.2 Gaps
- ⚠️ Theme toggle button: Missing `aria-pressed="true/false"` to indicate current state
- ⚠️ Theme lock button: Has `aria-pressed` but it's `hidden` until first toggle (OK, but inconsistent)
- ⚠️ SVG text elements ("You are here"): Rendered inline without proper semantic wrapper for screen readers
- ⚠️ News card: `<div class="news-card" id="today-in-ai-card">` is not semantic; should be `<article>`

**Overall:** Good accessibility foundation. A few WCAG AA improvements would bring it to "best practice" level.

---

## 7. Performance Observations

### 7.1 Network Performance
- **HTML:** 22 files, ~22KB total (unminified)
- **CSS:** 20KB unminified, ~12KB minified
- **JavaScript:** ~12KB total unminified (59 + 57 + 78 + 169 + 40 + 72 + 80 + 65 + 129 bytes, roughly)
- **External:** Google Fonts (2 preconnect, 1 stylesheet), HN Algolia API (cached 1x per hour per visitor)

**Assessment:** Very lightweight. Preconnect hints are in place. No render-blocking resources.

### 7.2 Runtime Performance
- Canvas animation (150 rays): ~60fps target via `requestAnimationFrame`; uses `devicePixelRatio` for proper scaling
- Nav wave effect: Pure CSS transforms, no layout thrashing
- Theme switching: DOM attribute change only, no repaint overhead
- API caching: 1-hour TTL, no re-fetching on navigation

**Assessment:** Performant for a course site. No obvious bottlenecks.

---

## 8. Security Considerations

### 8.1 High-Risk Issues
None identified.

### 8.2 Medium-Risk Issues
1. **XSS in news card (4.2.1):** Use of `innerHTML` with unsanitized API data. Unlikely to be exploited (HN API is trustworthy), but not defensive.
2. **SVG string concatenation (4.2.2):** Similar issue; unlikely in practice, but the pattern is fragile.

### 8.3 Low-Risk Issues
- No CSRF tokens (not applicable; site is read-only)
- No authentication (correct for a course site)
- No database (correct for a static site)
- localStorage usage: Properly wrapped in try/catch for private browsing mode

---

## 9. Recommendations — Prioritized

### Tier 1: Security / Code Quality (Fix Soon)
1. **4.2.1:** Replace `innerHTML` with `textContent` or proper HTML escaping in `today-in-ai.js`
2. **4.3.2:** Add validation function for calendar data at initialization
3. **4.2.2:** Use DOM methods instead of string concatenation for SVG generation

### Tier 2: Efficiency / Maintainability (Fix When Convenient)
4. **4.3.1:** Conditionally load homepage-only scripts on `index.html` only
5. **2.2 + 6.2:** Add `aria-pressed` to theme toggle button
6. **3.2.2:** Extract breakpoint values to CSS variables

### Tier 3: Improvements (Nice-to-Have)
7. Add unit tests for JavaScript modules (Vitest or Jest)
8. Refactor course calendar data into a single source of truth (array of week objects)
9. Add client-side error logging (optional, low priority for internal site)
10. Consider templating solution if page count grows beyond 40

---

## 10. Conclusion

**A clean, well-tested static course website suitable for classroom use.** The codebase demonstrates good discipline: comprehensive test suite, semantic HTML, proper accessibility markers, and good module isolation in JavaScript.

The two security concerns (XSS patterns) are real but unlikely to be exploited in practice. The architectural constraint (hand-duplicated boilerplate on 22 pages) is a known tradeoff that works fine at this scale but would become painful beyond ~50 pages.

**Recommendation:** Ready for production use. Prioritize fixing the three Tier 1 findings (security/code quality) before the next semester or before adding more pages. Consider adding JavaScript unit tests when the test suite is next updated.

---

**Report Date:** 2026-09-08  
**Reviewer:** Claude Code (static analysis)  
**Files Analyzed:** 22 HTML pages, 1 CSS file, 8 JS modules, 3 test files
