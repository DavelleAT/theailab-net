// "Today in AI" — live headlines from Hacker News, shown as a supplementary
// widget (never course content, never authoritative). See
// docs/design-spec_phase3_website-revision_v1_20260903.md Part 3.
//
// Headlines are chosen for the week the reader is on: on a week page, that
// week; anywhere else, whichever week the semester is currently in. The per-week
// search terms live in js/course-calendar.js as WEEK_TOPICS.
//
// Two queries back the card. The topic query looks across the last month, since
// news about, say, the Model Context Protocol does not appear daily. The general
// query is the original behaviour, today's top AI stories, and fills the card
// whenever the topic turns up less than a full set. So the card is topical when
// it can be and still current when it cannot.
//
// Data source is the public, keyless HN Algolia Search API. Results are cached
// in localStorage per week and per six-hour window, so the card turns over about
// four times a day without re-fetching on every page view. If the fetch fails,
// or nothing clears the relevance filter, the card does not render at all. It is
// supplementary, so failing invisibly is correct.

(function () {
  var CACHE_PREFIX = "today-in-ai:v2:";
  // How often the card turns over. Also the cache lifetime, since a new window
  // means a new key and the old entry is simply never read again.
  var ROTATION_MS = 6 * 60 * 60 * 1000;
  var SHOW_COUNT = 3;
  var POOL_SIZE = 8;
  var TOPIC_WINDOW_DAYS = 30;

  var KEYWORDS = [
    "ai", "llm", "gpt", "openai", "anthropic", "claude", "gemini",
    "machine learning", "neural", "agent"
  ];

  var KEYWORD_PATTERNS = KEYWORDS.map(function (kw) {
    // Word-boundary match — a plain substring check would let short keywords
    // like "ai" match inside unrelated words ("Ukrainian", "maintain",
    // "portrait"), which happened during testing.
    return new RegExp("\\b" + kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b", "i");
  });

  function isRelevant(title) {
    return KEYWORD_PATTERNS.some(function (re) { return re.test(title); });
  }

  /* ---- which week are we speaking to ---- */

  // A week page names its own week in the filename. Everywhere else follows the
  // calendar, which is also what the "This Week" card does, so the two agree.
  function activeWeek() {
    var fromPath = window.location.pathname.match(/week-(\d{2})\.html$/);
    if (fromPath) return parseInt(fromPath[1], 10);
    var CC = window.CourseCalendar;
    return CC ? CC.currentWeekNumber(CC.today()) : null;
  }

  function topicFor(week) {
    var CC = window.CourseCalendar;
    if (!week || !CC || !CC.weekTopic) return "";
    return CC.weekTopic(week);
  }

  /* ---- fetching ---- */

  function search(params) {
    var url = "https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=100&" + params;
    return fetch(url).then(function (res) {
      if (!res.ok) throw new Error("HN API error " + res.status);
      return res.json();
    });
  }

  // Words worth matching a headline against, from a topic like "Claude Code CLI".
  // Two-letter words are dropped as noise, except that nothing in the topics is
  // that short except "AI", which the generic keyword list already covers.
  function topicPatterns(topic) {
    return topic
      .split(/\s+/)
      .filter(function (w) { return w.length >= 3; })
      .map(function (w) {
        return new RegExp("\\b" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b", "i");
      });
  }

  function matchesAny(patterns, title) {
    return patterns.some(function (re) { return re.test(title); });
  }

  function toStories(hits, accept, keepApiOrder) {
    var candidates = hits.filter(function (h) {
      return h.title && h.url && accept(h.title);
    });
    // Topic results keep the API's relevance order. Re-sorting them by points
    // was surfacing high-scoring stories that barely matched the query at all
    // ("Risklytics – Insurance brokerage") over genuine matches with fewer
    // points. Relevance is the whole reason for running a topic query.
    if (!keepApiOrder) {
      candidates.sort(function (a, b) { return (b.points || 0) - (a.points || 0); });
    }
    return candidates.slice(0, POOL_SIZE).map(function (h) {
      return { title: h.title, url: h.url, points: h.points || 0 };
    });
  }

  function fetchTopic(topic) {
    if (!topic) return Promise.resolve([]);
    var since = Math.floor((Date.now() - TOPIC_WINDOW_DAYS * 86400000) / 1000);
    var patterns = topicPatterns(topic);
    return search(
      "query=" + encodeURIComponent(topic) +
      "&numericFilters=created_at_i%3E" + since
    ).then(function (data) {
      // The headline itself has to carry a word from the topic. Algolia ranks
      // loose matches into the results too, and the generic AI keyword list
      // cannot stand in here: it would drop a squarely on-topic headline like
      // "Mcploitable, the Metasploitable of the Model Context Protocol", which
      // names no AI term at all.
      return toStories(data.hits || [], function (title) {
        return matchesAny(patterns, title);
      }, true);
    });
  }

  function fetchGeneral() {
    var todayStart = Math.floor(new Date().setHours(0, 0, 0, 0) / 1000);
    // The relevance-sorted "search" endpoint is used deliberately instead of
    // "search_by_date": an earlier version used the chronological one and, with
    // a modest hitsPerPage, only ever sampled stories posted in the last few
    // minutes (near-zero points), never the day's actual top stories.
    return search("numericFilters=created_at_i%3E" + todayStart).then(function (data) {
      return toStories(data.hits || [], isRelevant, false);
    });
  }

  function dedupe(stories) {
    var seen = {};
    return stories.filter(function (s) {
      if (seen[s.url]) return false;
      seen[s.url] = true;
      return true;
    });
  }

  // Topic stories first, then today's general AI stories to fill any shortfall.
  function fetchStories(topic) {
    return fetchTopic(topic).then(function (topical) {
      var count = topical.length;
      if (count >= SHOW_COUNT) {
        return { stories: topical, topical: count };
      }
      return fetchGeneral().then(function (general) {
        return {
          stories: dedupe(topical.concat(general)),
          topical: count
        };
      });
    });
  }

  /* ---- cache ---- */

  function cacheKey(week) {
    return CACHE_PREFIX + (week || "none") + ":" + Math.floor(Date.now() / ROTATION_MS);
  }

  function loadCache(week) {
    try {
      var raw = localStorage.getItem(cacheKey(week));
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      return parsed && parsed.stories && parsed.stories.length ? parsed : null;
    } catch (e) {
      return null;
    }
  }

  function saveCache(week, payload) {
    try {
      localStorage.setItem(cacheKey(week), JSON.stringify(payload));
      // Rotating the key leaves the previous window's entry behind, so clear
      // out anything belonging to an older window on the way past.
      var current = cacheKey(week);
      for (var i = localStorage.length - 1; i >= 0; i--) {
        var key = localStorage.key(i);
        if (key && key.indexOf(CACHE_PREFIX) === 0 && key !== current) {
          localStorage.removeItem(key);
        }
      }
    } catch (e) {
      /* storage unavailable — the card just re-fetches next page view */
    }
  }

  /* ---- rendering ---- */

  function cardContent(payload, week, topic) {
    var container = document.createElement("div");

    var label = document.createElement("div");
    label.className = "news-label";
    label.textContent = "Today in AI";
    container.appendChild(label);

    // Only claim a topic when the topic query actually supplied something,
    // otherwise the card would credit a subject it is not showing.
    if (topic && payload.topical > 0) {
      var topicLine = document.createElement("div");
      topicLine.className = "news-topic";
      topicLine.textContent = "Week " + week + " · " + topic;
      container.appendChild(topicLine);
    }

    for (var i = 0; i < Math.min(payload.stories.length, SHOW_COUNT); i++) {
      var p = document.createElement("p");
      p.className = "news-headline";
      var a = document.createElement("a");
      a.href = payload.stories[i].url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "“" + payload.stories[i].title + "”";
      p.appendChild(a);
      container.appendChild(p);
    }

    var source = document.createElement("p");
    source.className = "news-source";
    source.textContent = "via Hacker News";
    container.appendChild(source);

    var caption = document.createElement("p");
    caption.className = "news-caption";
    caption.textContent = "The field doesn't pause for a syllabus. Here's today's "
      + "version of it, next to where you are in the course.";
    container.appendChild(caption);

    return container;
  }

  function render(payload, week, topic) {
    if (!payload || !payload.stories || !payload.stories.length) return;
    var card = document.getElementById("today-in-ai-card");
    if (!card) return;
    card.innerHTML = "";
    card.appendChild(cardContent(payload, week, topic));
    card.hidden = false;
  }

  function init() {
    if (!document.getElementById("today-in-ai-card")) return;

    var week = activeWeek();
    var topic = topicFor(week);

    var cached = loadCache(week);
    if (cached) {
      render(cached, week, topic);
      return;
    }

    fetchStories(topic)
      .then(function (payload) {
        if (!payload.stories.length) return;
        saveCache(week, payload);
        render(payload, week, topic);
      })
      .catch(function () {
        /* offline, API down, etc. — no card, no error surfaced */
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
