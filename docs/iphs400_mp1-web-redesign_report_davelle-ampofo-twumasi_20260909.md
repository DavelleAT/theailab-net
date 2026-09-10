# IPHS 400 Mini-Project 1: Course Website Redesign

**Davelle Ampofo-Twumasi** · 9 September 2026

**Live site:** https://davelleat.github.io/theailab-net/
**Repository:** https://github.com/DavelleAT/theailab-net

---

## (a) What I improved

A note on what I started from. The site I inherited was a plain port with system fonts, no map of the semester, no news widget, and a schedule page with no dates on it. Several of the things I describe below are therefore second attempts at my own earlier work rather than fixes to someone else's. The type system, the course map, and the news widget were all mine before this pass, and I rewrote or replaced all three. Being willing to throw out my own week-old work turned out to be the most useful habit I picked up here.

**Type system.** The site I started from had no web fonts at all, just the browser's default stacks. My first pass at fixing that picked Fraunces, Newsreader, and Quicksand. That was a mistake I had to see on screen for a while before I could name it: Quicksand is a rounded geometric sans, and it was making an upper-level CS course read like a children's product. I replaced my own stack with Instrument Serif for display, Inter for reading and interface text, and JetBrains Mono for labels, dates, and numerals. The mono labels do most of the work: they give the page a technical register that suits a course about agentic software engineering. Instrument Serif ships a single weight, so heading hierarchy comes from size and spacing rather than bold, which forced a cleaner scale than I would have written otherwise.

**Course arc.** The site I inherited had no map of the semester at all. I built one in an earlier pass: an SVG of fifteen colored dots along a wavy path. Coming back to it with fresh eyes, it looked like a board game, so I threw it out and rebuilt it as a proportional phase band over an indexed list of all fifteen weeks, with the current week marked. The index is now real navigation instead of decoration sitting next to it. Replacing my own work was the right call, and it is the change I am most confident about.

**Motion.** A new `js/motion.js` adds scroll reveals, a masthead that condenses once you scroll, and progress bars that draw in. Targets are selected in that one file instead of being marked up across 22 pages. Everything degrades: no JavaScript, no `IntersectionObserver`, or a visitor who has asked for reduced motion all get the finished page with nothing hidden.

**Schedule page.** This was the weakest page on the site. It listed the same fifteen weeks as the homepage with less information and no dates at all, while every session date, both recesses, and the semester bookends were compressed into a single paragraph of prose at the top. I rebuilt it as the semester timeline: each week shows its class dates, the five assignment deadlines sit as their own rows in chronological position, and the recesses appear inline where they actually fall.

**Calendar export.** Because the schedule now holds structured dates, I generate `iphs400.ics` from it: 38 events covering 28 class sessions, 5 deadlines, 2 recesses, and the three semester-close dates. Students can subscribe in Google Calendar, Apple Calendar, or Outlook instead of remembering to check a page. Sessions are timed events carrying a full `VTIMEZONE` definition, because the semester crosses the November daylight-saving change and without it every session after 1 November shows up an hour off.

**Today in AI.** This widget is mine, not something the starting site had. The idea was that a course about a field moving this fast should show the field moving, so the page pulls live AI headlines from Hacker News beside the week you are reading. My first version ran one fixed keyword list against stories posted that day, which meant all 22 pages showed identical headlines and the feature was closer to decoration than information. Each week now carries its own search terms, so the headlines beside Week 8 are about Codex CLI and the ones beside Week 12 are about LLM costs.

**Accessibility.** I measured the palette and found the light theme was below WCAG AA. Both failing colors were mine. I had pulled the teal from the instructor's own site because I liked it, and it sat at 3.15:1 against the background, with the muted grey at 3.51:1, against a 4.5:1 floor. That covered every body link and, after I shrank the labels during the type pass, nearly every label on the site. I darkened both while holding hue and saturation, solving against the tinted background of the highlighted row rather than the plain one, since that is the worst case. Dark mode was already past 7:1.

**Testing.** The suite went from 33 tests to 67. More useful than the count is what they now cover: the schedule's dates are checked against the week pages, the calendar is regenerated and compared against the committed file, and the palette's contrast ratios are computed from the stylesheet. Each of these guards something that would otherwise rot silently.

### Bugs the work surfaced

Three worth naming, because they were not on the plan:

1. A nav-consistency test caught that `syllabus.html` and `assignments.html` had never received the Schedule link. `404.html` was missing it too, and the test had been skipping that file for unrelated reasons.
2. The page title went invisible on two pages. I had hidden it with a rule keyed on a class set before first paint, so when the script that reveals it failed to load, the title stayed hidden with its space still reserved. Every other reveal was keyed on an attribute the script adds itself, which cannot exist unless the script ran. The title had opted out of that guarantee.
3. My first diagnosis of that bug was wrong. I blamed a timing interaction with cross-document view transitions, built machinery around that theory, then found the real cause was a stale cached page pointing at a script I had deleted. I removed the machinery.

---

## (b) Resources and why

**Reference sites.** I pulled the teal accent from **jonachun.com**. For layout and motion I worked from four sites found through **awwwards.com**: **ecidni.com**, **madewithgsap.com**, **creativeans.com**, and **thenest.pl**. What they share is animation-forward design that still reads serious, which is what I wanted. A school site can move without being playful.

**AI usage.** I used Claude Code throughout, and the prompts that mattered were the ones that constrained it rather than the ones that asked for output. Three examples:

- *"i dont want icons, that is ai slop"*. This killed a proposed icon system before it was built.
- *"spec it out let me see"*. This forced a written spec before the Schedule rebuild. The spec surfaced a decision I would otherwise have made badly: whether to generate the page from JavaScript or keep it static. Static won, because the repo's own tests parse HTML.
- The most useful thing I did was refuse to accept plausible output. The first fifteen search topics for the news widget looked fine. I had them measured against the live API instead, and six returned nothing at all. All six were four words or longer. Every topic was rewritten and re-measured, and the counts are recorded in the source so the next person can see whether an edit helped.

**Tools and APIs.** The Hacker News Algolia Search API (public, keyless) for headlines, Google Fonts for the type, pytest with BeautifulSoup for the test suite, and the `icalendar` library to validate the calendar output rather than trusting my own generator.

**Deliberate non-choices.** No framework, no build step, no dependencies in the shipped site. It is HTML, CSS, and vanilla JavaScript, which is what a course site should be if it is going to outlive the semester.

---

## (c) Future improvements

**Mobile verification.** I wrote the breakpoints but never confirmed them on a real device, and the browser tooling I had would not give me a true narrow viewport. This is the honest gap and the first thing I would close.

**The interior pages.** Syllabus, Assignments, and Policies still have not had a structural pass. They are long text with the new type applied and nothing else.

**Site search.** Twenty-two pages and no way to answer "which week covers hooks" without clicking through.

**A next-deadline indicator.** The deadline data is now structured, so surfacing the next one site-wide is cheap.

**CI.** The test suite only protects the site if it runs. A GitHub Action on push would close that.
