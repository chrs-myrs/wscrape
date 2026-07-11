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


def test_search_returns_json_results():
    result = run(["search", "python web scraping", "--limit", "3"])
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "url" in data[0]
    assert "title" in data[0]


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
