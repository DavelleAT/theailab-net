"""Keeps core/schedule.html agreeing with the week pages and the course calendar.

The schedule lists every week's dates. Those dates also live in each week page's
.session-meta line, and the week start dates and titles live a third time in
js/course-calendar.js, whose own header comment warns it "will silently go stale
otherwise". Nothing checked any of that.

The dates are written into the HTML by hand rather than generated, so that the
page needs no build step and no JavaScript to render its links. These tests are
what make that safe: edit a date in one place and forget the others, and this
fails and names the mismatch.

Comparisons are on parsed (month, day) values, never on strings. The week page
says "Tuesday & Thursday, September 8 & 10" and the schedule says "Sep 8 & 10";
both describe the same two dates, which is the invariant that matters.
"""
import re

import pytest
from bs4 import BeautifulSoup

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

TOTAL_WEEKS = 15


def _months_and_days(text):
    """Parse "Tuesday & Thursday, September 29 & October 1" into {(9,29),(10,1)}.

    Days attach to the most recently named month, which is what makes a range
    spanning a month boundary parse correctly. Numbers appearing before any
    month are ignored, so a trailing "(Weeks 3-5)" contributes nothing.
    """
    text = re.sub(r"&(amp|nbsp|ndash|mdash);", " ", text)
    dates = set()
    month = None
    for token in re.findall(r"[A-Za-z]+|\d+", text):
        if token.isalpha():
            key = token[:3].lower()
            if key in MONTHS:
                month = MONTHS[key]
        elif month is not None:
            day = int(token)
            if 1 <= day <= 31:
                dates.add((month, day))
    return dates


def _session_dates(week_soup):
    """The session-date line only.

    .session-meta holds a second paragraph naming the mini-project and its week
    range ("Part of Mini-Project 2 (Weeks 3-5)"). Those week numbers are not
    dates, so only the bolded first line is read.
    """
    line = week_soup.select_one(".session-meta p:first-child strong")
    assert line is not None, "week page has no bolded session-date line"
    return _months_and_days(line.get_text(" ", strip=True))


@pytest.fixture(scope="module")
def schedule(site_root):
    return BeautifulSoup(
        (site_root / "core" / "schedule.html").read_text(encoding="utf-8"), "lxml"
    )


@pytest.fixture(scope="module")
def calendar(site_root):
    """The arrays declared in js/course-calendar.js, read as data."""
    js = (site_root / "js" / "course-calendar.js").read_text(encoding="utf-8")

    def strings(name):
        body = re.search(name + r"\s*=\s*\[(.*?)\];", js, re.S)
        assert body, f"course-calendar.js has no {name} array"
        return re.findall(r'"([^"]*)"', body.group(1))

    ethics = re.search(r"ETHICS_WEEKS\s*=\s*\[([^\]]*)\]", js)
    assert ethics, "course-calendar.js has no ETHICS_WEEKS array"
    return {
        "starts": strings("WEEK_START_DATES"),
        "titles": strings("WEEK_TITLES"),
        "ethics": [int(n) for n in ethics.group(1).split(",")],
    }


@pytest.fixture(scope="module")
def week_pages(site_root):
    pages = {}
    for n in range(1, TOTAL_WEEKS + 1):
        path = site_root / "weeks" / f"week-{n:02d}.html"
        pages[n] = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    return pages


def _schedule_rows(schedule):
    """Map week number -> (date text, title text) from the timeline."""
    rows = {}
    for a in schedule.select("a.sched-week"):
        match = re.search(r"week-(\d+)\.html", a.get("href", ""))
        assert match, f"sched-week link with no week href: {a.get('href')}"
        rows[int(match.group(1))] = (
            a.select_one(".sched-date").get_text(" ", strip=True),
            a.select_one(".sched-title").get_text(" ", strip=True),
        )
    return rows


class TestScheduleCoverage:
    def test_every_week_appears_exactly_once(self, schedule):
        found = [
            int(re.search(r"week-(\d+)\.html", a["href"]).group(1))
            for a in schedule.select("a.sched-week")
        ]
        assert sorted(found) == list(range(1, TOTAL_WEEKS + 1)), (
            f"schedule weeks are {sorted(found)}, expected 1..{TOTAL_WEEKS}"
        )

    def test_weeks_are_in_chronological_order(self, schedule):
        found = [
            int(re.search(r"week-(\d+)\.html", a["href"]).group(1))
            for a in schedule.select("a.sched-week")
        ]
        assert found == sorted(found), f"schedule weeks are out of order: {found}"


