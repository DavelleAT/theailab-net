"""Unit tests: every HTML page has valid structure and required elements."""
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent

TITLE_SUFFIX = "– IPHS 400: Frontiers in AI"  # en dash
FOOTER_TEXT = "IPHS 400: Frontiers in AI · Kenyon College"


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


class TestDoctype:
    def test_all_pages_have_doctype(self, parsed_pages):
        """Every HTML page must begin with <!DOCTYPE html>."""
        failures = []
        for path, text, _ in parsed_pages:
            if not text.strip().lower().startswith("<!doctype html"):
                failures.append(_rel(path))
        assert not failures, f"Pages missing <!DOCTYPE html>: {failures[:15]}"


class TestTitle:
    def test_all_titles_end_with_course_suffix(self, parsed_pages):
        """Every <title> must end with '{TITLE_SUFFIX}'."""
        failures = []
        for path, _, soup in parsed_pages:
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            if not title.endswith(TITLE_SUFFIX):
                failures.append(f"{_rel(path)}: '{title}'")
        assert not failures, f"Titles not ending with course suffix: {failures[:15]}"


class TestCSSLink:
    def test_all_pages_link_to_resolvable_style_css(self, parsed_pages):
        """Every page must have a <link rel='stylesheet'> to a resolvable css/style.css."""
        failures = []
        for path, _, soup in parsed_pages:
            links = [
                tag for tag in soup.find_all("link", rel="stylesheet")
                if "style.css" in tag.get("href", "")
            ]
            if not links:
                failures.append(f"{_rel(path)}: no stylesheet link")
                continue
            href = links[0]["href"]
            target = (path.parent / href).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: href '{href}' does not resolve")
        assert not failures, f"CSS link issues: {failures[:15]}"


class TestFavicon:
    def test_all_pages_link_to_resolvable_favicon(self, parsed_pages):
        """Every page must have a <link rel='icon'> to a resolvable favicon file."""
        failures = []
        for path, _, soup in parsed_pages:
            icon = soup.find("link", rel="icon")
            if not icon or not icon.get("href"):
                failures.append(f"{_rel(path)}: no <link rel='icon'>")
                continue
            target = (path.parent / icon["href"]).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: favicon href '{icon['href']}' does not resolve")
        assert not failures, f"Favicon issues: {failures[:15]}"


class TestMetaDescription:
    def test_all_pages_have_nonempty_meta_description(self, parsed_pages):
        """Every page must have a non-empty <meta name='description'>."""
        failures = []
        for path, _, soup in parsed_pages:
            meta = soup.find("meta", attrs={"name": "description"})
            if not meta or not meta.get("content", "").strip():
                failures.append(f"{_rel(path)}: missing or empty meta description")
        assert not failures, f"Meta description issues: {failures[:15]}"


class TestTableWrap:
    def test_all_tables_have_table_wrap_ancestor(self, parsed_pages):
        """Every <table> must have an ancestor <div class="table-wrap"> for horizontal-scroll safety."""
        failures = []
        for path, _, soup in parsed_pages:
            for table in soup.find_all("table"):
                if not table.find_parent("div", class_="table-wrap"):
                    failures.append(_rel(path))
                    break
        assert not failures, f"Tables missing .table-wrap ancestor: {failures[:15]}"


class TestSessionMeta:
    WEEK_FILES = {f"week-{i:02d}.html" for i in range(1, 16)}

    def test_every_week_page_has_session_meta_wrapper(self, parsed_pages):
        """Every weeks/week-NN.html must wrap its date + MP-arc lines in .session-meta."""
        failures = []
        for path, _, soup in parsed_pages:
            if path.name in self.WEEK_FILES and path.parent.name == "weeks":
                if not soup.select_one(".session-meta"):
                    failures.append(_rel(path))
        assert not failures, f"Week pages missing .session-meta: {failures[:15]}"


