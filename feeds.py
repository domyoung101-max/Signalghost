"""feeds.py — Signalghost sourcing framework (v2.3.1 — RSS-first parallel hybrid sourcing).

SOURCING FRAMEWORK — 18 NAMED FEEDS BY TIER (v1.2.1)

Priority order per feed:
1. RSS/direct source fetch where configured
2. Claude web_search fallback when RSS/direct yields no usable recent findings

Execution model:
- NON-SEQUENTIAL: feeds are processed concurrently with a bounded thread pool
- Result contract preserved for session_executor.py compatibility
"""

import os
import time
import email.utils
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    FEED_TIERS,
    TOTAL_NAMED_FEEDS,
    MODEL_FINAL_NARRATION,          # reused as primary Claude model
    NARRATION_DEFAULT_MAX_TOKENS,   # used as a conservative ceiling for feed fallback
)
from models import FeedSweepResult
from persistence import insert_row

USER_AGENT = "Signalghost/2.3 (+RSS-first parallel hybrid sourcing)"
RSS_TIMEOUT = 12
RECENCY_HOURS = 72
MAX_WORKERS = 6

FALLBACK_MAX_TOKENS = min(800, NARRATION_DEFAULT_MAX_TOKENS)
FALLBACK_MAX_CHARS = 3000
SUPPLEMENTARY_MAX_CHARS = 5000  # Extended limit for Tier 1-2 with adversarial queries


def get_all_feeds() -> List[Dict[str, object]]:
    feeds = []
    tier_num_map = {"TIER_1": 1, "TIER_2": 2, "TIER_3": 3, "TIER_4": 4}
    for tier_key, feed_list in FEED_TIERS.items():
        tier_num = tier_num_map[tier_key]
        for feed_name in feed_list:
            feeds.append({"feed_name": feed_name, "tier": tier_num})
    assert len(feeds) == TOTAL_NAMED_FEEDS
    return feeds


FEED_QUERIES: Dict[str, str] = {
    "Trump Truth Social / White House official statements": "Trump Iran statement today 2026",
    "CENTCOM public affairs": "CENTCOM Hormuz statement today 2026",
    "IDF official statements": "IDF Lebanon Hezbollah statement today 2026",
    "Iran SNSC / IRNA (named attribution)": "IRNA Iran talks statement today 2026",
    "Named government spokesperson statements": "Araghchi Iran foreign ministry statement today 2026",
    "Reuters": "Reuters Iran Hormuz latest 2026",
    "AP": "AP News Iran Middle East latest 2026",
    "Bloomberg": "Bloomberg Iran oil sanctions latest 2026",
    "Al Jazeera": "Al Jazeera Iran US talks latest 2026",
    "NBC News live updates": "NBC News Iran Middle East updates 2026",
    "CBS News live updates": "CBS News Iran talks latest 2026",
    "NPR": "NPR Iran nuclear Middle East 2026",
    "Tasnim News Agency (IRGC-linked)": "Tasnim News Iran IRGC latest 2026",
    "Mehr News Agency": "Mehr News Agency Iran latest 2026",
    "WANA News Agency": "WANA News Middle East latest 2026",
    "House of Saud / Conflict Pulse": "Saudi Arabia Iran Gulf conflict latest 2026",
    "Wikipedia": "2026 Iran United States crisis Wikipedia",
    "ACLED conflict monitor": "ACLED Middle East conflict data 2026",
}

