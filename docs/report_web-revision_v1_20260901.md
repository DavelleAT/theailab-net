# theailab-net Website Review

**Date:** 2026-09-01
**Scope:** Full repository — 22 static HTML pages, shared stylesheet, pytest test suite, Netlify/GitHub Actions deploy pipeline.
**Reviewer:** Claude Code (automated codebase audit)

## Summary

This is a small, well-disciplined static site: no build step, one shared stylesheet, a consistent page skeleton (header/nav/hero/footer), and a genuinely useful pytest suite that already catches broken links, missing structural elements, and orphaned pages (25/25 tests pass as of this review). The content (syllabus, schedule, policies) is thorough and internally date-consistent — I checked every schedule date against the actual 2026 calendar and they all land on the days of the week claimed.

The gaps are concentrated in three areas the test suite doesn't cover: **(1) a production-breaking deploy misconfiguration**, **(2) SEO/social metadata**, and **(3) accessibility affordances beyond what plain semantic HTML gives for free**. None of the content itself is wrong; the issues below are omissions, not errors in what's written.

Findings are ordered by severity.

---

## 1. Critical

### 1.1 `netlify.toml` redirects the entire site to 404

```toml
[[redirects]]
  from = "/*"
  to = "/404.html"
  status = 404
```

This is a catch-all redirect matching every path (`/*`) to `404.html` with a `404` status. On Netlify, a `[[redirects]]` rule with no `force = true` still applies if no static file matches the request *before* falling through — but more importantly, this rule as written has no exceptions carved out for real pages. Depending on how Netlify's redirect precedence resolves against the static files in `publish = "."`, this either:

- does nothing (Netlify serves static files first, so this never fires) — makes the rule dead weight, or
- actively breaks every route that isn't served as a literal file match (e.g., trailing-slash variants, any future clean-URL routing) by forcing a 404.

Either way, this is very likely not the intent. A custom 404 page should be configured via a **404.html file at the publish root** (which Netlify auto-detects with no redirect needed) or, if a redirect is wanted, scoped narrowly — never `/*`. As written, this rule is a landmine: the moment someone add a route Netlify doesn't statically resolve (e.g. `/schedule` without `.html`), it will silently serve a 404 instead of the intended content.

**Recommendation:** Delete the `[[redirects]]` block entirely. Netlify serves `404.html` automatically as the custom error page for unmatched routes in a static site with no other config needed. If clean URLs (no `.html`) are wanted later, add `pretty_urls` handling deliberately, not via this rule.

### 1.2 No verification that the Netlify deploy has ever succeeded

The GitHub Actions workflow (`.github/workflows/deploy-netlify.yml`) and README both note the deploy step requires `NETLIFY_AUTH_TOKEN` and `NETLIFY_SITE_ID` repository secrets, and that "until those secrets are configured, the workflow run will fail at the deploy step." The README's own "Live site" line still reads `_add Netlify URL here once deployed_`. There's no evidence in-repo that the site has ever been live. This isn't a code defect, but given finding 1.1, it means the redirect bug may not have been exercised against a real deployment yet — worth fixing before the first real deploy, not after.

---

## 2. High

### 2.1 No `<meta name="description">` on any of the 22 pages

Every page (home, 404, all 5 core pages, all 15 week pages) is missing a meta description. This directly affects search-result snippets and any share preview that falls back to it. Trivial to add per-page (each page already has distinct, well-written prose to summarize).

### 2.2 No Open Graph / Twitter Card metadata

No `og:title`, `og:description`, `og:image`, or `twitter:card` tags anywhere in the site. Since students and the instructor will likely share links to this course site (syllabus, schedule) in Slack/Discord/email/social, unfurled links will show a bare URL with no title/preview. Low effort, real payoff for a course site meant to be shared.

### 2.3 No favicon

No `<link rel="icon">` anywhere and no favicon file in the repo. Browsers will show a generic icon in tabs/bookmarks across all 22 pages.

### 2.4 No `robots.txt` or `sitemap.xml`

Neither file exists at the site root. Not strictly required for a small course site, but both are one-file, zero-maintenance additions that improve crawlability and let you control indexing (e.g., excluding `404.html` from a sitemap, or blocking indexing entirely if this is meant to be low-visibility until launch).

### 2.5 Inconsistent relative-link style for the same targets

Within `core/`, the six pages don't agree on how they link to each other:

- `syllabus.html` and `schedule.html` link internally as `../core/syllabus.html`, `../core/schedule.html`, etc. (going up to root and back down into `core/`, even though the linking page is already inside `core/`).
- `assignments.html`, `policies.html`, and `about.html` link to sibling pages as bare `syllabus.html`, `schedule.html`, etc.

