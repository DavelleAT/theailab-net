// "Today in AI" — a live headline pulled from Hacker News, shown as a
// supplementary widget (never course content, never authoritative). See
// docs/design-spec_phase3_website-revision_v1_20260903.md Part 3.
//
// Data source: the public, keyless HN Algolia Search API. The list of
// today's top AI-relevant stories is fetched at most once per hour per
// visitor (cached in localStorage); a random story from that cached list
// is shown on every page load/navigation/refresh, so visitors see variety
// across the same session without extra API calls. If the fetch fails, or
// no story matches the AI-relevance keyword filter, the card simply does
// not render — this is supplementary, not core, so failing invisibly is
// correct.

(function () {
  var CACHE_KEY = "today-in-ai-cache";
  var CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour
  var CANDIDATE_COUNT = 8;
  var KEYWORDS = [
    "ai", "llm", "gpt", "openai", "anthropic", "claude", "gemini",
    "machine learning", "neural", "agent"
  ];

  function loadCache() {
    try {
      var raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (Date.now() - parsed.fetchedAt > CACHE_TTL_MS) return null;
      if (!parsed.stories || !parsed.stories.length) return null;
      return parsed;
    } catch (e) {
      return null;
    }
  }

  function saveCache(stories) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ stories: stories, fetchedAt: Date.now() }));
    } catch (e) {
      /* storage unavailable — just won't persist across pages */
    }
  }

  var KEYWORD_PATTERNS = KEYWORDS.map(function (kw) {
    // Word-boundary match — a plain substring check would let short
    // keywords like "ai" match inside unrelated words ("Ukrainian",
    // "maintain", "portrait"), which happened during testing.
    return new RegExp("\\b" + kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b", "i");
  });

  function isRelevant(title) {
    return KEYWORD_PATTERNS.some(function (re) { return re.test(title); });
  }

  function pickTopStories(hits) {
    var candidates = hits.filter(function (h) {
      return h.title && h.url && isRelevant(h.title);
    });
    candidates.sort(function (a, b) { return (b.points || 0) - (a.points || 0); });
    return candidates.slice(0, CANDIDATE_COUNT).map(function (h) {
      return { title: h.title, url: h.url, points: h.points || 0 };
    });
  }

  function fetchTopStories() {
    var todayStartEpoch = Math.floor(new Date().setHours(0, 0, 0, 0) / 1000);
    // The "search" endpoint (relevance/points/comments sort) is used
    // deliberately instead of "search_by_date" (chronological) — an earlier
    // version used search_by_date and, combined with a modest hitsPerPage,
    // only ever sampled the handful of stories posted in the last few
    // minutes (near-zero points), never the day's actual top stories.
    var api =
      "https://hn.algolia.com/api/v1/search?tags=story&numericFilters=created_at_i%3E" +
      todayStartEpoch + "&hitsPerPage=100";
    return fetch(api)
      .then(function (res) {
        if (!res.ok) throw new Error("HN API error " + res.status);
        return res.json();
      })
      .then(function (data) { return pickTopStories(data.hits || []); });
  }

  function cardHTML(stories) {
    if (!stories || !stories.length) return '';
    var container = document.createElement('div');

    var label = document.createElement('div');
    label.className = 'news-label';
    label.textContent = 'Today in AI';
    container.appendChild(label);

    for (var i = 0; i < Math.min(stories.length, 3); i++) {
      var s = stories[i];
      var p = document.createElement('p');
      p.className = 'news-headline';

      var a = document.createElement('a');
      a.href = s.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = '"' + s.title + '"';

      p.appendChild(a);
      container.appendChild(p);
    }

    var source = document.createElement('p');
    source.className = 'news-source';
    source.textContent = 'via Hacker News';
    container.appendChild(source);

    var caption = document.createElement('p');
    caption.className = 'news-caption';
    caption.textContent = "The field doesn't pause for a syllabus — here's today's version of it, next to where you are in the course.";
    container.appendChild(caption);

    return container;
  }

  function render(stories) {
    if (!stories || !stories.length) return;
    var card = document.getElementById("today-in-ai-card");
    if (!card) return;
    var content = cardHTML(stories);
    card.innerHTML = content.innerHTML;
    card.hidden = false;
  }

  function init() {
    if (!document.getElementById("today-in-ai-card")) {
      return; // page has no widget-rail container at all
    }

    var cached = loadCache();
    if (cached) {
      render(cached.stories);
      return;
    }

    fetchTopStories()
      .then(function (stories) {
        if (stories.length) {
          saveCache(stories);
          render(stories);
        }
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