FEED_RSS_SOURCES: Dict[str, List[str]] = {
    "Reuters": [
        "https://feeds.reuters.com/reuters/worldNews",
        "https://feeds.reuters.com/reuters/topNews",
    ],
    "Al Jazeera": [
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.aljazeera.com/xml/rss/all.xml?traffic_source=rss",
    ],
    "NPR": [
        "https://feeds.npr.org/1004/rss.xml",
        "https://feeds.npr.org/1001/rss.xml",
    ],
    "CBS News live updates": [
        "https://www.cbsnews.com/latest/rss/main",
    ],
    "NBC News live updates": [
        "https://feeds.nbcnews.com/nbcnews/public/news",
    ],
    "Tasnim News Agency (IRGC-linked)": [
        "https://www.tasnimnews.com/en/rss/feed/0/7/0/world",
        "https://www.tasnimnews.com/en/rss/feed/0/7/7/middle-east",
    ],
    "Mehr News Agency": [
        "https://en.mehrnews.com/rss",
    ],
    "WANA News Agency": [
        "https://wanaen.com/feed/",
    ],
    "Wikipedia": [
        "https://en.wikipedia.org/w/api.php?action=feedrecentchanges&feedformat=atom",
    ],
}

TOPIC_KEYWORDS = {
    "Trump Truth Social / White House official statements": ["trump", "white house", "iran", "hormuz", "middle east"],
    "CENTCOM public affairs": ["centcom", "iran", "hormuz", "gulf", "middle east"],
    "IDF official statements": ["idf", "lebanon", "hezbollah", "gaza", "israel"],
    "Iran SNSC / IRNA (named attribution)": ["iran", "irna", "tehran", "talks", "nuclear", "araghchi"],
    "Named government spokesperson statements": ["araghchi", "foreign ministry", "state department", "spokesperson", "iran"],
    "Reuters": ["iran", "hormuz", "middle east", "talks", "sanctions", "lebanon"],
    "AP": ["iran", "middle east", "talks", "nuclear", "lebanon", "israel"],
    "Bloomberg": ["iran", "oil", "sanctions", "hormuz", "middle east"],
    "Al Jazeera": ["iran", "us", "talks", "middle east", "lebanon", "israel"],
    "NBC News live updates": ["iran", "middle east", "talks", "israel", "lebanon"],
    "CBS News live updates": ["iran", "talks", "middle east", "israel", "lebanon"],
    "NPR": ["iran", "nuclear", "middle east", "talks", "israel"],
    "Tasnim News Agency (IRGC-linked)": ["iran", "irgc", "talks", "hormuz", "araghchi"],
    "Mehr News Agency": ["iran", "talks", "nuclear", "araghchi", "middle east"],
    "WANA News Agency": ["iran", "middle east", "talks", "sanctions", "hormuz"],
    "House of Saud / Conflict Pulse": ["saudi", "gulf", "iran", "conflict", "hormuz"],
    "Wikipedia": ["iran", "united states", "crisis", "middle east"],
    "ACLED conflict monitor": ["middle east", "conflict", "iran", "israel", "lebanon"],
}


def _get_api_key() -> Optional[str]:
    return os.environ.get("ANTHROPIC_API_KEY")


def _generate_adversarial_queries() -> List[str]:
    """Generate prediction-aware queries from open predictions.

    Reads open predictions + disconfirmation thresholds from DB,
    produces targeted search queries that hunt for BOTH confirmation
    and contradiction signals — with contradiction weighted first.

    Returns a flat list of query strings ready for web search.
    """
    try:
        from persistence import get_open_predictions
        preds = get_open_predictions()
    except Exception:
        return []

    queries = []
    for p in preds:
        if "RESOLVED" in (p.get("status") or ""):
            continue
        flag = p.get("flag", "")
        res_no = p.get("resolution_no", "") or ""
        res_yes = p.get("resolution_yes", "") or ""
        pred_ref = p.get("pred_ref", "")

        # Contradiction queries FIRST (adversarial — hunting to break
        # the system's own position)
        if "memo" in flag.lower() or "framework" in flag.lower():
            queries.append("US rejects Iran deal proposal 2026")
            queries.append("Iran negotiations fail collapse 2026")
        if "uranium" in flag.lower() or "stockpile" in flag.lower():
            queries.append("IAEA Iran uranium stockpile remains 2026")
            queries.append("Iran rejects uranium transfer export 2026")
        if "irgc" in flag.lower() or "snsc" in flag.lower():
            queries.append("Salami contradicts Araghchi Iran 2026")
            queries.append("IRGC opposes Iran diplomacy talks 2026")

        # Confirmation queries (standard — tracking positive resolution)
        if "memo" in flag.lower():
            queries.append("Iran US framework memo signed deal 2026")
        if "uranium" in flag.lower():
            queries.append("IAEA Iran uranium transfer shipment 2026")
        if "irgc" in flag.lower() or "endorses" in flag.lower():
            queries.append("IRGC SNSC endorses Araghchi diplomacy 2026")

    # Deduplicate while preserving order (contradiction-first)
    seen = set()
    unique = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    try:
        dt = email.utils.parsedate_to_datetime(value)
        if dt is not None:
            return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    iso_value = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso_value)
        return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _fetch_url_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=RSS_TIMEOUT) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1].lower()
    return tag.lower()