class TestMpDot:
    EXPECTED_TOKEN = {}
    for _n in range(1, 3): EXPECTED_TOKEN[f"week-{_n:02d}.html"] = "--mp1"
    for _n in range(3, 6): EXPECTED_TOKEN[f"week-{_n:02d}.html"] = "--mp2"
    for _n in range(6, 10): EXPECTED_TOKEN[f"week-{_n:02d}.html"] = "--mp3"
    for _n in range(10, 14): EXPECTED_TOKEN[f"week-{_n:02d}.html"] = "--mp4"
    for _n in range(14, 16): EXPECTED_TOKEN[f"week-{_n:02d}.html"] = "--final"

    def test_every_week_page_has_mp_dot_with_correct_color_token(self, parsed_pages):
        """Every week page's .mp-dot must use the CSS var matching its mini-project arc."""
        failures = []
        for path, _, soup in parsed_pages:
            expected = self.EXPECTED_TOKEN.get(path.name)
            if not expected:
                continue
            dot = soup.select_one(".mp-dot")
            style = dot.get("style", "") if dot else ""
            if not dot or expected not in style:
                failures.append(f"{_rel(path)}: expected {expected} in style, got '{style}'")
        assert not failures, f"MP-dot color mismatches: {failures[:15]}"


class TestEthicsThread:
    ETHICS_WEEKS = {"week-03.html", "week-08.html", "week-12.html"}

    def test_ethics_thread_appears_exactly_on_weeks_3_8_12(self, parsed_pages):
        """Exactly weeks 3, 8, and 12 have an <aside class="ethics-thread">."""
        found = {
            path.name for path, _, soup in parsed_pages
            if soup.select_one("aside.ethics-thread")
        }
        assert found == self.ETHICS_WEEKS, f"ethics-thread found on {found}, expected {self.ETHICS_WEEKS}"


class TestSkipLink:
    def test_all_pages_have_skip_link_as_first_body_child(self, parsed_pages):
        """Every page's <body> must start with an <a class="skip-link" href="#main">."""
        failures = []
        for path, _, soup in parsed_pages:
            body = soup.find("body")
            first = body.find(True) if body else None
            if not first or "skip-link" not in first.get("class", []) or first.get("href") != "#main":
                failures.append(f"{_rel(path)}: body's first child is not a skip-link to #main")
        assert not failures, f"Skip-link issues: {failures[:15]}"

    def test_all_pages_have_main_with_id(self, parsed_pages):
        """Every page's <main class="content-wrapper"> must have id="main"."""
        failures = []
        for path, _, soup in parsed_pages:
            main = soup.select_one("main.content-wrapper")
            if not main or main.get("id") != "main":
                failures.append(f"{_rel(path)}: main.content-wrapper missing id='main'")
        assert not failures, f"Main-id issues: {failures[:15]}"


class TestHeaderFooterHero:
    def test_all_pages_have_site_header(self, parsed_pages):
        """Every page must contain a <header class="site-header">."""
        failures = [_rel(p) for p, _, s in parsed_pages if not s.select_one("header.site-header")]
        assert not failures, f"Pages missing header.site-header: {failures[:15]}"

    def test_all_pages_have_site_footer_with_text(self, parsed_pages):
        """Every page must contain a <footer class="site-footer"> with the course footer text."""
        failures = []
        for path, _, soup in parsed_pages:
            footer = soup.select_one("footer.site-footer")
            if not footer:
                failures.append(f"{_rel(path)}: missing footer.site-footer")
                continue
            if FOOTER_TEXT not in footer.get_text():
                failures.append(f"{_rel(path)}: footer text mismatch")
        assert not failures, f"Footer issues: {failures[:15]}"

    def test_all_pages_have_hero_with_h1(self, parsed_pages):
        """Every page must have a <section class="hero"> containing an <h1>."""
        failures = []
        for path, _, soup in parsed_pages:
            hero = soup.select_one("section.hero")
            if not hero:
                failures.append(f"{_rel(path)}: missing section.hero")
                continue
            if not hero.find("h1"):
                failures.append(f"{_rel(path)}: hero has no h1")
        assert not failures, f"Hero section issues: {failures[:15]}"