class TestScheduleMatchesWeekPages:
    def test_dates_match_each_week_page(self, schedule, week_pages):
        rows = _schedule_rows(schedule)
        failures = []
        for n, soup in week_pages.items():
            expected = _session_dates(soup)
            actual = _months_and_days(rows[n][0])
            if actual != expected:
                failures.append(
                    f"week {n}: schedule says {sorted(actual)}, "
                    f"week page says {sorted(expected)}"
                )
        assert not failures, f"Schedule dates disagree with week pages: {failures}"

    def test_ethics_weeks_marked_consistently(self, schedule, week_pages):
        marked = {
            int(re.search(r"week-(\d+)\.html", a["href"]).group(1))
            for a in schedule.select("a.sched-week[data-ethics]")
        }
        actual = {n for n, s in week_pages.items() if s.select_one(".ethics-thread")}
        assert marked == actual, (
            f"schedule marks weeks {sorted(marked)} as ethics threads, "
            f"but .ethics-thread appears on {sorted(actual)}"
        )


class TestDeadlinesReachTheSchedule:
    def test_every_week_page_deadline_appears_on_the_schedule(self, schedule, week_pages):
        """A due date students can only find by opening a week page is a bug."""
        sched_dates = _months_and_days(
            " ".join(el.get_text(" ", strip=True) for el in schedule.select(".sched-due"))
        )
        failures = []
        for n, soup in week_pages.items():
            for strong in soup.select(".content-section strong"):
                text = strong.get_text(" ", strip=True)
                # Read per sentence, since a deadline line can also name dates
                # that are not deadlines: week 13 reads "MP4 presentations
                # Nov 17/19. MP4 due Friday, November 20." Only the second
                # sentence carries a due date; the first names class sessions.
                for sentence in re.split(r"(?<=\.)\s+", text):
                    if "due" not in sentence.lower():
                        continue
                    for date in _months_and_days(sentence):
                        if date not in sched_dates:
                            failures.append(f"week {n}: {sentence!r} (missing {date})")
        assert not failures, f"Deadlines missing from the schedule: {failures}"


class TestListingsShareOneSetOfTitles:
    """js/course-calendar.js holds the canonical week titles.

    A week page's <h1> is a deliberately shortened display form ("Hooks
    Architecture" for what the listings call "Hooks Architecture and
    Guardrails"), because the hero sets it at up to 76px and the full title
    wraps to three lines. So the <h1> is not compared here. What must agree are
    the places that present a week in a list: the schedule timeline, the
    homepage course arc, and the calendar they both draw from.
    """

    def test_schedule_titles_match_the_calendar(self, calendar, schedule):
        rows = _schedule_rows(schedule)
        failures = []
        for n in range(1, TOTAL_WEEKS + 1):
            expected = calendar["titles"][n - 1]
            actual = rows[n][1].strip()
            if actual != expected:
                failures.append(f"week {n}: schedule {actual!r} vs calendar {expected!r}")
        assert not failures, f"Schedule titles disagree with course-calendar.js: {failures}"

    def test_homepage_arc_titles_match_the_calendar(self, calendar, site_root):
        soup = BeautifulSoup(
            (site_root / "index.html").read_text(encoding="utf-8"), "lxml"
        )
        failures = []
        for a in soup.select("a.arc-week"):
            n = int(a["data-week"])
            expected = calendar["titles"][n - 1]
            actual = a.select_one(".arc-title").get_text(" ", strip=True)
            if actual != expected:
                failures.append(f"week {n}: arc {actual!r} vs calendar {expected!r}")
        assert not failures, f"Course arc titles disagree with course-calendar.js: {failures}"


class TestCourseCalendarMatchesWeekPages:
    """Closes the drift the course-calendar.js header comment warns about."""

    def test_start_dates_fall_within_each_week(self, calendar, week_pages):
        failures = []
        for n, soup in week_pages.items():
            _, month, day = (int(p) for p in calendar["starts"][n - 1].split("-"))
            page_dates = _session_dates(soup)
            if (month, day) not in page_dates:
                failures.append(
                    f"week {n}: calendar starts {month}-{day}, "
                    f"page lists {sorted(page_dates)}"
                )
        assert not failures, f"course-calendar.js start dates are stale: {failures}"

    def test_ethics_weeks_match(self, calendar, week_pages):
        actual = sorted(n for n, s in week_pages.items() if s.select_one(".ethics-thread"))
        assert sorted(calendar["ethics"]) == actual, (
            f"course-calendar.js lists ethics weeks {sorted(calendar['ethics'])}, "
            f"but .ethics-thread appears on {actual}"
        )