def _extract_entries_from_xml(xml_text: str) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    root = ET.fromstring(xml_text)

    for parent_tag in ("item", "entry"):
        for node in root.iter():
            if _local_name(node.tag) != parent_tag:
                continue
            item: Dict[str, str] = {"title": "", "summary": "", "link": "", "published": ""}
            for child in list(node):
                name = _local_name(child.tag)
                text = (child.text or "").strip()
                if name == "title":
                    item["title"] = text
                elif name in ("description", "summary", "content", "encoded") and not item["summary"]:
                    item["summary"] = text
                elif name in ("pubdate", "published", "updated", "date") and not item["published"]:
                    item["published"] = text
                elif name == "link":
                    href = child.attrib.get("href", "").strip()
                    item["link"] = href or text
            entries.append(item)
    return entries


def _filter_recent_relevant_entries(feed_name: str, entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    cutoff = _utc_now() - timedelta(hours=RECENCY_HOURS)
    keywords = TOPIC_KEYWORDS.get(feed_name, [])
    scored: List[Tuple[int, Dict[str, str]]] = []

    for entry in entries:
        title = (entry.get("title") or "").strip()
        summary = (entry.get("summary") or "").strip()
        blob = f"{title} {summary}".lower()
        if not blob:
            continue
        published = _parse_date(entry.get("published", ""))
        if published and published < cutoff:
            continue
        score = sum(1 for kw in keywords if kw in blob)
        if score == 0 and keywords:
            continue
        entry_copy = dict(entry)
        entry_copy["published"] = published.isoformat() if published else (entry.get("published") or "")
        scored.append((score, entry_copy))

    scored.sort(key=lambda x: (-x[0], x[1].get("published", "")))
    return [item for _, item in scored[:3]]


def _format_rss_findings(entries: List[Dict[str, str]]) -> str:
    if not entries:
        return "NO NEW FINDINGS"
    lines = []
    for entry in entries[:3]:
        title = (entry.get("title") or "Untitled").replace("\n", " ").strip()
        link = (entry.get("link") or "").strip()
        published = (entry.get("published") or "").strip()
        if published:
            lines.append(f"- {title} [{published}] {link}".strip())
        else:
            lines.append(f"- {title} {link}".strip())
    joined = "\n".join(lines).strip()
    return joined[:FALLBACK_MAX_CHARS] if joined else "NO NEW FINDINGS"


def _try_rss_feed(feed_name: str, tier: int) -> Optional[Dict]:
    urls = FEED_RSS_SOURCES.get(feed_name, [])
    if not urls:
        return None

    for url in urls:
        try:
            xml_text = _fetch_url_text(url)
            entries = _extract_entries_from_xml(xml_text)
            filtered = _filter_recent_relevant_entries(feed_name, entries)
            if filtered:
                return {
                    "feed_name": feed_name,
                    "tier": tier,
                    "findings": _format_rss_findings(filtered),
                    "checked": True,
                }
        except Exception:
            continue
    return None


def _search_single_feed(feed_name: str, tier: int, query: str) -> Dict:
    key = _get_api_key()
    if not key:
        return {"feed_name": feed_name, "tier": tier, "findings": "API unavailable", "checked": False}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)

        prompt = (
            f"Source: {feed_name}\n"
            f"Search query: {query}\n\n"
            "Task: Use web_search_20250305 to retrieve the very latest verifiable news "
            "from this specific source over the last 48 hours.\n\n"
            "Output format (STRICT):\n"
            "- Up to 3 bullet points.\n"
            "- Each bullet is ONE sentence.\n"
            "- Each must contain: actor, action, date (if available), and source name.\n"
            "- NO analysis, NO commentary, NO probabilities.\n"
            "- If no recent relevant news found, output exactly: NO NEW FINDINGS\n"
        )

        for attempt in range(4):
            try:
                message = client.messages.create(
                    model=MODEL_FINAL_NARRATION,
                    max_tokens=FALLBACK_MAX_TOKENS,
                    tools=[{"type": "web_search_20250305", "name": "web_search"}],
                    system=(
                        "Search the web and return ONLY short factual bullet points. "
                        "No analysis, no commentary, no summaries. "
                        "Maximum three bullets. If nothing relevant, return exactly: NO NEW FINDINGS"
                    ),
                    messages=[{"role": "user", "content": prompt}],
                )

                full_text = ""
                for block in message.content:
                    if hasattr(block, "text"):
                        full_text += block.text

                findings_raw = full_text.strip()
                if not findings_raw:
                    findings = "NO NEW FINDINGS"
                else:
                    findings = findings_raw[:FALLBACK_MAX_CHARS]

                return {
                    "feed_name": feed_name,
                    "tier": tier,
                    "findings": findings,
                    "checked": True,
                }

            except anthropic.RateLimitError:
                if attempt >= 2:
                    break
                wait = 10 * (attempt + 1)
                print(f" {feed_name}: rate limited, waiting {wait}s...")
                time.sleep(wait)

        return {
            "feed_name": feed_name,
            "tier": tier,
            "findings": "Rate limit exceeded — feed skipped",
            "checked": False,
        }

    except Exception as e:
        return {
            "feed_name": feed_name,
            "tier": tier,
            "findings": f"Error: {str(e)[:150]}",
            "checked": True,
        }


