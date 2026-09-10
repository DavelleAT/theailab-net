"""Keeps iphs400.ics agreeing with the schedule it was generated from.

The calendar is a committed static file rather than something built on request,
so it can be linked, downloaded, and subscribed to without a server or any
JavaScript. The cost of committing generated output is that it goes stale
silently: someone moves a deadline on the schedule page, the tests there pass
because the week pages agree, and the calendar students already subscribed to
keeps showing the old date.

So the generator is required to be deterministic, and this regenerates and
compares. If it fails, run scripts/build_calendar.py and commit the result.
"""
import re
import subprocess
import sys

import pytest

pytest.importorskip("bs4")


def _build_module(site_root):
    """Import scripts/build_calendar.py without installing anything."""
    import importlib.util

    path = site_root / "scripts" / "build_calendar.py"
    spec = importlib.util.spec_from_file_location("build_calendar", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder(site_root):
    return _build_module(site_root)


@pytest.fixture(scope="module")
def ics_text(site_root):
    path = site_root / "iphs400.ics"
    assert path.exists(), "iphs400.ics is missing; run scripts/build_calendar.py"
    # Decoded from bytes rather than read_text(), whose universal-newline
    # handling would turn the CRLF line endings iCalendar requires into LF and
    # quietly break both the comparison and the line-length check below.
    return path.read_bytes().decode("utf-8")


class TestCommittedFileIsCurrent:
    def test_regenerating_produces_the_committed_file(self, builder, ics_text):
        assert builder.build() == ics_text, (
            "iphs400.ics is out of date with core/schedule.html. "
            "Run scripts/build_calendar.py and commit the result."
        )

    def test_generator_is_deterministic(self, builder):
        """Two builds must be byte-identical, or the check above is meaningless."""
        assert builder.build() == builder.build()


class TestCalendarContents:
    def test_every_week_has_a_session_for_each_class_date(self, builder, ics_text, site_root):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            (site_root / "core" / "schedule.html").read_text(encoding="utf-8"), "lxml"
        )
        expected = 0
        for link in soup.select("a.sched-week"):
            expected += len(
                builder.parse_dates(link.select_one(".sched-date").get_text(" ", strip=True))
            )
        actual = len(re.findall(r"UID:week-\d+-session-\d+@", ics_text))
        assert actual == expected, (
            f"calendar has {actual} class sessions, schedule lists {expected}"
        )

    def test_every_deadline_on_the_schedule_is_in_the_calendar(self, ics_text, site_root):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            (site_root / "core" / "schedule.html").read_text(encoding="utf-8"), "lxml"
        )
        due_rows = soup.select(".sched-row.sched-due")
        assert due_rows, "schedule has no deadline rows"
        found = len(re.findall(r"UID:due-\d{8}-", ics_text))
        assert found == len(due_rows), (
            f"calendar has {found} deadlines, schedule lists {len(due_rows)}"
        )

    def test_sessions_carry_a_timezone_rather_than_floating(self, ics_text):
        """A floating time lands at the wrong hour for anyone outside Ohio."""
        # Only DTSTART inside VEVENT blocks. VTIMEZONE carries its own DTSTART
        # lines for the daylight and standard rules, and those correctly have
        # no TZID of their own.
        events = re.findall(r"BEGIN:VEVENT\r\n(.*?)END:VEVENT", ics_text, re.S)
        assert events, "calendar has no events"
        starts = [
            m.group(0)
            for body in events
            for m in re.finditer(r"^DTSTART[^:\r\n]*:", body, re.M)
        ]
        timed = [s for s in starts if "VALUE=DATE" not in s]
        assert timed, "calendar has no timed events"
        untimed = [s for s in timed if "TZID=America/New_York" not in s]
        assert not untimed, f"timed events without a timezone: {untimed[:3]}"

    def test_timezone_definition_is_present(self, ics_text):
        """TZID references are meaningless to a client without the definition."""
        assert "BEGIN:VTIMEZONE" in ics_text
        assert "TZID:America/New_York" in ics_text
        # Both halves of the year, since the semester crosses the November change.
        assert "TZNAME:EDT" in ics_text and "TZNAME:EST" in ics_text

    def test_uids_are_unique(self, ics_text):
        uids = re.findall(r"^UID:(.+)$", ics_text, re.M)
        duplicates = {u for u in uids if uids.count(u) > 1}
        assert not duplicates, f"duplicate UIDs would collide on re-subscribe: {duplicates}"

    def test_lines_stay_within_the_ics_length_limit(self, ics_text):
        long_lines = [
            line for line in ics_text.split("\r\n")
            if len(line.encode("utf-8")) > 75
        ]
        assert not long_lines, f"unfolded lines over 75 octets: {long_lines[:2]}"


class TestSchedulePageOffersTheCalendar:
    def test_schedule_links_to_the_calendar_file(self, site_root):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            (site_root / "core" / "schedule.html").read_text(encoding="utf-8"), "lxml"
        )
        link = soup.find("a", href=re.compile(r"\.ics$"))
        assert link, "schedule.html does not link to the calendar"
        target = (site_root / "core" / link["href"]).resolve()
        assert target.exists(), f"calendar link does not resolve: {link['href']}"


class TestGeneratorCheckMode:
    def test_check_flag_passes_against_the_committed_file(self, site_root):
        """--check is what a hook or CI step would call."""
        result = subprocess.run(
            [sys.executable, str(site_root / "scripts" / "build_calendar.py"), "--check"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