Both forms resolve correctly today (confirmed by the passing link-integrity tests), so this is not a bug — but it's an inconsistency that will confuse whoever edits these files next, and it signals the six `core/` pages were not generated from one shared template/script. Pick one convention (bare sibling-relative is simpler and shorter) and normalize all six.

### 2.6 No active/current-page indication for assistive technology

The nav's "active" page is marked only with `class="active"` (a CSS hook), with no `aria-current="page"`. Sighted users get a visual cue (underline); screen-reader users get none. This is a one-attribute-per-page fix (15+7 pages) that meaningfully improves nav orientation for AT users.

---

## 3. Medium

### 3.1 No skip-to-content link

Every page repeats the same header → branding → nav block before reaching `<main>`. There's no `<a class="skip-link" href="#main-content">Skip to content</a>` as the first focusable element, so keyboard and screen-reader users must tab through the full nav (6 links) on every single page load, on all 22 pages, to reach the actual content. This is a standard, cheap accessibility fix (one link + a few lines of CSS to hide it until focused) that pays off site-wide because the layout is shared.

### 3.2 `<main>` has no `id`, so a skip link (and any deep-linking to content) has nothing to target

Related to 3.1: `<main class="content-wrapper">` never gets an `id`, so there's currently no way to anchor a skip link or a "jump to content" affordance even if one were added.

### 3.3 Table headers lack `scope` attributes

All data tables (Course Details, Assignments, Grading Scale, MP3/4 rubric, etc. — 13 `<th>` elements in `syllabus.html` alone) omit `scope="col"`/`scope="row"`. This is a WCAG 1.3.1 (Info and Relationships) best practice for screen readers navigating tabular data; without it, a screen reader announcing a cell can't reliably say which header it belongs to.

### 3.4 `.gitignore` is a full Python-project template on an HTML/CSS site

The committed `.gitignore` is the generic GitHub Python template (Django, Flask, Scrapy, PyBuilder, Jupyter, pipenv/poetry/pdm/pixi lockfile guidance, Streamlit secrets, marimo, etc.) even though the only Python in this repo is the `tests/` directory. This is harmless (it doesn't ignore anything that shouldn't be ignored) but is dead weight and slightly misleading about what kind of project this is — a maintainer skimming it would reasonably assume there's a Python application somewhere. A trimmed version (`__pycache__/`, `.venv/`, `.pytest_cache/`, `*.pyc`) would be clearer and is functionally equivalent for this repo's actual needs.

### 3.5 Untracked `notes/` directory at repo root

`git status` shows `notes/subscription-zai-glm-coder.md` as untracked. It's unrelated to the site content (a subscription note for an unrelated tool) and isn't `.gitignore`d, so it will show as dirty/untracked indefinitely and risks being accidentally committed into a site repo where it doesn't belong. Worth moving out of this repo or explicitly ignoring.

### 3.6 No structured data (JSON-LD) for the course

A `Course`/`EducationalOccupationalProgram`-type JSON-LD block on the home page or syllabus page is a low-cost addition that can improve how the page is understood by search engines and any tool that scrapes course metadata (e.g., a future Kenyon course aggregator). Not essential, but consistent with the "professional public portfolio" framing the syllabus itself uses for the students' own work — the course site could model the same practice.

### 3.7 No `lang` distinctions or handling for non-English content

Not an issue today (everything is English), but worth noting there's no `hreflang`/i18n consideration at all — fine for now, just flagging it's a non-consideration rather than a deliberate decision, in case this site is ever reused as a template (the README says the layout was adapted from a prior course site, so reuse is a real pattern here).

---

## 4. Low / Polish

### 4.1 No `Last updated` / version indicator on syllabus or schedule

The syllabus explicitly warns readers that "this syllabus... may be updated during the semester" and directs them to "weekly updates to the course GitHub repository (the authoritative version)." Without a visible "last updated" date or a link to the commit history, a student has no way to tell, from the page itself, whether they're looking at current or stale content. A simple `<p class="page-meta">Last updated: 2026-09-01</p>` (the repo already has an unused `.page-meta` CSS class defined for exactly this) would close the gap between what the text promises and what the page delivers.

### 4.2 `.page-meta` CSS class defined but unused

`css/style.css` defines `.page-meta` (`css/style.css:266`) as a "repo addition — quiet" style, but no HTML page actually uses it. Combined with 4.1, this looks like a feature that was designed but never wired up.

### 4.3 No print stylesheet

A syllabus is one of the most commonly printed documents in a course site (financial aid, advising, students without reliable laptop access in class). There's no `@media print` block to suppress the header/nav/hero chrome and hero underline decoration, or to expand the `--mw: 640px` text column to full page width for print. Currently printing any page will include the nav links and the decorative underline the CSS draws before `<h1>` via `.hero h1::before`.