class TestNoLeftoverBranding:
    def test_no_programming_humanity_text(self, parsed_pages):
        """No page should contain leftover 'Programming Humanity' template branding."""
        failures = [
            _rel(path) for path, text, _ in parsed_pages
            if "Programming Humanity" in text
        ]
        assert not failures, f"Pages with leftover 'Programming Humanity' text: {failures[:15]}"

    def test_no_placeholder_notice(self, parsed_pages):
        """No page should contain a .placeholder-notice element."""
        failures = [
            _rel(path) for path, _, soup in parsed_pages
            if soup.select_one(".placeholder-notice")
        ]
        assert not failures, f"Pages with .placeholder-notice: {failures[:15]}"

    def test_no_stub_or_placeholder_strings(self, parsed_pages):
        """No page should contain literal 'Lorem ipsum', 'TBD', or 'TODO' text."""
        failures = []
        for path, text, _ in parsed_pages:
            hits = [s for s in ("Lorem ipsum", "TBD", "TODO") if s in text]
            if hits:
                failures.append(f"{_rel(path)}: {hits}")
        assert not failures, f"Pages with stub/placeholder strings: {failures[:15]}"


class TestThemeToggle:
    def test_all_pages_load_theme_init_before_stylesheet(self, parsed_pages):
        """theme-init.js must be present and precede the style.css link (avoids a flash of the wrong theme)."""
        failures = []
        for path, text, soup in parsed_pages:
            init_script = soup.find("script", src=lambda s: s and s.endswith("js/theme-init.js"))
            style_link = soup.find("link", rel="stylesheet", href=lambda h: h and "style.css" in h)
            if not init_script:
                failures.append(f"{_rel(path)}: missing theme-init.js")
                continue
            if not style_link or text.index(str(init_script)) > text.index(str(style_link)):
                failures.append(f"{_rel(path)}: theme-init.js does not precede style.css link")
        assert not failures, f"theme-init.js ordering issues: {failures[:15]}"

    def test_all_pages_load_motion_js(self, parsed_pages):
        """motion.js (scroll reveals, sticky header) must be present and resolvable on every page."""
        failures = []
        for path, _, soup in parsed_pages:
            script = soup.find("script", src=lambda s: s and s.endswith("js/motion.js"))
            if not script:
                failures.append(f"{_rel(path)}: missing js/motion.js")
                continue
            target = (path.parent / script["src"]).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: motion.js src '{script['src']}' does not resolve")
        assert not failures, f"motion.js issues: {failures[:15]}"

    def test_all_pages_load_theme_js(self, parsed_pages):
        """theme.js (button wiring) must be present and resolvable on every page."""
        failures = []
        for path, _, soup in parsed_pages:
            script = soup.find("script", src=lambda s: s and s.endswith("js/theme.js") and not s.endswith("theme-init.js"))
            if not script:
                failures.append(f"{_rel(path)}: missing js/theme.js")
                continue
            target = (path.parent / script["src"]).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: theme.js src '{script['src']}' does not resolve")
        assert not failures, f"theme.js issues: {failures[:15]}"

    def test_all_pages_have_toggle_and_lock_buttons(self, parsed_pages):
        """Every page's nav must contain the theme-toggle button and a hidden theme-lock button."""
        failures = []
        for path, _, soup in parsed_pages:
            toggle = soup.select_one("#theme-toggle")
            lock = soup.select_one("#theme-lock")
            if not toggle:
                failures.append(f"{_rel(path)}: missing #theme-toggle")
                continue
            if not lock or lock.has_attr("hidden") is False:
                failures.append(f"{_rel(path)}: #theme-lock missing or not hidden by default")
        assert not failures, f"Theme toggle/lock button issues: {failures[:15]}"


