# Tech Spec: Website Revision v1

**Date:** 2026-09-01
**Repo:** `theailab-net` (IPHS 400 course site)
**Scope:** Revisions to the standalone static site *after* Netlify/CI removal (see Mini-Project #1 manual, Step 0 — Netlify config, `.github/workflows/`, and Netlify-only headers/redirects are assumed already deleted and the site is served via a local dev webserver only).
**Input:** Findings from `docs/report_web-revision_v1_20260901.md`, re-scoped and re-ranked as standalone implementation tasks.
**Audience:** A student working through Mini-Project #1 with AI coding-agent assistance. Each task is self-contained: read the description and justification, then follow the numbered steps. Do tasks in order within a criticality tier; tiers themselves should be done High → Medium → Low.

**Conventions used below:**
- File paths are relative to the repo root.
- "All pages" means: `index.html`, `404.html`, `core/*.html` (5 files), `weeks/week-01.html` … `week-15.html` (15 files) — 22 pages total.
- After every task, re-run the test suite: `pytest tests/ -v` — all tests must stay green. If a task requires a *new* test, add it in the same task (don't defer test-writing to a later pass).

---

## Task List Overview

| # | Task | Criticality |
|---|---|---|
| 1 | Add per-page `<meta name="description">` | High |
| 2 | Add favicon | High |
| 3 | Add `robots.txt` and `sitemap.xml` | High |
| 4 | Add `aria-current="page"` to active nav link | High |
| 5 | Add skip-to-content link + `id` on `<main>` | High |
| 6 | Normalize internal link style in `core/` pages | Medium |
| 7 | Add `scope` attributes to table headers | Medium |
| 8 | Trim `.gitignore` to match actual project type | Medium |
| 9 | Relocate/remove stray `notes/` directory | Medium |
| 10 | Add Open Graph / Twitter Card metadata | Medium |
| 11 | Add "Last updated" indicator using existing `.page-meta` class | Low |
| 12 | Add print stylesheet | Low |
| 13 | Add footer links (repo, license) | Low |
| 14 | Convert bare-`<code>` GitHub URLs to real links | Low |
| 15 | Add HTML validation step to local test workflow | Low |
| 16 | Add JSON-LD structured data for the course | Low |

---

## High Criticality

### Task 1 — Add per-page `<meta name="description">`

**Description:** None of the 22 pages has a `<meta name="description">` tag. Add one to each, written from that page's own content.

**Justification:** This is the single highest-leverage SEO/sharing fix available: it controls the snippet shown in search results and is the fallback text for social-link previews. Every page already has enough distinct prose to summarize in one sentence — this is a content task, not a design task.

**Steps:**
1. For each of the 22 HTML files, read the page's main content and write one sentence (120–158 characters is the safe range for search snippets) that describes what the page contains.
2. Insert `<meta name="description" content="...">` immediately after the existing `<meta content="width=device-width..." ...>` viewport tag, before `<title>`.
3. Write a new pytest test in `tests/test_unit_html_structure.py` asserting every page has a non-empty `meta[name="description"]` tag with `content` length ≥ 50 characters.
4. Run `pytest tests/ -v` and confirm the new test passes for all 22 pages.

---

### Task 2 — Add favicon

**Description:** No `<link rel="icon">` exists anywhere, and no favicon file is in the repo.

**Justification:** Every page currently shows a generic browser-tab icon. A favicon is a one-time asset + one `<link>` tag per page, and it's the kind of visual polish a visitor notices immediately (tab bar, bookmarks, browser history).

**Steps:**
1. Create or source a simple favicon (an "IPHS" monogram, or reuse Kenyon's public brand mark if license permits — otherwise generate a simple text/color favicon). Save as `images/favicon.ico` and/or `images/favicon.svg` (SVG favicons are supported by modern browsers and are trivially agent-generatable as plain markup).
2. Add `<link rel="icon" href="/images/favicon.svg" type="image/svg+xml">` (adjust relative path per page — `core/` and `weeks/` pages need `../images/favicon.svg`) to every page's `<head>`.
3. Add a pytest test asserting every page has a `link[rel="icon"]` tag.
4. Run tests; verify the icon renders in a browser tab when the site is served locally.

---

### Task 3 — Add `robots.txt` and `sitemap.xml`

**Description:** Neither file exists at the site root.

**Justification:** Zero-maintenance, one-file additions that make the site's crawl/index behavior explicit rather than accidental. `sitemap.xml` also gives a canonical list of every real page, useful for future automated checks.

**Steps:**
1. Create `robots.txt` at repo root:
   ```
   User-agent: *
   Allow: /
   Sitemap: <site-root-url>/sitemap.xml
   ```
   (Leave the sitemap URL as a placeholder or the actual deploy URL once known — a local-only site can use a relative comment noting this should be updated at deploy time.)
2. Create `sitemap.xml` listing all 22 pages with `<loc>`, using standard sitemap XML schema.
3. Add a pytest test confirming both files exist at repo root and that `sitemap.xml` is well-formed XML containing exactly 22 `<url>` entries.
4. Run tests.

---

### Task 4 — Add `aria-current="page"` to active nav link

**Description:** The active nav item is marked only via `class="active"` (CSS-only). Add `aria-current="page"` to the same `<a>` tag on every page.

**Justification:** Sighted users get a visual underline cue for "you are here"; screen-reader users currently get nothing. `aria-current="page"` is the standard ARIA attribute for exactly this case and is a one-attribute change replicated across 22 pages using the existing `class="active"` marker as the target.

**Steps:**
1. For each page, find the nav `<a>` that already carries `class="active"` and add `aria-current="page"` to that same element.
2. Add a pytest test asserting exactly one `a[aria-current="page"]` exists per page, and that it's the same element carrying `class="active"`.
3. Run tests.

---

### Task 5 — Add skip-to-content link + `id` on `<main>`

**Description:** No page has a "skip to content" link, and `<main class="content-wrapper">` has no `id` to target even if one were added.

**Justification:** Every page repeats the same header/branding/6-link-nav block before reaching real content. Without a skip link, keyboard and screen-reader users must tab through the full nav on every single page load across all 22 pages. This is a standard, cheap, high-payoff accessibility fix because the layout is shared — one template change, replicated everywhere, fixes it site-wide.

**Steps:**
1. Add `id="main-content"` to the `<main class="content-wrapper">` element on every page.
2. Add, as the very first child of `<body>` on every page (before `<header>`): `<a class="skip-link" href="#main-content">Skip to content</a>`.
3. In `css/style.css`, add a `.skip-link` rule that visually hides the link off-screen by default and reveals it on `:focus` (standard pattern: `position: absolute; left: -9999px;` normally, `left: 0; top: 0;` on focus, with visible background/border so it's usable when focused).
4. Add a pytest test confirming every page has exactly one `a.skip-link[href="#main-content"]` as an early descendant of `<body>`, and that `main#main-content` exists on every page.
5. Manually test with keyboard only (Tab key on page load) in a browser to confirm the skip link appears and jumps focus correctly.
6. Run automated tests.

---

## Medium Criticality

### Task 6 — Normalize internal link style in `core/` pages

**Description:** `syllabus.html` and `schedule.html` link to sibling pages as `../core/syllabus.html` (up-and-back-down); `assignments.html`, `policies.html`, and `about.html` link as bare `syllabus.html` (direct sibling). Both resolve correctly today, but it's an inconsistency.

**Justification:** Not a bug (tests already pass), but it signals the six `core/` pages weren't generated from one shared template, and it will confuse the next person (or agent) editing these files, since two different mental models of "how do I link to a sibling" are both present.

**Steps:**
1. Choose the simpler convention: bare sibling-relative paths (e.g., `syllabus.html`, not `../core/syllabus.html`).
2. In `syllabus.html` and `schedule.html`, find every internal link using the `../core/*.html` form and rewrite it to the bare sibling form.
3. Confirm existing link-integrity tests (`tests/test_integration_links.py`) still pass — they should, since both forms already resolved correctly.
4. Manually click through all six `core/` pages locally to confirm no broken links.

---

### Task 7 — Add `scope` attributes to table headers

**Description:** All `<th>` elements across the site (13 in `syllabus.html` alone — Course Details, Assignments, Grading Scale, rubric tables, etc.) omit `scope="col"` / `scope="row"`.

**Justification:** WCAG 1.3.1 (Info and Relationships) best practice. Without `scope`, a screen reader announcing a table cell can't reliably state which header it belongs to, making tabular content (grading breakdowns, schedules) harder to navigate non-visually.

**Steps:**
1. For each `<table>` across all pages, determine whether headers are column headers (top row) or row headers (first cell of each row, as used in the two-column `Course Details`-style tables in `index.html`/`syllabus.html`).
2. Add `scope="col"` to column-header `<th>` elements and `scope="row"` to row-header `<th>` elements.
3. Add a pytest test asserting every `<th>` element site-wide has a non-empty `scope` attribute.
4. Run tests.

---

### Task 8 — Trim `.gitignore` to match actual project type

**Description:** The committed `.gitignore` is the full generic GitHub Python-project template (Django, Flask, Scrapy, Jupyter, pipenv/poetry/pdm lockfiles, Streamlit secrets, etc.), even though the only Python in the repo is the `tests/` directory.

**Justification:** Harmless but misleading — a maintainer skimming `.gitignore` would assume there's a Python application somewhere in the repo. A trimmed file that matches what's actually here (`.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, OS cruft like `.DS_Store`) is clearer with zero functional loss.

**Steps:**
1. Replace `.gitignore` contents with a short list covering only what this repo actually produces: virtual environment directory, Python bytecode/cache, pytest cache, editor/OS files (`.DS_Store`, `.vscode/` if not intentionally tracked).
2. Run `git status` before and after to confirm nothing newly tracked/untracked changes unexpectedly.

---

### Task 9 — Relocate/remove stray `notes/` directory

**Description:** `notes/subscription-zai-glm-coder.md` is untracked, unrelated to the site (a note about an unrelated AI-tool subscription), and not `.gitignore`d.

**Justification:** It's dead weight in a course-site repo and risks being accidentally committed. It should not ship as part of the public course repo.

**Steps:**
1. Move the file out of the repo entirely (e.g., to a personal notes location outside `~/code/theailab-net`), or delete it if no longer needed.
2. Confirm `git status` shows a clean working tree with no stray untracked files at repo root.

---

### Task 10 — Add Open Graph / Twitter Card metadata

**Description:** No `og:title`, `og:description`, `og:image`, or `twitter:card` tags exist anywhere.

**Justification:** Students and the instructor will likely share links to specific pages (syllabus, schedule) in Slack/Discord/email. Without OG tags, unfurled links show a bare URL with no title or preview — a real usability gap for a course site meant to be shared, and low effort given Task 1 already produced per-page descriptions to reuse.

**Steps:**
1. For each page, add `<meta property="og:title" content="...">` (reuse the `<title>` text minus the site suffix), `<meta property="og:description" content="...">` (reuse the Task 1 meta description), and `<meta property="og:type" content="website">`.
2. Add `<meta name="twitter:card" content="summary">` site-wide.
3. Optionally create one shared social-preview image (`images/og-preview.png`) and reference it via `og:image` on every page — acceptable to skip `og:image` if no image asset is available yet.
4. Add a pytest test confirming `meta[property="og:title"]` and `meta[property="og:description"]` exist on every page.
5. Run tests.

---

## Low Criticality

### Task 11 — Add "Last updated" indicator using existing `.page-meta` class

**Description:** `css/style.css` already defines a `.page-meta` class (line 266) that is never used in any HTML page. The syllabus text itself promises students should check "weekly updates to the course GitHub repository (the authoritative version)," but no page shows a last-updated date.

**Justification:** This closes a gap between what the site's own text promises and what it delivers — the styling already exists and is unused, so this is pure wiring, not new design work.

**Steps:**
1. On `syllabus.html` and `schedule.html` (the two pages most likely to change during the semester), add `<p class="page-meta">Last updated: YYYY-MM-DD</p>` near the top of `<main>`, using the actual last-edit date.
2. Optionally extend to all pages if consistency is preferred.
3. Decide (and document in a code comment or the README) whether this date is updated manually per edit, or leave as a manual-process note for now — no automation is required for this task.

---

### Task 12 — Add print stylesheet

**Description:** No `@media print` block exists. A syllabus is one of the most commonly printed course documents (advising, financial aid, offline access).

**Justification:** Printing any page today includes the header, full nav links, and the decorative `::before` underline on the hero heading — all irrelevant on paper and wasteful of ink/space.

**Steps:**
1. In `css/style.css`, add an `@media print { ... }` block that: hides `.main-nav`, `.skip-link`, and the hero's decorative underline; expands the text column (`--mw`) to a wider print-friendly measure; ensures link URLs are not required to print (optional: add `a::after { content: " (" attr(href) ")"; }` if desired, or skip for simplicity).
2. Use a browser's print-preview to visually confirm `syllabus.html` and one week page look reasonable without nav chrome.

---

### Task 13 — Add footer links (repo, license)

**Description:** The footer on every page is plain text only: `IPHS 400: Frontiers in AI · Kenyon College`.

**Justification:** The README already documents a public GitHub repo and an MIT license — surfacing both as footer links is a standard courtesy for a public academic site and costs one shared template edit.

**Steps:**
1. Update the shared footer markup on all 22 pages to add a link to the GitHub repo and a link to the license (either `LICENSE` file or an about-page anchor).
2. Add a pytest test confirming every page's footer contains a link matching the repo URL pattern.
3. Run tests.

---

### Task 14 — Convert bare-`<code>` GitHub URLs to real links

**Description:** In `syllabus.html` and `about.html`, `https://github.com/jon-chun/theailab-net` is marked up as plain `<code>` text, not a clickable `<a href>`.

**Justification:** Students currently have to copy-paste the URL manually. Trivial fix, meaningful convenience.

**Steps:**
1. In both files, replace `<code>https://github.com/...</code>` with `<a href="https://github.com/jon-chun/theailab-net"><code>https://github.com/...</code></a>` (or drop the `<code>` styling entirely if a plain link reads better).
2. Manually click both links locally to confirm they resolve.

---

### Task 15 — Add HTML validation step to local test workflow

**Description:** The pytest suite validates this site's own structural invariants (nav consistency, no orphans, no stub text) using `lxml`'s lenient parser, but nothing checks strict HTML5 validity (unclosed tags, duplicate `id`s, invalid attribute values).

**Justification:** Given how disciplined the rest of the test suite already is, adding a real validity check is a natural, cheap extension that catches a different class of bug than the existing tests target.

**Steps:**
1. Add an HTML5 validator tool as a dev dependency (e.g., `html5validator`, a pure-Python tool installable via `uv add --dev html5validator` or run via `uv run`).
2. Add a `tests/test_html_validity.py` that runs the validator against all 22 HTML files and asserts zero errors.
3. Run `pytest tests/ -v` and fix any validity errors surfaced (expect ID collisions to be the most likely finding given `id="main-content"` was just added in Task 5 — confirm it appears exactly once per page).

---

### Task 16 — Add JSON-LD structured data for the course

**Description:** No structured data (JSON-LD) describes the course to search engines or scraping tools.

**Justification:** Low-cost, consistent with the site's own "professional portfolio" framing for student work — the course site can model the same practice it asks of students. Not essential for a small course site, but a clean example of a "real-world SEO practice" for students to see and learn from.

**Steps:**
1. On `index.html` (and optionally `syllabus.html`), add a `<script type="application/ld+json">` block using `schema.org`'s `Course` type, populated with course title, description, instructor name, and provider (Kenyon College).
2. Validate the JSON-LD using a schema.org-compatible structured-data testing approach (e.g., manually check the JSON parses and matches the `Course` schema's expected fields).
3. No test suite change required — this is additive markup with no structural invariant to assert beyond "valid JSON," which can be a lightweight pytest check (`json.loads()` on the script tag's text content).

---

## Notes on Execution Order

Tasks within a tier are independent of each other (each touches a distinct concern) except:
- Task 5 (skip-link `id="main-content"`) should land before Task 15 (HTML validation), since duplicate/missing `id`s are exactly what a validator will flag.
- Task 1 (meta descriptions) should land before Task 10 (OG tags), since Task 10 reuses Task 1's descriptions.

All other tasks can be done in any order within their tier, and are good candidates for doing one-at-a-time with a fresh test-driven cycle (write/extend test → implement → run tests → fix → confirm green) as described in the Mini-Project #1 manual.
