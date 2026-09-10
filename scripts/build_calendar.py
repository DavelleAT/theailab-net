#!/usr/bin/env python3
"""Generate iphs400.ics from core/schedule.html.

The schedule page is the source: it already carries every session date,
deadline, and recess, and tests/test_unit_schedule.py holds it to the week
pages. Reading it here means the calendar cannot describe a different semester
than the site does. Class time and room come from the course-details table on
index.html for the same reason.

Output is deterministic, so tests/test_unit_calendar.py can regenerate and
compare against the committed file. That is what catches a schedule edit that
never made it into the calendar.

Usage: python3 scripts/build_calendar.py [--check]
  --check  exit non-zero if the committed file is out of date, write nothing
"""
import argparse
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SITE_ROOT = Path(__file__).resolve().parent.parent
SCHEDULE = SITE_ROOT / "core" / "schedule.html"
INDEX = SITE_ROOT / "index.html"
OUTPUT = SITE_ROOT / "iphs400.ics"

YEAR = 2026
COURSE = "IPHS 400"
DOMAIN = "theailab.net"

# Fixed rather than "now": a timestamp that moved on every run would make the
# committed file differ from a fresh build on every check.
DTSTAMP = "20260901T000000Z"

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# US eastern rules, so a reader's calendar resolves the 2:40 PM sessions
# correctly either side of the 1 November 2026 changeover rather than
# shifting them by an hour.
VTIMEZONE = """BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE"""


def parse_dates(text):
    """["Sep 29", "Oct 1"] style text into ordered (month, day) pairs.

    Days attach to the most recently named month, so a span crossing a month
    boundary parses correctly. Order is preserved because a week's two sessions
    are separate events while a recess is one range.
    """
    text = re.sub(r"&(amp|nbsp|ndash|mdash);", " ", text)
    out = []
    month = None
    for token in re.findall(r"[A-Za-z]+|\d+", text):
        if token.isalpha():
            key = token[:3].lower()
            if key in MONTHS:
                month = MONTHS[key]
        elif month is not None:
            day = int(token)
            if 1 <= day <= 31:
                out.append((month, day))
    return out


def course_details():
    """Class time and room, from the table on the homepage."""
    soup = BeautifulSoup(INDEX.read_text(encoding="utf-8"), "lxml")
    found = {}
    for row in soup.select("table tr"):
        header, value = row.find("th"), row.find("td")
        if header and value:
            found[header.get_text(strip=True)] = value.get_text(strip=True)

    times = found.get("Schedule", "")
    match = re.search(r"(\d{1,2}):(\d{2})\s*[–-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)", times)
    if not match:
        sys.exit(f"could not read class times from index.html: {times!r}")

    sh, sm, eh, em, meridiem = match.groups()
    sh, sm, eh, em = int(sh), int(sm), int(eh), int(em)
    # "2:40-4:00 PM": the meridiem is stated once and governs both ends, so a
    # start hour below 12 is afternoon too.
    if meridiem == "PM":
        if eh < 12:
            eh += 12
        if sh < 12:
            sh += 12

    room = found.get("Location", "")
    if not room:
        sys.exit("could not read location from index.html")
    return (sh, sm), (eh, em), room


def fold(line):
    """Wrap to the 75-octet limit, continuations marked by a leading space."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    chunks, current = [], b""
    for char in line:
        char_bytes = char.encode("utf-8")
        limit = 75 if not chunks else 74
        if len(current) + len(char_bytes) > limit:
            chunks.append(current)
            current = b""
        current += char_bytes
    chunks.append(current)
    return "\r\n ".join(chunk.decode("utf-8") for chunk in chunks)


def escape(text):
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def ymd(month, day, offset=0):
    from datetime import date, timedelta
    return (date(YEAR, month, day) + timedelta(days=offset)).strftime("%Y%m%d")


def event(uid, summary, lines):
    body = [f"BEGIN:VEVENT", f"UID:{uid}@{DOMAIN}", f"DTSTAMP:{DTSTAMP}"]
    body += lines
    body.append(f"SUMMARY:{escape(summary)}")
    body.append("END:VEVENT")
    return body


def build():
    soup = BeautifulSoup(SCHEDULE.read_text(encoding="utf-8"), "lxml")
    (start_h, start_m), (end_h, end_m), room = course_details()

    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{DOMAIN}//{COURSE}//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{COURSE}: Frontiers in AI",
        "X-WR-TIMEZONE:America/New_York",
    ]
    out += VTIMEZONE.split("\n")

    for row in soup.select(".sched-row"):
        classes = row.get("class", [])
        link = row.select_one("a.sched-week")
        node = link or row
        date_text = node.select_one(".sched-date").get_text(" ", strip=True)
        title = node.select_one(".sched-title").get_text(" ", strip=True)
        dates = parse_dates(date_text)
        if not dates:
            sys.exit(f"no date parsed from schedule row: {date_text!r}")

        if link:
            week = int(re.search(r"week-(\d+)\.html", link["href"]).group(1))
            # One timed event per class session, so two-session weeks appear
            # twice rather than as a single block spanning the gap between them.
            for index, (month, day) in enumerate(dates, start=1):
                out += event(
                    f"week-{week:02d}-session-{index}",
                    f"{COURSE}: Week {week} — {title}",
                    [
                        f"DTSTART;TZID=America/New_York:{ymd(month, day)}T"
                        f"{start_h:02d}{start_m:02d}00",
                        f"DTEND;TZID=America/New_York:{ymd(month, day)}T"
                        f"{end_h:02d}{end_m:02d}00",
                        f"LOCATION:{escape(room)}",
                        f"URL:https://{DOMAIN}/weeks/week-{week:02d}.html",
                    ],
                )
        else:
            # Deadlines and recesses are all-day. A single date covers one day;
            # a span is written as its first and last, so DTEND is the day after
            # the last, since the property is exclusive.
            first, last = dates[0], dates[-1]
            kind = "due" if "sched-due" in classes else "break"
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
            out += event(
                f"{kind}-{ymd(*first)}-{slug}",
                f"{COURSE}: {title}" if kind == "due" else title,
                [
                    f"DTSTART;VALUE=DATE:{ymd(*first)}",
                    f"DTEND;VALUE=DATE:{ymd(*last, offset=1)}",
                    "TRANSP:TRANSPARENT",
                ],
            )

    out.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in out) + "\r\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="verify the committed file is current, write nothing")
    args = parser.parse_args()

    calendar = build()
    if args.check:
        if not OUTPUT.exists():
            sys.exit(f"{OUTPUT.name} does not exist; run scripts/build_calendar.py")
        # Read as bytes. iCalendar requires CRLF, and read_text() would collapse
        # those to LF on the way in, so the comparison could never match.
        if OUTPUT.read_bytes() != calendar.encode("utf-8"):
            sys.exit(f"{OUTPUT.name} is out of date; run scripts/build_calendar.py")
        print(f"{OUTPUT.name} is up to date")
        return

    OUTPUT.write_text(calendar, encoding="utf-8", newline="")
    events = calendar.count("BEGIN:VEVENT")
    print(f"wrote {OUTPUT.relative_to(SITE_ROOT)} ({events} events)")


if __name__ == "__main__":
    main()
