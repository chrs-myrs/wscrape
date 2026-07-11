import subprocess
import json
import re
import importlib.util
from importlib.machinery import SourceFileLoader
import pytest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "tools" / "wscrape")


def _load_cli():
    """Import wscrape (extensionless PEP 723 script) as a module for unit tests.

    crawl4ai is imported lazily inside functions, so this stays cheap.
    """
    spec = importlib.util.spec_from_loader("wscrape_cli", SourceFileLoader("wscrape_cli", SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault("timeout", 60)
    return subprocess.run(
        ["uv", "run", SCRIPT] + args,
        capture_output=True,
        text=True,
        **kwargs,
    )


def test_no_args_shows_help():
    result = run([], check=False)
    assert result.returncode != 0
    assert "usage" in result.stderr.lower() or "usage" in result.stdout.lower()


def test_unknown_command_fails():
    result = run(["bogus"], check=False)
    assert result.returncode != 0


def test_repair_title_respaces_query_terms_only():
    """ddgs strips spaces around highlighted query terms; we re-insert them."""
    w = _load_cli()
    q = "Tower Hamlets festivals"
    assert w._repair_title("TowerHamletsTown Hall | TikTok", q) == "Tower Hamlets Town Hall | TikTok"
    assert w._repair_title("attendTowerHamletsfestivalswith", q) == "attend Tower Hamlets festivals with"
    # Brand casing that isn't a query term must be left untouched.
    assert w._repair_title("TikTok GitHub iPhone", q) == "TikTok GitHub iPhone"


def test_search_returns_json_results():
    result = run(["search", "python web scraping", "--limit", "3"])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "url" in data[0]
    assert "title" in data[0]
    # Backend fallback should yield usable snippet bodies for triage.
    assert any(r.get("snippet") for r in data)


def test_search_writes_to_file(tmp_path):
    out = tmp_path / "results.json"
    result = run(["search", "python", "--limit", "2", "-o", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()
    data = json.loads(out.read_text())
    assert len(data) > 0


def test_scrape_static_page_returns_markdown():
    result = run(["scrape", "https://example.com"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.strip()) > 100
    assert "example" in result.stdout.lower()


def test_scrape_writes_to_file(tmp_path):
    out = tmp_path / "page.md"
    result = run(["scrape", "https://example.com", "-o", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert len(out.read_text()) > 100


def test_build_markdown_generator_selects_filter():
    """Raw -> no generator; query -> BM25; otherwise -> pruning."""
    w = _load_cli()
    assert w._build_markdown_generator(want_raw=True, query=None) is None
    # Filter selection needs crawl4ai importable in this interpreter.
    pytest.importorskip("crawl4ai")
    bm25 = w._build_markdown_generator(want_raw=False, query="some question")
    assert type(bm25.content_filter).__name__ == "BM25ContentFilter"
    pruning = w._build_markdown_generator(want_raw=False, query=None)
    assert type(pruning.content_filter).__name__ == "PruningContentFilter"


def test_choose_markdown_query_mode_keeps_short_fit():
    """With ratio_check off (query mode), a short non-empty fit is kept."""
    w = _load_cli()
    raw = "x" * 100
    short_fit = "x" * 10  # 10% of raw — would fall back under ratio_check
    assert w._choose_markdown(short_fit, raw, False, ratio_check=False) == (short_fit, False)
    # empty fit still falls back even in query mode
    assert w._choose_markdown("", raw, False, ratio_check=False) == (raw, True)


def test_choose_markdown_fallback_logic():
    """Safety-net: fit is used when healthy, raw when fit is empty or too sparse."""
    w = _load_cli()
    raw = "x" * 100

    # --raw always returns raw, never flags a fallback
    assert w._choose_markdown("anything", raw, True) == (raw, False)

    # empty / whitespace fit -> fall back to raw
    assert w._choose_markdown("   ", raw, False) == (raw, True)

    # fit below the 30% ratio -> fall back to raw
    assert w._choose_markdown("x" * 20, raw, False) == (raw, True)

    # healthy fit (>= 30% of raw) -> keep fit, no fallback
    fit = "x" * 50
    assert w._choose_markdown(fit, raw, False) == (fit, False)


def test_scrape_raw_flag_returns_fuller_content():
    """--raw keeps links/headings that the precise default strips."""
    default = run(["scrape", "https://example.com"])
    raw = run(["scrape", "https://example.com", "--raw"])
    assert default.returncode == 0 and raw.returncode == 0, raw.stderr
    # raw retains the outbound link (iana.org) that precise extraction drops
    assert "iana.org" in raw.stdout
    assert len(raw.stdout) >= len(default.stdout)


def test_scrape_js_path_returns_content():
    """Live: the crawl4ai/JS path exercises the fit_markdown + fallback wiring."""
    result = run(["scrape", "https://example.com", "--js"])
    assert result.returncode == 0, result.stderr
    assert "example" in result.stdout.lower()


def test_scrape_docs_archetype():
    """Live archetype: a docs page extracts sane, non-empty content."""
    result = run(["scrape", "https://docs.python.org/3/library/asyncio.html"])
    assert result.returncode == 0, result.stderr
    assert "asyncio" in result.stdout.lower()
    assert len(result.stdout.strip()) > 200


def test_map_returns_urls():
    result = run(["map", "https://example.com"])
    assert result.returncode == 0, result.stderr
    # example.com has few links, zero is acceptable
    lines = [l for l in result.stdout.strip().splitlines() if l.startswith("http")]
    assert isinstance(lines, list)


def test_map_search_filter():
    result = run(["map", "https://docs.python.org/3/", "--search", "library", "--limit", "20"])
    assert result.returncode == 0, result.stderr
    urls = [u for u in result.stdout.strip().splitlines() if u.startswith("http")]
    # If any URLs returned, they should all match the filter
    for url in urls:
        assert "library" in url.lower()


def test_crawl_returns_json_array():
    result = run(["crawl", "https://example.com", "--limit", "2", "--depth", "1"])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "url" in data[0]
    assert "markdown" in data[0]


def test_crawl_keywords_relevance():
    """Live: --keywords activates relevance-scored deep crawl."""
    result = run(["crawl", "https://docs.python.org/3/", "--keywords", "asyncio,await",
                  "--limit", "3", "--depth", "1"])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert isinstance(data, list) and len(data) >= 1
    assert "url" in data[0] and "markdown" in data[0]


def test_scrape_query_bm25():
    """Live: --query returns query-relevant passages via the crawl4ai/BM25 path."""
    result = run(["scrape", "https://docs.python.org/3/library/asyncio-task.html",
                  "--query", "how to create a task"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.strip()) > 0
    assert "task" in result.stdout.lower()


def test_map_seed_sitemap():
    """Live: --seed sitemap discovers URLs via the site's sitemap."""
    result = run(["map", "https://fastapi.tiangolo.com", "--seed", "sitemap", "--limit", "5"])
    assert result.returncode == 0, result.stderr
    urls = [u for u in result.stdout.strip().splitlines() if u.startswith("http")]
    assert len(urls) >= 1


def test_gather_returns_digest_and_json():
    """Live: gather adaptively crawls and returns a digest; --json is structured."""
    digest = run(["gather", "https://docs.python.org/3/", "--query", "async context managers",
                  "--limit", "4"], timeout=200)
    assert digest.returncode == 0, digest.stderr
    assert "# Gather:" in digest.stdout

    as_json = run(["gather", "https://docs.python.org/3/", "--query", "async context managers",
                   "--limit", "4", "--json"], timeout=200)
    assert as_json.returncode == 0, as_json.stderr
    data = json.loads(as_json.stdout)
    assert isinstance(data, list)


def test_norm_doi_strips_prefix_and_lowercases():
    w = _load_cli()
    assert w._norm_doi("https://doi.org/10.1/ABC") == "10.1/abc"
    assert w._norm_doi("http://dx.doi.org/10.1/ABC") == "10.1/abc"
    assert w._norm_doi("10.1/ABC") == "10.1/abc"
    assert w._norm_doi(None) is None
    assert w._norm_doi("") is None


def test_scholar_key_precedence():
    """Dedup key falls through DOI → arXiv id → PMID → normalised title."""
    w = _load_cli()
    assert w._scholar_key({"doi": "https://doi.org/10.1/X"}) == "10.1/x"
    assert w._scholar_key({"doi": None, "arxiv_id": "2306.1"}) == "arxiv:2306.1"
    assert w._scholar_key({"arxiv_id": None, "pmid": "999"}) == "pmid:999"
    assert w._scholar_key({"title": "Deep Learning!"}) == "title:deep learning"


def test_merge_records_unions_sources_and_keeps_richest():
    w = _load_cli()
    a = {"title": "T", "sources": ["crossref"], "citations": 2, "authors": ["A"],
         "abstract": "short", "venue": "", "open_access": None}
    b = {"title": "T", "sources": ["arxiv"], "citations": 10, "authors": ["A", "B"],
         "abstract": "a much longer abstract", "venue": "arXiv", "open_access": True}
    m = w._merge_records(a, b)
    assert m["sources"] == ["arxiv", "crossref"]      # union, sorted
    assert m["citations"] == 10                        # max
    assert m["authors"] == ["A", "B"]                  # longer author list
    assert m["abstract"] == "a much longer abstract"   # longer abstract
    assert m["venue"] == "arXiv"                        # fill empty field
    assert m["open_access"] is True


def test_rrf_merge_rewards_cross_engine_agreement():
    """A work found by two engines outranks works found by one (RRF)."""
    w = _load_cli()
    list1 = [{"doi": "10/y"}, {"doi": "10/x"}]   # y@1, x@2
    list2 = [{"doi": "10/x"}, {"doi": "10/z"}]   # x@1, z@2
    merged = w._rrf_merge([list1, list2])
    assert [r["doi"] for r in merged] == ["10/x", "10/y", "10/z"]
    assert len(merged) == 3


def test_scholar_federates_keyless():
    """Live: scholar federates the keyless core and reports coverage on stderr."""
    result = run(["scholar", "transformer neural networks", "--limit", "5"], timeout=90)
    assert result.returncode == 0, result.stderr
    assert "# Scholar:" in result.stdout
    # Coverage line names the engines queried; keyless core must appear.
    assert "wscrape scholar:" in result.stderr
    assert "crossref" in result.stderr and "arxiv" in result.stderr


def test_scholar_json_shape():
    """Live: --json emits records with the common Result schema."""
    result = run(["scholar", "CRISPR gene editing", "--limit", "3", "--json"], timeout=90)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert isinstance(data, list) and len(data) >= 1
    for key in ("title", "doi", "url", "citations", "sources"):
        assert key in data[0]
    assert isinstance(data[0]["sources"], list)


def test_canonical_url_normalises():
    w = _load_cli()
    assert (w._canonical_url("http://www.Example.com/path/?utm_source=x&id=5#frag")
            == "https://example.com/path?id=5")
    assert w._canonical_url("https://example.com/") == "https://example.com/"
    assert w._canonical_url("https://example.com/a/") == "https://example.com/a"


def test_is_tracking_param():
    w = _load_cli()
    assert w._is_tracking("utm_source") and w._is_tracking("fbclid") and w._is_tracking("gclid")
    assert not w._is_tracking("id") and not w._is_tracking("q")


def test_domain_of_strips_www():
    w = _load_cli()
    assert w._domain_of("https://www.bbc.co.uk/news") == "bbc.co.uk"
    assert w._domain_of("https://forbes.com/x") == "forbes.com"


def test_news_key_canonical_then_title():
    w = _load_cli()
    assert w._news_key({"url": "http://www.x.com/a/?utm_source=y"}) == "https://x.com/a"
    assert w._news_key({"url": "", "title": "Big News!"}) == "title:big news"


def test_rrf_merge_accepts_custom_key_fn():
    """News dedups by canonical URL: the same article from two engines fuses."""
    w = _load_cli()
    l1 = [{"url": "https://a.com/1"}, {"url": "https://b.com/2"}]
    l2 = [{"url": "http://www.a.com/1/"}, {"url": "https://c.com/3"}]  # a.com/1 dup
    merged = w._rrf_merge([l1, l2], key_fn=w._news_key)
    assert w._news_key(merged[0]) == "https://a.com/1"  # found in both → top
    assert len(merged) == 3


def test_match_domain_prefers_source_and_specificity():
    w = _load_cli()
    urls = [
        "https://google.com/x",
        "https://www.timeout.com/london",                     # section homepage
        "https://www.timeout.com/london/things-to-do/article",  # specific article
        "https://other.com/y",
    ]
    # Same-domain matches: prefer the deepest path (the real article).
    assert w._match_domain(urls, "timeout.com") == "https://www.timeout.com/london/things-to-do/article"
    # No domain hint: first non-Google result.
    assert w._match_domain(urls, "") == "https://www.timeout.com/london"
    # Only Google stubs → unresolved.
    assert w._match_domain(["https://news.google.com/rss/articles/CBMi"], "x.com") is None


def test_news_gdelt_federates():
    """Live: news queries GDELT and reports coverage (tolerant of GDELT 429s)."""
    result = run(["news", "climate policy", "--limit", "3"], timeout=90)
    assert result.returncode == 0, result.stderr
    assert "# News:" in result.stdout
    # Coverage line names the engine whether it returned data or was rate-limited.
    assert "gdelt" in result.stderr


def test_reddit_url_parsing():
    """Test URL parsing logic in-process."""
    import re

    _REDDIT_URL = re.compile(
        r"https?://(?:www\.|old\.)?reddit\.com"
        r"(?:/r/(?P<sub>[^/]+)(?:/comments/(?P<post_id>[^/]+))?)?",
    )

    def _parse(url):
        m = _REDDIT_URL.match(url)
        if not m:
            return None
        return {"subreddit": m.group("sub"), "post_id": m.group("post_id")}

    assert _parse("https://www.reddit.com/r/linux/comments/abc123/post_title/") == {
        "subreddit": "linux", "post_id": "abc123"
    }
    assert _parse("https://reddit.com/r/python/") == {
        "subreddit": "python", "post_id": None
    }
    assert _parse("https://old.reddit.com/r/neovim/comments/xyz789/title/") == {
        "subreddit": "neovim", "post_id": "xyz789"
    }
    assert _parse("https://example.com/page") is None


def test_reddit_subreddit_listing():
    result = run(["reddit", "https://www.reddit.com/r/python/", "--limit", "3"])
    if result.returncode == 0:
        assert "r/python" in result.stdout
    else:
        # Documented: Reddit blocks .json from data-centre IPs. Expect the
        # helpful hint pointing to --search, not a raw HTTP error.
        assert "403" in result.stderr and "--search" in result.stderr


def test_reddit_search():
    result = run(["reddit", "python web scraping", "--search", "--limit", "3"])
    assert result.returncode == 0, result.stderr
    assert "Reddit Search Results" in result.stdout
    assert "reddit.com" in result.stdout


def test_vtt_parsing():
    """Test VTT parsing logic in-process."""
    _VTT_SAMPLE = (
        "WEBVTT\n"
        "Kind: captions\n"
        "Language: en\n"
        "\n"
        "00:00:00.000 --> 00:00:02.500\n"
        "Hello, welcome to the video.\n"
        "\n"
        "00:00:02.500 --> 00:00:05.000\n"
        "Hello, welcome to the video.\n"
        "\n"
        "00:00:05.000 --> 00:00:08.000\n"
        "<font color=\"#CCCCCC\">Today we discuss Python.</font>\n"
        "\n"
        "00:00:08.000 --> 00:00:10.000\n"
        "Today we discuss Python.\n"
    )

    lines = _VTT_SAMPLE.splitlines()
    text_lines: list[str] = []
    prev = ""
    for line in lines:
        line = line.strip()
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d+$", line):
            continue
        if re.match(r"\d{2}:\d{2}:\d{2}", line):
            continue
        if not line:
            continue
        clean = re.sub(r"<[^>]+>", "", line)
        if not clean:
            continue
        if clean != prev:
            text_lines.append(clean)
            prev = clean

    assert text_lines == [
        "Hello, welcome to the video.",
        "Today we discuss Python.",
    ]


def test_transcript_extracts_subtitles():
    """Live test: extract transcript from a known YouTube video with subtitles."""
    result = run(["transcript", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.strip()) > 0


def test_transcript_video_id_shorthand():
    """Live test: bare 11-char video ID works."""
    result = run(["transcript", "dQw4w9WgXcQ"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.strip()) > 0


def test_transcript_writes_to_file(tmp_path):
    out = tmp_path / "transcript.md"
    result = run(["transcript", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "-o", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert len(out.read_text()) > 0


def test_transcript_no_subs_fails():
    """A nonexistent video should fail gracefully."""
    result = run(["transcript", "https://www.youtube.com/watch?v=XXXXXXXXXXX"], check=False)
    assert result.returncode != 0


# ── longtail ────────────────────────────────────────────────────────────────

def test_parse_instances_defaults_and_normalises():
    w = _load_cli()
    assert w._parse_instances(None) == w._DISCOURSE_DEFAULT_INSTANCES
    assert w._parse_instances("https://a.com/, b.com , ") == ["a.com", "b.com"]


def test_longtail_merge_key_fuses_cross_engine():
    """Same URL from Marginalia + HN fuses via the canonical-URL RRF key."""
    w = _load_cli()
    marg = [{"url": "https://x.com/a", "sources": ["marginalia"]},
            {"url": "https://y.com/b", "sources": ["marginalia"]}]
    hn = [{"url": "http://www.x.com/a/", "sources": ["hn"]},   # canonical dup of x.com/a
          {"url": "https://z.com/c", "sources": ["hn"]}]
    merged = w._rrf_merge([marg, hn], key_fn=w._news_key)
    assert w._news_key(merged[0]) == "https://x.com/a"   # found by both → top
    assert set(merged[0]["sources"]) == {"marginalia", "hn"}
    assert len(merged) == 3


def test_hn_record_handles_story_and_comment():
    """Story hits carry title+url; comment hits fall back to objectID item link."""
    w = _load_cli()
    story = w._hn_record({"title": "T", "url": "https://ex.com/p", "author": "a",
                          "objectID": "1", "created_at": "2020-01-01T00:00:00Z"})
    assert story["url"] == "https://ex.com/p" and story["title"] == "T"
    comment = w._hn_record({"comment_text": "<p>hi &amp; bye</p>", "author": "b",
                            "objectID": "42"})
    assert comment["url"] == "https://news.ycombinator.com/item?id=42"
    assert comment["snippet"] == "hi & bye"      # tags stripped, entities unescaped
    assert comment["sources"] == ["hn"]


def test_strip_html_unescapes_entities():
    w = _load_cli()
    assert w._strip_html("<b>a</b> &#x27;b&#x27; &amp; c") == "a 'b' & c"


def test_longtail_hn_live():
    """Live: longtail against HN (the reliable engine) returns merged JSON."""
    result = run(["longtail", "python packaging", "--engines", "hn", "--limit", "3", "--json"],
                 timeout=60)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert isinstance(data, list) and len(data) >= 1
    assert "url" in data[0] and "sources" in data[0]
    assert "wscrape longtail:" in result.stderr


def test_longtail_marginalia_live_tolerant():
    """Live: Marginalia has an undocumented QPM throttle; the command must still
    exit 0 and report coverage even when Marginalia is rate-limited."""
    result = run(["longtail", "small web", "--engines", "marginalia", "--limit", "3"],
                 timeout=60)
    assert result.returncode == 0, result.stderr
    assert "marginalia" in result.stderr   # ok(N) or failed/throttled — either is fine


# ── cdx ─────────────────────────────────────────────────────────────────────

def test_cdx_params_builds_pywb_dialect():
    w = _load_cli()
    p = w._cdx_params("example.com", match="domain", from_date="2008", to_date="2009",
                      filters=["statuscode:200", "mimetype:text/html"],
                      collapse="urlkey", limit=5)
    assert p["url"] == "example.com"
    assert p["output"] == "json"
    assert p["matchType"] == "domain"
    assert p["from"] == "2008" and p["to"] == "2009"
    assert p["collapse"] == "urlkey" and p["limit"] == 5
    assert p["filter"] == ["statuscode:200", "mimetype:text/html"]
    # Minimal call omits absent params entirely.
    bare = w._cdx_params("example.com")
    assert set(bare) == {"url", "output", "matchType"}


def test_cdx_live_tolerant():
    """Live: CDX enumerates captures; archive.org throttling (429/refused) is
    tolerated the way the reddit 403 test tolerates data-centre blocks."""
    result = run(["cdx", "example.com", "--limit", "3"], timeout=60, check=False)
    if result.returncode == 0:
        assert "| timestamp |" in result.stdout or "No captures" in result.stdout
    else:
        assert ("429" in result.stderr or "throttl" in result.stderr.lower()
                or "could not reach" in result.stderr.lower())


# ── probe ───────────────────────────────────────────────────────────────────

def test_ledger_record_shape_and_append(tmp_path):
    """Ledger record carries the contractual fields; append writes one JSON line."""
    w = _load_cli()
    rec = w._ledger_record(
        hunt_id="h1", surface="hn", query="q", params={"limit": 10},
        records=[{"url": "https://a.com/1"}, {"doi": "10.1/X"}],
        outcome="ok", canary_status="pass",
    )
    for field in ("ts", "hunt_id", "surface", "query_verbatim", "params", "hit_count",
                  "top_result_ids", "outcome", "canary_status", "wscrape_version"):
        assert field in rec
    assert rec["hit_count"] == 2
    assert rec["top_result_ids"] == ["https://a.com/1", "doi:10.1/x"]
    assert rec["wscrape_version"] == w.__version__

    path = tmp_path / "hunt" / "probes.jsonl"
    w._append_ledger(str(path), rec)
    w._append_ledger(str(path), rec)
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2                      # append-only, dirs created
    assert json.loads(lines[0])["surface"] == "hn"


def test_probe_canary_stamping_and_unverified(tmp_path, monkeypatch):
    """A failed canary marks every subsequent record for that engine UNVERIFIED;
    a passing canary stamps pass. Canary itself is logged too."""
    import asyncio
    w = _load_cli()

    # Mock the engine caller: hn's canary ("python") blanks → fail;
    # marginalia's canary ("linux") hits → pass. Real queries always hit.
    async def fake_call(engine, client, query, limit, instances):
        if query == w._PROBE_CANARIES["hn"]:      # "python" → force a failed canary
            return []
        return [{"url": f"https://ex.com/{engine}/{query}"}]

    monkeypatch.setattr(w, "_probe_call", fake_call)
    monkeypatch.setitem(w._PROBE_PACING, "hn", 0.0)
    monkeypatch.setitem(w._PROBE_PACING, "marginalia", 0.0)

    ledger = tmp_path / "probes.jsonl"
    records, warnings = asyncio.run(w._do_probe(
        engines=["hn", "marginalia"], queries=["real query"], limit=5,
        instances=[], hunt_id="h", ledger_path=str(ledger),
    ))

    by = lambda surface: [r for r in records if r["surface"] == surface]
    # hn: canary "python" fails → both hn records UNVERIFIED (canary_status=fail)
    hn = by("hn")
    assert len(hn) == 2 and all(r["canary_status"] == "fail" for r in hn)
    hn_canary = [r for r in hn if r["query_verbatim"] == "python"][0]
    assert hn_canary["outcome"] == "empty" and hn_canary["hit_count"] == 0
    # marginalia: canary "linux" passes → records verified
    marg = by("marginalia")
    assert len(marg) == 2 and all(r["canary_status"] == "pass" for r in marg)
    # A warning names the failed hn canary; ledger got every probe (4 lines).
    assert any("hn canary" in wmsg and "UNVERIFIED" in wmsg for wmsg in warnings)
    assert len(ledger.read_text().strip().splitlines()) == 4


def test_probe_hn_live_writes_ledger(tmp_path):
    """Live: a real hn probe writes a well-formed ledger line (canary + query)."""
    ledger = tmp_path / "probes.jsonl"
    result = run(["probe", "--engines", "hn", "--ledger", str(ledger), "async python"],
                 timeout=60)
    assert result.returncode == 0, result.stderr
    summaries = json.loads(result.stdout)
    assert isinstance(summaries, list) and len(summaries) == 2   # canary + 1 query
    lines = ledger.read_text().strip().splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[-1])
    assert rec["surface"] == "hn" and rec["query_verbatim"] == "async python"
    assert rec["outcome"] in ("ok", "empty", "timeout", "blocked")


def test_probe_rejects_unknown_engine():
    result = run(["probe", "--engines", "bogus", "x"], check=False)
    assert result.returncode != 0
    assert "unknown engine" in result.stderr.lower()


def test_probe_registers_greylit_engines():
    """The grey-lit engines are wired into the probe registry (pacing + canary)."""
    w = _load_cli()
    for eng in ("dblp", "openaire", "ntrs"):
        assert eng in w._PROBE_PACING
        assert eng in w._PROBE_CANARIES


# ── PDF scrape ──────────────────────────────────────────────────────────────

def _make_pdf(pages: list[str]) -> bytes:
    """Build a minimal valid multi-page PDF whose pages carry the given text."""
    def stream_for(text):
        content = f"BT /F1 24 Tf 72 700 Td ({text}) Tj ET".encode()
        return b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content)

    n = len(pages)
    kids = " ".join(f"{3 + i} 0 R" for i in range(n))
    parts = {1: b"<< /Type /Catalog /Pages 2 0 R >>",
             2: b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids.encode(), n)}
    font_obj = 3 + 2 * n
    for i in range(n):
        page_obj, content_obj = 3 + i, 3 + n + i
        parts[page_obj] = (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                           b"/Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>"
                           % (content_obj, font_obj))
        parts[content_obj] = stream_for(pages[i])
    parts[font_obj] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    out = b"%PDF-1.4\n"
    offsets = {}
    for i in range(1, font_obj + 1):
        offsets[i] = len(out)
        out += b"%d 0 obj\n" % i + parts[i] + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (font_obj + 1)
    for i in range(1, font_obj + 1):
        out += b"%010d 00000 n \n" % offsets[i]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (font_obj + 1, xref_pos)
    return out


def test_looks_like_pdf_url():
    w = _load_cli()
    assert w._looks_like_pdf_url("https://arxiv.org/pdf/2504.12516.pdf")
    assert w._looks_like_pdf_url("https://x.com/doc.PDF?download=1")   # case + query ignored
    assert not w._looks_like_pdf_url("https://example.com/page.html")
    assert not w._looks_like_pdf_url("https://example.com/pdf-viewer")


def _serve_dir(directory):
    """Serve `directory` over HTTP on a free port; return (base_url, shutdown)."""
    import threading
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}", srv.shutdown


def test_scrape_pdf_extracts_text_and_query_filter(tmp_path):
    """End-to-end (real uv env, pypdf present): scrape detects a .pdf target,
    extracts text, and --query keeps only the matching page (section filter)."""
    (tmp_path / "doc.pdf").write_bytes(_make_pdf(["alpha meditation", "beta turbulence"]))
    base, shutdown = _serve_dir(tmp_path)
    try:
        full = run(["scrape", f"{base}/doc.pdf"])
        assert full.returncode == 0, full.stderr
        assert "alpha meditation" in full.stdout and "beta turbulence" in full.stdout

        filtered = run(["scrape", f"{base}/doc.pdf", "--query", "meditation"])
        assert filtered.returncode == 0, filtered.stderr
        assert "alpha meditation" in filtered.stdout
        assert "beta turbulence" not in filtered.stdout
    finally:
        shutdown()


# ── cdx: Common Crawl + response-dialect parsing ─────────────────────────────

def test_parse_cdx_response_both_dialects():
    """Wayback returns array-of-arrays; Common Crawl returns NDJSON objects."""
    w = _load_cli()
    wayback = ('[["urlkey","timestamp","original","mimetype","statuscode"],'
               '["com,example)/","20020120","http://example.com/","text/html","200"]]')
    rows = w._parse_cdx_response(wayback)
    assert len(rows) == 1
    assert rows[0]["original"] == "http://example.com/" and rows[0]["statuscode"] == "200"

    cc = ('{"urlkey":"com,example)/","timestamp":"20260605","url":"https://example.com/",'
          '"status":"200","filename":"crawl-data/…/x.warc.gz","offset":"1","length":"9"}\n'
          '{"urlkey":"com,example)/","timestamp":"20260606","url":"https://www.example.com/",'
          '"status":"200","filename":"y.warc.gz","offset":"2","length":"8"}\n')
    rows = w._parse_cdx_response(cc)
    assert len(rows) == 2
    assert rows[0]["url"] == "https://example.com/" and rows[0]["filename"].endswith("x.warc.gz")
    assert w._parse_cdx_response("") == []


def test_cc_base_builds_index_url():
    w = _load_cli()
    assert w._cc_base("CC-MAIN-2026-25") == "https://index.commoncrawl.org/CC-MAIN-2026-25-index"


def test_format_cdx_table_cc_shows_warc_pointers():
    w = _load_cli()
    rows = [{"timestamp": "20260605", "url": "https://example.com/", "status": "200",
             "mime": "text/html", "filename": "x.warc.gz", "offset": "1", "length": "9"}]
    out = w._format_cdx_table(rows, "example.com", cc=True)
    assert "filename" in out and "offset" in out and "length" in out
    assert "x.warc.gz" in out and "Common Crawl" in out


# ── scholar: grey-literature engine record mapping (canned JSON) ─────────────

class _FakeResp:
    def __init__(self, payload, status_code=200, headers=None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    async def get(self, url, params=None, headers=None):
        return _FakeResp(self._payload)


def _run_adapter(fn, payload):
    import asyncio
    return asyncio.run(fn(_FakeClient(payload), "q", 5))


def test_scholar_dblp_mapping():
    w = _load_cli()
    payload = {"result": {"hits": {"hit": [
        {"info": {"title": "An exact mapping.",
                  "authors": {"author": [{"text": "Ana Stanojevic"}, {"text": "Wulfram Gerstner"}]},
                  "venue": "Neural Networks", "year": "2024", "doi": "10.1/x",
                  "ee": "https://doi.org/10.1/x", "access": "open"}},
        {"info": {"title": "Single author work",
                  "authors": {"author": {"text": "Solo Person"}},  # single-author = dict, not list
                  "year": "2020", "venue": "V"}},
    ]}}}
    recs = _run_adapter(w._scholar_dblp, payload)
    assert len(recs) == 2
    assert recs[0]["title"] == "An exact mapping"          # trailing period stripped
    assert recs[0]["authors"] == ["Ana Stanojevic", "Wulfram Gerstner"]
    assert recs[0]["doi"] == "10.1/x" and recs[0]["open_access"] is True
    assert recs[0]["abstract"] == "" and recs[0]["sources"] == ["dblp"]
    assert recs[1]["authors"] == ["Solo Person"]           # dict coerced to single-item list


def test_scholar_openaire_mapping():
    w = _load_cli()
    payload = {"results": [
        {"mainTitle": "The Dark Night", "authors": [{"fullName": "A B"}],
         "publicationDate": "2022-10-22", "descriptions": ["<jats:p>Abstract text</jats:p>"],
         "pids": [{"scheme": "doi", "value": "10.1/oa"}], "openAccessColor": "gold",
         "container": {"name": "J Contemp"}},
    ]}
    recs = _run_adapter(w._scholar_openaire, payload)
    assert recs[0]["title"] == "The Dark Night" and recs[0]["year"] == 2022
    assert recs[0]["doi"] == "10.1/oa" and recs[0]["url"] == "https://doi.org/10.1/oa"
    assert recs[0]["abstract"] == "Abstract text"          # jats markup stripped
    assert recs[0]["venue"] == "J Contemp" and recs[0]["open_access"] is True
    assert recs[0]["sources"] == ["openaire"]


def test_scholar_ntrs_mapping():
    w = _load_cli()
    payload = {"results": [
        {"id": 20250011362, "title": "Wind and Turbulence",
         "authorAffiliations": [{"meta": {"author": {"name": "Evan Kawamura"}}}],
         "distributionDate": "2026-01-12T08:00:00", "stiTypeDetails": "Conference Paper",
         "otherReportNumbers": [{"number": "NASA/TM-2026-1"}],
         "abstract": "Turbulence poses challenges."},
    ]}
    recs = _run_adapter(w._scholar_ntrs, payload)
    assert recs[0]["title"] == "Wind and Turbulence" and recs[0]["year"] == 2026
    assert recs[0]["url"] == "https://ntrs.nasa.gov/citations/20250011362"
    assert recs[0]["authors"] == ["Evan Kawamura"]
    assert "Conference Paper" in recs[0]["venue"] and "NASA/TM-2026-1" in recs[0]["venue"]
    assert recs[0]["open_access"] is True and recs[0]["sources"] == ["ntrs"]


def test_scholar_osf_mapping():
    w = _load_cli()
    payload = {"data": [
        {"attributes": {"title": "Meditation and mind", "date_published": "2026-07-03T10:13",
                        "doi": None, "description": "Desc here"},
         "links": {"html": "https://osf.io/xyz"}},
    ]}
    recs = _run_adapter(w._scholar_osf, payload)
    assert recs[0]["title"] == "Meditation and mind" and recs[0]["year"] == 2026
    assert recs[0]["url"] == "https://osf.io/xyz" and recs[0]["venue"] == "OSF Preprints"
    assert recs[0]["authors"] == [] and recs[0]["abstract"] == "Desc here"
    assert recs[0]["open_access"] is True and recs[0]["sources"] == ["osf"]


# ── live-tolerant: widened federation + Common Crawl + snapshot fetch ────────

def test_scholar_widened_federation_live():
    """Live: scholar now federates 7 keyless engines; coverage names all of them."""
    result = run(["scholar", "dark night meditation phenomenology", "--limit", "8"], timeout=120)
    assert result.returncode == 0, result.stderr
    assert "wscrape scholar:" in result.stderr
    for eng in ("crossref", "arxiv", "europepmc", "openaire", "ntrs", "dblp", "osf"):
        assert eng in result.stderr, f"{eng} missing from coverage line"


def test_cdx_cc_collinfo_live_tolerant():
    """Live: --cc resolves the newest crawl via collinfo.json and queries it.
    CC index throttling is tolerated the way the Wayback test tolerates 429s."""
    result = run(["cdx", "example.com", "--cc", "--limit", "3"], timeout=90, check=False)
    if result.returncode == 0:
        # CC output exposes WARC pointers, not a Wayback snapshot column.
        assert "Common Crawl" in result.stdout or "No captures" in result.stdout
        if "filename" in result.stdout:
            assert "offset" in result.stdout and "length" in result.stdout
    else:
        assert ("429" in result.stderr or "throttl" in result.stderr.lower()
                or "could not reach" in result.stderr.lower())


def test_cdx_fetch_rejected_with_cc():
    """--fetch is Wayback-only; combining it with --cc errors politely, no fetch."""
    result = run(["cdx", "example.com", "--cc", "--fetch", "1"], check=False)
    assert result.returncode != 0
    assert "wayback-only" in result.stderr.lower()


def test_cdx_fetch_single_snapshot_live_tolerant():
    """Live: --fetch retrieves+extracts a snapshot; archive.org throttling tolerated."""
    result = run(["cdx", "dharmaoverground.org", "--match", "domain", "--from", "2008",
                  "--to", "2009", "--limit", "3", "--fetch", "1"], timeout=120, check=False)
    if result.returncode == 0:
        # Enumeration table always present; snapshot section present when rows existed.
        assert "# CDX" in result.stdout
        if "# CDX snapshots:" in result.stdout:
            assert "##" in result.stdout  # a per-snapshot section (content or fetch-failed note)
    else:
        assert ("429" in result.stderr or "throttl" in result.stderr.lower()
                or "could not reach" in result.stderr.lower())