### 4.4 Footer has no links (privacy, license, repo)

The footer on every page is just plain text: `IPHS 400: Frontiers in AI · Kenyon College`. Given the README publicly documents the GitHub repo and the LICENSE (MIT), a footer link to the repo (`github.com/jon-chun/theailab-net`) and/or the license would be a small, standard courtesy for a public academic site — especially since About and Syllabus already surface the repo URL as inline `<code>`, not as a clickable link.

### 4.5 GitHub URL is presented as `<code>`, not a link

In both `syllabus.html` and `about.html`, `https://github.com/jon-chun/theailab-net` is marked up as `<code>` text rather than an `<a href>`. Students have to copy-paste it manually instead of clicking through.

### 4.6 CI workflow has no HTML validator / linter step

The GitHub Actions workflow runs the pytest suite (which is structural/content-focused) but nothing checks the HTML against the W3C validator or an HTML linter (e.g., `html5validator`, `htmlhint`). The pytest suite is good at catching *this site's* specific invariants (nav consistency, no orphans, no stub text) but wouldn't catch, e.g., unclosed tags, duplicate `id`s, or invalid attribute values, since it parses with `lxml`'s lenient HTML parser rather than validating strictly. Given how disciplined the rest of the pipeline already is, adding an HTML5-validity check would be a natural, cheap addition.

### 4.7 No `Content-Security-Policy` header

`netlify.toml` sets `X-Frame-Options: DENY` and `X-Content-Type-Options: nosniff`, which is a good start, but there's no CSP header. Low risk for a static site with no user input and no third-party scripts, but since the site does load nothing external at all (no CDN fonts, no analytics, no JS), a strict `default-src 'self'` CSP would be free to add and forecloses that risk category entirely if any external embed is ever added later without someone remembering to revisit security headers.

### 4.8 No analytics or uptime signal

There's no way to know from the repo whether the deployed site is actually being visited, or whether links are being clicked, once (if) it goes live. Not a defect — plenty of sites intentionally skip analytics for privacy reasons — but worth a conscious decision rather than a default. If privacy is the goal, that's a fine choice; if visibility into whether students are actually finding assignments is useful, a privacy-respecting option (e.g., Plausible, GoatCounter, or Netlify's own analytics) is low-friction to add later since there's no existing tracking to conflict with.

---

## 5. What's already good (worth preserving, not just noting)

- **Test coverage is genuinely strong for what it targets**: doctype, title suffix, CSS resolution, header/footer/hero presence, no leftover template branding, no stub content, all internal links resolve, nav is identical and correct across all 22 pages, schedule links all 15 weeks, exact page-count and file-set assertions, and full reachability from `index.html`. This is more rigorous than most static sites of this size get, and it already caught the class of bug (broken/missing links, drifted nav, orphaned pages) that's most common in hand-edited multi-page HTML.
- **Date consistency**: every date claimed across `schedule.html` and the 15 week pages was independently checked against the real 2026 calendar (day-of-week for every session date, the October Break window, Thanksgiving recess, and the exam period) — all of it is internally correct.
- **Content quality**: the syllabus, policies, and assignments pages are unusually complete and well-organized for a course site — clear grading breakdowns, an explicit and non-punitive AI-use policy, secrets-hygiene guidance baked into course content, and a sensible non-AI-maximalist carve-out for the final poster prose.
- **No build step, no JS, one stylesheet**: this keeps the whole site auditable in one sitting and matches the README's own stated design goal. The CSS custom-property-based theming is clean and the responsive breakpoints are sensible.
- **Color contrast passes WCAG AA**: verified `--text-lt` (#767676) at 4.54:1 and `--accent` (#0073aa) at 5.21:1 against the white background — both clear the 4.5:1 threshold for normal text.
- **Security headers exist at all**: `X-Frame-Options` and `X-Content-Type-Options` are set in `netlify.toml`, which is more than many static sites bother with.

---

## Suggested Priority Order

1. Fix or remove the `netlify.toml` catch-all 404 redirect (1.1) — do this before the first real deploy.
2. Add per-page `<meta name="description">`, favicon, and `robots.txt`/`sitemap.xml` (2.1–2.4) — batchable, low-risk, high payoff.
3. Add `aria-current="page"` to nav (2.6) and a skip-to-content link with a `#main-content` target on `<main>` (3.1–3.2) — improves accessibility site-wide with a single template change replicated across pages.
4. Normalize the `core/` internal link style (2.5) and add `scope` to table headers (3.3).
5. Everything in Section 4 as ongoing polish, prioritizing 4.1 (last-updated indicator) since the syllabus text explicitly promises it and the CSS class is already sitting there unused.