def _search_supplementary(feed_name: str, tier: int, queries: List[str]) -> str:
    """Run a batched adversarial query sweep for a Tier 1-2 feed.

    Takes multiple prediction-aware queries and executes them in a
    single API call. Returns concatenated findings text.
    Contradiction queries appear first (by construction from
    _generate_adversarial_queries).

    Cost: ONE API call per Tier 1-2 feed (~11 extra calls per sweep).
    """
    key = _get_api_key()
    if not key or not queries:
        return ""

    # Cap at 4 queries per feed to control token usage
    capped = queries[:4]
    query_block = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(capped))

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)

        prompt = (
            f"Source context: {feed_name}\n\n"
            f"Run the following {len(capped)} searches and report findings:\n"
            f"{query_block}\n\n"
            "For EACH query, use web_search to find the latest evidence "
            "from the last 48 hours.\n\n"
            "Output format (STRICT):\n"
            "- Up to 2 bullet points PER query that returned results.\n"
            "- Each bullet: ONE factual sentence with actor, action, date, source.\n"
            "- Skip queries with no results — do NOT write 'no findings' for them.\n"
            "- NO analysis, NO commentary, NO probabilities.\n"
            "- If ALL queries return nothing, output exactly: NO NEW FINDINGS\n"
        )

        message = client.messages.create(
            model=MODEL_FINAL_NARRATION,
            max_tokens=FALLBACK_MAX_TOKENS,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            system=(
                "You are a senior intelligence analyst conducting an adversarial "
                "evidence sweep. Search for evidence that could CONFIRM or "
                "CONTRADICT active forecasting predictions. Report only verified "
                "facts. Maximum 8 bullets total. If nothing found, return: "
                "NO NEW FINDINGS"
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        full_text = ""
        for block in message.content:
            if hasattr(block, "text"):
                full_text += block.text

        result = full_text.strip()
        if not result or "NO NEW FINDINGS" in result:
            return ""
        return result

    except Exception:
        return ""


def _process_single_feed(
    index: int,
    total: int,
    feed: Dict[str, object],
    edition: int,
    timestamp: str,
    adversarial_queries: Optional[List[str]] = None,
) -> Tuple[int, FeedSweepResult]:
    fname = str(feed["feed_name"])
    tier = int(feed["tier"])
    query = FEED_QUERIES.get(fname, fname)

    raw = _try_rss_feed(fname, tier)
    if raw is None:
        raw = _search_single_feed(fname, tier, query)

    findings = raw.get("findings", "NO FINDINGS")

    # ── ADVERSARIAL SUPPLEMENTARY SWEEP (Tier 1-2 only) ──────────
    # ONE batched API call per feed with prediction-aware queries.
    # Contradiction queries appear first by construction.
    # Cost: ~11 extra API calls per sweep (one per Tier 1-2 feed).
    if tier <= 2 and adversarial_queries:
        supplement = _search_supplementary(fname, tier, adversarial_queries)
        if supplement:
            findings = (findings + "\n[ADVERSARIAL SWEEP]\n" + supplement)
            findings = findings[:SUPPLEMENTARY_MAX_CHARS]

    fsr = FeedSweepResult(
        feed_name=raw.get("feed_name", fname),
        tier=raw.get("tier", tier),
        checked=raw.get("checked", False),
        findings=findings,
        edition=edition,
        timestamp=timestamp,
    )

    return index, fsr


def execute_feed_sweep(edition: int, timestamp: str) -> Dict:
    all_feeds = get_all_feeds()
    results_by_index: Dict[int, FeedSweepResult] = {}
    unchecked: List[str] = []

    # ── ADVERSARIAL QUERY GENERATION ─────────────────────────────
    # Generate prediction-aware queries ONCE before sweep starts.
    # These hunt for confirmation AND contradiction signals aligned
    # with open prediction disconfirmation thresholds.
    adv_queries = _generate_adversarial_queries()
    if adv_queries:
        print(f" Adversarial queries generated: {len(adv_queries)} "
              f"(Tier 1-2 feeds will run supplementary searches)")
    else:
        print(" No adversarial queries generated (no open predictions or DB unavailable)")

    print(f" Launching parallel feed sweep with {MAX_WORKERS} workers...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(
                _process_single_feed, i, len(all_feeds), feed, edition, timestamp,
                adv_queries if int(feed["tier"]) <= 2 else None,
            ): (i, feed)
            for i, feed in enumerate(all_feeds)
        }

        for future in as_completed(future_map):
            i, feed = future_map[future]
            fname = str(feed["feed_name"])
            tier = int(feed["tier"])
            try:
                index, fsr = future.result()
            except Exception as e:
                fsr = FeedSweepResult(
                    feed_name=fname,
                    tier=tier,
                    checked=False,
                    findings=f"Error: {str(e)[:150]}",
                    edition=edition,
                    timestamp=timestamp,
                )
                index = i

            results_by_index[index] = fsr
            if not fsr.checked:
                unchecked.append(fname)

            finding_preview = fsr.findings[:60].replace("\n", " ")
            print(f" [{index+1}/{len(all_feeds)}] {fname} (Tier {tier}) -> {finding_preview}...")

    ordered_results = [results_by_index[i] for i in range(len(all_feeds))]
    checked_count = sum(1 for r in ordered_results if r.checked)

    return {
        "results": ordered_results,
        "feeds_checked": checked_count,
        "total_feeds": TOTAL_NAMED_FEEDS,
        "all_checked": checked_count == TOTAL_NAMED_FEEDS,
        "bypass_required": checked_count < TOTAL_NAMED_FEEDS,
        "bypass_feeds": unchecked,
        "adversarial_queries": adv_queries,
    }


def persist_sweep_results(results: List[FeedSweepResult]):
    for r in results:
        insert_row("feed_sweep_results", {
            "feed_name": r.feed_name,
            "tier": r.tier,
            "checked": 1 if r.checked else 0,
            "findings": r.findings,
            "edition": r.edition,
            "timestamp": r.timestamp,
        })
