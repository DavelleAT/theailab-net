// "Today in AI" — live headlines from Hacker News, shown as a supplementary
// widget (never course content, never authoritative). See
// docs/design-spec_phase3_website-revision_v1_20260903.md Part 3.
//
// The card shows what the field is actually talking about: frontier model
// releases, research, and the arguments around them. An earlier version
// searched per-week course topics ("MCP servers", "Codex CLI"), which sounded
// better than it read. Those terms live on Hacker News mostly in "Show HN"
// posts, so the card filled up with links to individual side-project repos
// rather than news. The filters below exist to keep that from coming back:
//
//   - Show HN, Launch HN, Ask HN and Tell HN titles are dropped outright
//   - so are links straight to a code host, which are projects, not stories
//   - a points floor keeps what is left to stories the site actually engaged
//     with, rather than anything posted that happened to match a keyword
//
// Data source is the public, keyless HN Algolia Search API. Results are cached
// in localStorage per six-hour window, so the card turns over about four times
// a day without re-fetching on every page view. If the fetch fails, or nothing
// clears the filters, the card does not render at all. It is supplementary, so
// failing invisibly is correct.

(function () {
  var CACHE_PREFIX = "today-in-ai:v3:";
  // How often the card turns over. Also the cache lifetime, since a new window
  // means a new key and the old entry is never read again.
  var ROTATION_MS = 6 * 60 * 60 * 1000;
  var SHOW_COUNT = 3;

  // Tried in order, first one that fills the card wins. Recent and well-read
  // is the goal; the later entries trade freshness for having enough to show
  // during a quiet week.
  var STRATEGIES = [
    { days: 7, minPoints: 50 },
    { days: 14, minPoints: 50 },
    { days: 30, minPoints: 20 }
  ];

  var KEYWORDS = [
    "ai", "llm", "gpt", "openai", "anthropic", "claude", "gemini", "deepseek",
    "machine learning", "neural", "transformer", "agent", "model", "chatbot"
  ];

  var KEYWORD_PATTERNS = KEYWORDS.map(function (kw) {
    // Word-boundary match — a plain substring check would let short keywords
    // like "ai" match inside unrelated words ("Ukrainian", "maintain",
    // "portrait"), which happened during testing.
    return new RegExp("\\b" + kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b", "i");
  });

  var SELF_POST = /^\s*(show|launch|ask|tell)\s+hn\b/i;
  var CODE_HOST = /^https?:\/\/(www\.)?(github\.com|gitlab\.com|bitbucket\.org|codeberg\.org)/i;

  function isNews(hit, minPoints) {
    if (!hit.title || !hit.url) return false;
    if ((hit.points || 0) < minPoints) return false;
    if (SELF_POST.test(hit.title)) return false;
    if (CODE_HOST.test(hit.url)) return false;
    return KEYWORD_PATTERNS.some(function (re) { return re.test(hit.title); });
  }

  function fetchStories(strategy) {
    var since = Math.floor((Date.now() - strategy.days * 86400000) / 1000);
    var url = "https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=100" +
      "&numericFilters=created_at_i%3E" + since;
    return fetch(url)
      .then(function (res) {
        if (!res.ok) throw new Error("HN API error " + res.status);
        return res.json();
      })
      .then(function (data) {
        var hits = (data.hits || []).filter(function (h) {
          return isNews(h, strategy.minPoints);
        });
        // Most-discussed first. The relevance ordering the API returns by
        // default is for text queries; there is no query here.
        hits.sort(function (a, b) { return (b.points || 0) - (a.points || 0); });
        return hits.slice(0, SHOW_COUNT).map(function (h) {
          return { title: h.title, url: h.url, points: h.points || 0 };
        });
      });
  }

  // Walk the strategies until one returns a full card.
  function fetchBest(index) {
    index = index || 0;
    if (index >= STRATEGIES.length) return Promise.resolve([]);
    return fetchStories(STRATEGIES[index]).then(function (stories) {
      if (stories.length >= SHOW_COUNT) return stories;
      return fetchBest(index + 1).then(function (next) {
        return next.length > stories.length ? next : stories;
      });
    });
  }

  /* ---- cache ---- */

  function cacheKey() {
    return CACHE_PREFIX + Math.floor(Date.now() / ROTATION_MS);
  }

  function loadCache() {
    try {
      var raw = localStorage.getItem(cacheKey());
      if (!raw) return null;
      var stories = JSON.parse(raw);
      return stories && stories.length ? stories : null;
    } catch (e) {
      return null;
    }
  }

  function saveCache(stories) {
    try {
      var current = cacheKey();
      localStorage.setItem(current, JSON.stringify(stories));
      // Rotating the key leaves the previous window's entry behind, so clear
      // anything from an older window on the way past.
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

  function cardContent(stories) {
    var container = document.createElement("div");

    var label = document.createElement("div");
    label.className = "news-label";
    label.textContent = "Today in AI";
    container.appendChild(label);

    for (var i = 0; i < stories.length; i++) {
      var p = document.createElement("p");
      p.className = "news-headline";
      var a = document.createElement("a");
      a.href = stories[i].url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "“" + stories[i].title + "”";
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

  function render(stories) {
    if (!stories || !stories.length) return;
    var card = document.getElementById("today-in-ai-card");
    if (!card) return;
    card.innerHTML = "";
    card.appendChild(cardContent(stories));
    card.hidden = false;
  }

  function init() {
    if (!document.getElementById("today-in-ai-card")) return;

    var cached = loadCache();
    if (cached) {
      render(cached);
      return;
    }

    fetchBest()
      .then(function (stories) {
        if (!stories.length) return;
        saveCache(stories);
        render(stories);
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