class TestWidgetRail:
    def test_all_pages_load_today_in_ai_js(self, parsed_pages):
        """today-in-ai.js must be present and resolvable on every page."""
        failures = []
        for path, _, soup in parsed_pages:
            script = soup.find("script", src=lambda s: s and s.endswith("js/today-in-ai.js"))
            if not script:
                failures.append(f"{_rel(path)}: missing js/today-in-ai.js")
                continue
            target = (path.parent / script["src"]).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: today-in-ai.js src '{script['src']}' does not resolve")
        assert not failures, f"today-in-ai.js issues: {failures[:15]}"

    def test_homepage_has_grid_and_here_card(self, site_root):
        """index.html must have the two-column grid, with Today-in-AI and This-Week stacked in the rail (same pattern as interior pages)."""
        soup_path = site_root / "index.html"
        import bs4
        soup = bs4.BeautifulSoup(soup_path.read_text(encoding="utf-8"), "lxml")
        assert soup.select_one(".home-grid") is not None, "index.html missing .home-grid"
        assert soup.select_one(".home-main") is not None, "index.html missing .home-main"
        rail = soup.select_one(".home-rail")
        assert rail is not None, "index.html missing .home-rail"
        assert rail.select_one("#today-in-ai-card") is not None, ".home-rail missing #today-in-ai-card"
        assert rail.select_one("#here-card") is not None, ".home-rail missing #here-card"

    def test_interior_pages_have_page_rail(self, site_root):
        """Every core/ and weeks/ page must have a .page-rail with hidden today-in-ai and here cards."""
        failures = []
        interior = sorted((site_root / "core").glob("*.html")) + sorted((site_root / "weeks").glob("*.html"))
        import bs4
        for path in interior:
            soup = bs4.BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
            rail = soup.select_one(".page-rail")
            if not rail:
                failures.append(f"{_rel(path)}: missing .page-rail")
                continue
            for card_id in ("today-in-ai-card", "here-card"):
                card = rail.select_one("#" + card_id)
                if not card:
                    failures.append(f"{_rel(path)}: .page-rail missing #{card_id}")
                elif not card.has_attr("hidden"):
                    failures.append(f"{_rel(path)}: #{card_id} not hidden by default")
        assert not failures, f"Interior page rail issues: {failures[:15]}"

    def test_bg_flourish_is_absent_sitewide(self, parsed_pages):
        """The decorative canvas background was retired; no page may reintroduce it.

        It was removed because its rays rendered a visible hard edge at the
        canvas boundary that resisted fixing. Kept as a regression guard rather
        than deleted so the canvas does not quietly come back.
        """
        failures = []
        for path, _, soup in parsed_pages:
            if soup.select_one("#bg-flourish"):
                failures.append(f"{_rel(path)}: unexpected #bg-flourish canvas")
            if soup.find("script", src=lambda s: s and s.endswith("js/hero-flourish.js")):
                failures.append(f"{_rel(path)}: unexpected js/hero-flourish.js")
        assert not failures, f"bg-flourish should be gone: {failures[:15]}"

    def test_all_pages_load_course_calendar_and_this_week_card_js(self, parsed_pages):
        """course-calendar.js and this-week-card.js must be present and resolvable on every page."""
        failures = []
        for path, _, soup in parsed_pages:
            for name in ("course-calendar.js", "this-week-card.js"):
                script = soup.find("script", src=lambda s, n=name: s and s.endswith("js/" + n))
                if not script:
                    failures.append(f"{_rel(path)}: missing js/{name}")
                    continue
                target = (path.parent / script["src"]).resolve()
                if not target.exists():
                    failures.append(f"{_rel(path)}: {name} src '{script['src']}' does not resolve")
        assert not failures, f"course-calendar.js/this-week-card.js issues: {failures[:15]}"


class TestContentNotEmpty:
    def test_page_content_has_minimum_text(self, parsed_pages):
        """Every page's .page-content div must have at least 20 characters of stripped text."""
        failures = []
        for path, _, soup in parsed_pages:
            content_div = soup.select_one(".page-content")
            if not content_div:
                failures.append(f"{_rel(path)}: missing .page-content")
                continue
            text = content_div.get_text(strip=True)
            if len(text) < 20:
                failures.append(f"{_rel(path)}: only {len(text)} chars")
        assert not failures, f"Pages with near-empty .page-content: {failures[:15]}"
