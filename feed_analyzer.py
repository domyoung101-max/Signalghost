"""
feed_analyzer.py — Signalghost feed intelligence analysis.

Takes raw feed findings from feeds.py and uses Claude API to produce:
1. Likelihood ratios per hypothesis (for AI-009 Bayesian update)
2. Causal edge observations (for AI-012-1)
3. Prediction resolution recommendations (for Gate 5)
4. H4 gap / Tier 1 denial / prep action flags (for PMM-004 / AI-012-10)

The API is used ONLY for interpreting intelligence — never for probability
math, gate logic, calibration, timestamps, or governance. All numerical
operations happen in calibration_pipeline.py.
"""

import os
import json
import re
from typing import List, Dict, Optional


def _get_api_key() -> Optional[str]:
    return os.environ.get("ANTHROPIC_API_KEY")


def analyze_feeds(
    feed_results: List[Dict],
    hypotheses: List[Dict],
    open_predictions: List[Dict],
    causal_edges: List[Dict],
    current_date: str,
) -> Dict:
    """Analyze feed findings and produce structured intelligence output.

    Returns dict with:
    likelihood_ratios : dict mapping hyp_id -> list of {description, lr}
    causal_observations : list of {cause, effect, observed_signal}
    prediction_resolutions : list of {pred_ref, outcome, evidence, fi}
    h4_flags : dict mapping hyp_id -> {h4_gap_active, tier1_denial, no_prep_action}
    key_developments : list of strings for executive summary
    """
    key = _get_api_key()
    if not key:
        return _empty_analysis(hypotheses)

    feed_summary = ""
    for fr in feed_results:
        findings = fr.get("findings", "")
        if findings and "NO NEW FINDINGS" not in findings:
            feed_summary += f"\n[{fr['feed_name']} (Tier {fr['tier']})]:\n{findings}\n"

    if not feed_summary.strip():
        return _empty_analysis(hypotheses)

    hyp_context = "\n".join(
        f" {h['hyp_id']} (Case {h['case_id']}): {h['range_lower']*100:.0f}-{h['range_upper']*100:.0f}%, "
        f"pt={h['point_estimate']:.2f}, status={h.get('status','')}"
        for h in hypotheses
    )

    pred_context = "\n".join(
        f" {p['pred_ref']}: {p['flag']} | Window: {p['window']} | "
        f"Disconfirmation: {p['disconfirmation']}"
        for p in open_predictions
    )

    edge_context = "\n".join(
        f" {e['cause']} -> {e['effect']}: strength={e.get('new_strength', e.get('prior_strength', 0)):.2f}"
        for e in causal_edges[:10]
    )

    prompt = f"""You are an intelligence analyst for the Signalghost forecasting system.
Today's date: {current_date}

Below are the latest findings from monitored feeds, followed by the current
hypotheses, open predictions, and causal edges.

FEED FINDINGS:
{feed_summary}

CURRENT HYPOTHESES:
{hyp_context}

OPEN PREDICTIONS:
{pred_context}

CAUSAL EDGES:
{edge_context}

Based ONLY on the feed findings above, produce a JSON analysis with these fields:

1. \"likelihood_ratios\": For each hypothesis where the feed findings provide NEW
evidence (not just restatement of known facts), provide a likelihood ratio.
LR > 1.0 means evidence supports the hypothesis. LR < 1.0 means evidence
undermines it. LR = 1.0 means no new evidence. Only include hypotheses where
there IS new evidence. Format:
{{\"hyp_id\": \"H-A1\", \"description\": \"brief reason\", \"lr\": 0.8, \"source_tier\": 2, \"source_name\": \"Al Jazeera\"}}
IMPORTANT: Always include \"source_tier\" (1-4) and \"source_name\" (the feed name).

TIER CONSTRAINTS:
- If the new evidence comes from Tier 1 source: LR may range 0.33 to 3.0
- If from Tier 2: LR may range 0.5 to 2.0
- If from Tier 3: LR may range 0.67 to 1.5 (corroboration required)
- If from Tier 4 (Wikipedia, ACLED): LR MUST be between 0.83 and 1.2 only
State the source tier in the description if it influenced your LR.

2. \"causal_observations\": For any causal edge where the feed findings provide
an update, give the observed signal. 1.0 = confirmed, 0.0 = contradicted,
0.5 = ambiguous. Format:
{{\"cause\": \"...\", \"effect\": \"...\", \"observed_signal\": 1.0}}

3. \"prediction_resolutions\": For any prediction where the feed findings provide
DEFINITIVE evidence meeting the disconfirmation threshold, recommend resolution.
Only recommend resolution when evidence is clear. Format:
{{\"pred_ref\": \"PRED-034-A\", \"outcome\": \"CONTRADICTED\", \"evidence\": \"brief evidence\", \"fi\": 0.56}}

4. \"h4_flags\": For Case A hypotheses only, assess whether:
- h4_gap_active: Is there a gap between US assertions and Iranian assertions?
- tier1_denial: Is there an active Tier 1 Iranian denial?
- no_prep_action: Is there no observable Iranian-side preparatory action?
Format: {{\"hyp_id\": \"H-A1\", \"h4_gap_active\": true, \"tier1_denial\": false, \"no_prep_action\": true}}

5. \"key_developments\": List of 3-5 most significant developments from the feeds.

Respond ONLY with valid JSON. No other text. Do not invent evidence not in the feeds.
If there is no new evidence for a field, return an empty list for that field."""

    try:
        import anthropic
        import time

        client = anthropic.Anthropic(api_key=key)

        message = None
        for attempt in range(5):
            try:
                message = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=4096,
                    system=(
                        "You are a structured intelligence analyst. Respond ONLY with "
                        "valid JSON. No markdown, no commentary, no backticks. "
                        "Do not invent facts not present in the feed findings. "
                        "Do not generate probabilities — only likelihood ratios."
                    ),
                    messages=[{"role": "user", "content": prompt}],
                )
                time.sleep(3)
                break
            except anthropic.RateLimitError:
                wait = 10 * (attempt + 1)
                print(f" Rate limited — waiting {wait}s (attempt {attempt + 1}/5)...")
                time.sleep(wait)

        if message is None:
            print(" Feed analysis: rate limit exceeded after 5 attempts.")
            return _empty_analysis(hypotheses)

        full_text = ""
        for block in message.content:
            if hasattr(block, "text"):
                full_text += block.text

        cleaned = full_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        parsed = json.loads(cleaned)

        return {
            "likelihood_ratios": _parse_lrs(parsed.get("likelihood_ratios", []), feed_results),
            "causal_observations": parsed.get("causal_observations", []),
            "prediction_resolutions": parsed.get("prediction_resolutions", []),
            "h4_flags": _parse_h4_flags(parsed.get("h4_flags", [])),
            "key_developments": parsed.get("key_developments", []),
        }

    except (json.JSONDecodeError, Exception) as e:
        print(f" Feed analysis error: {str(e)[:100]}")
        return _empty_analysis(hypotheses)


def _parse_lrs(raw_lrs: list, feed_results: List[Dict] = None) -> Dict[str, List[Dict]]:
    """Parse likelihood ratios into dict keyed by hyp_id.

    FIX (Items 3+4): Evidence Weight Ladder — mechanical per-tier LR clamping.
    Rule 3: Tier 1 > 2 > 3 > 4 in permitted LR range.
    Gate 0.4: Tier 1 HIGH-incentive feeds with no independent competing
              Tier 1 corroboration are downgraded to Tier 2 range.
    """
    from config import TIER_LR_RANGES, TIER_LR_DEFAULT, TIER1_HIGH_INCENTIVE_FEEDS

    result: Dict[str, List[Dict]] = {}
    if not isinstance(raw_lrs, list):
        return result

    # Build set of Tier 1 feed names that produced findings this sweep
    # (used for Gate 0.4 incentive downgrade check)
    tier1_feeds_active: set = set()
    if feed_results:
        for fr in feed_results:
            if fr.get("tier") == 1:
                findings = fr.get("findings", "") or ""
                if findings and "NO NEW FINDINGS" not in findings and len(findings) > 30:
                    tier1_feeds_active.add((fr.get("feed_name", "") or "").lower())

    for entry in raw_lrs:
        if not isinstance(entry, dict):
            continue
        hyp_id = entry.get("hyp_id", "")
        if not hyp_id:
            continue
        if hyp_id not in result:
            result[hyp_id] = []

        lr = float(entry.get("lr", 1.0))
        source_tier = int(entry.get("source_tier", 0) or 0)
        source_name = (entry.get("source_name", "") or "").lower()

        # If tier not provided by model, try to infer from description
        if source_tier == 0:
            desc_lower = entry.get("description", "").lower()
            if "tier 1" in desc_lower:
                source_tier = 1
            elif "tier 2" in desc_lower:
                source_tier = 2
            elif "tier 3" in desc_lower:
                source_tier = 3
            elif "tier 4" in desc_lower:
                source_tier = 4
            else:
                source_tier = 3  # conservative default

        # Gate 0.4 Tier 1 HIGH-incentive downgrade (Item 3):
        # If source is Tier 1 AND is in the high-incentive list AND
        # no other independent Tier 1 feed corroborates this edition,
        # downgrade effective tier to 2.
        effective_tier = source_tier
        if source_tier == 1 and source_name:
            is_high_incentive = any(
                hi_feed in source_name for hi_feed in TIER1_HIGH_INCENTIVE_FEEDS
            )
            if is_high_incentive:
                # Check: is there another Tier 1 feed active that is NOT
                # in the high-incentive list?
                independent_tier1 = any(
                    f for f in tier1_feeds_active
                    if not any(hi in f for hi in TIER1_HIGH_INCENTIVE_FEEDS)
                )
                if not independent_tier1:
                    effective_tier = 2  # downgrade to Tier 2 range

        # Apply mechanical per-tier LR clamp (Item 4)
        lr_min, lr_max = TIER_LR_RANGES.get(effective_tier, TIER_LR_DEFAULT)
        lr = max(lr_min, min(lr_max, lr))

        result[hyp_id].append({
            "description": entry.get("description", "feed evidence"),
            "lr": lr,
            "source_tier": source_tier,
            "effective_tier": effective_tier,
            "source_name": source_name,
        })

    return result


def _parse_h4_flags(raw_flags: list) -> Dict[str, Dict]:
    """Parse H4 flags into dict keyed by hyp_id."""
    result: Dict[str, Dict] = {}
    if not isinstance(raw_flags, list):
        return result

    for entry in raw_flags:
        if not isinstance(entry, dict):
            continue
        hyp_id = entry.get("hyp_id", "")
        if not hyp_id:
            continue
        result[hyp_id] = {
            "h4_gap_active": bool(entry.get("h4_gap_active", False)),
            "tier1_denial": bool(entry.get("tier1_denial", False)),
            "no_prep_action": bool(entry.get("no_prep_action", True)),
        }

    return result


def _empty_analysis(hypotheses: List[Dict]) -> Dict:
    """Return empty analysis when API is unavailable or feeds have no findings."""
    return {
        "likelihood_ratios": {},
        "causal_observations": [],
        "prediction_resolutions": [],
        "h4_flags": {},
        "key_developments": ["No new feed data available for analysis."],
    }


# ═══════════════════════════════════════════════════════════════════════════
# AI-010 CLUSTER DETECTION
# ═══════════════════════════════════════════════════════════════════════════

_TIER3_CLUSTERS = {
    "iranian_state": [
        "tasnim", "mehr", "wana", "irna", "press tv", "fars",
    ],
    "gulf_state": [
        "house of saud", "conflict pulse", "al arabiya",
    ],
}


def detect_source_clusters(
    feed_results: List[Dict],
    hypotheses: List[Dict],
) -> Dict[str, Dict]:
    """Detect single-cluster sourcing for each hypothesis."""
    result: Dict[str, Dict] = {}

    tier3_findings = []
    for fr in feed_results:
        tier = fr.get("tier", 0)
        if tier != 3:
            continue
        findings = (fr.get("findings", "") or "").lower()
        name = (fr.get("feed_name", "") or "").lower()
        if findings and len(findings) > 30 and "no new findings" not in findings:
            tier3_findings.append({
                "name": name,
                "findings": findings,
                "cluster": _identify_cluster(name),
            })

    h5_signals = _detect_h5_contradictions(feed_results)

    for hyp in hypotheses:
        hyp_id = hyp.get("hyp_id", "")
        case_id = hyp.get("case_id", "")
        case_keywords = _get_case_keywords(case_id)

        supporting = []
        for t3 in tier3_findings:
            relevance = sum(1 for kw in case_keywords if kw in t3["findings"])
            if relevance > 0:
                supporting.append(t3)

        if not supporting:
            result[hyp_id] = {
                "single_cluster": False,
                "h5_contradiction": False,
                "cluster_name": "",
                "supporting_sources": [],
            }
            continue

        clusters_found = set(s["cluster"] for s in supporting if s["cluster"])
        single_cluster = len(clusters_found) == 1 and len(supporting) >= 2
        h5_active = h5_signals.get(case_id, False)

        result[hyp_id] = {
            "single_cluster": single_cluster,
            "h5_contradiction": h5_active,
            "cluster_name": list(clusters_found)[0] if clusters_found else "",
            "supporting_sources": [s["name"] for s in supporting],
        }

    return result


def _identify_cluster(feed_name: str) -> str:
    """Map a feed name to its cluster family."""
    name_lower = feed_name.lower()
    for cluster_name, members in _TIER3_CLUSTERS.items():
        for member in members:
            if member in name_lower:
                return cluster_name
    return ""


def _get_case_keywords(case_id: str) -> List[str]:
    """Return keywords for case relevance matching."""
    keywords = {
        "A": ["talks", "negotiat", "diplomat", "peace", "ceasefire", "proposal"],
        "B": ["hormuz", "strait", "mine", "naval", "maritime", "shipping", "blockade"],
        "C": ["netanyahu", "strike", "idf", "hezbollah", "lebanon", "drone"],
        "D": ["gl u", "general license", "sanctions", "ofac", "chabahar", "waiver"],
        "E": ["yanbu", "petroline", "aramco", "saudi", "proxy", "red sea", "houthi"],
    }
    return keywords.get(case_id, [])


def _detect_h5_contradictions(feed_results: List[Dict]) -> Dict[str, bool]:
    """Detect H5 structural contradictions per case."""
    result: Dict[str, bool] = {}

    diplomatic_claims = []
    military_claims = []

    for fr in feed_results:
        name = (fr.get("feed_name", "") or "").lower()
        findings = (fr.get("findings", "") or "").lower()
        if not findings or len(findings) < 30:
            continue

        is_diplomatic = any(
            kw in name or kw in findings
            for kw in ["araghchi", "foreign minister", "diplomat", "ambassador", "snsc", "peace", "talks"]
        )
        is_military = any(
            kw in name or kw in findings
            for kw in ["irgc", "centcom", "idf", "military", "naval", "strike", "sank", "fired"]
        )

        if is_diplomatic:
            diplomatic_claims.append(findings[:200])
        if is_military:
            military_claims.append(findings[:200])

    if diplomatic_claims and military_claims:
        diplo_optimistic = any(
            kw in " ".join(diplomatic_claims)
            for kw in ["positive", "progress", "constructive", "reviewing", "breakthrough"]
        )
        mil_escalatory = any(
            kw in " ".join(military_claims)
            for kw in ["sank", "fired", "strike", "attack", "escalat", "control zone"]
        )
        if diplo_optimistic and mil_escalatory:
            result["A"] = True
            result["B"] = True

    ceasefire_claims = any(
        "ceasefire" in c and ("hold" in c or "maintain" in c)
        for c in diplomatic_claims + military_claims
    )
    violation_claims = any(
        kw in " ".join(military_claims)
        for kw in ["drone", "violation", "barrage", "rocket", "evacuation"]
    )
    if ceasefire_claims and violation_claims:
        result["C"] = True

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Carry-forward fact extraction hardening
# ═══════════════════════════════════════════════════════════════════════════

_BANNED_FACT_PATTERNS = [
    r"\bi need to search\b",
    r"\blet me search\b",
    r"\bbased on (the )?(search results|latest|my search|recent search)\b",
    r"\bhere are the verifiable facts\b",
    r"\bapi unavailable\b",
    r"\brate limit(ed)?\b",
    r"\bsearch again for more information\b",
    r"\boriginal length:\b",
    r"\btruncated\b",
    r"\bnow let me search\b",
]

_FACT_EVENT_TERMS = {
    "stated", "said", "reported", "issued", "confirmed", "announced", "warned",
    "disabled", "seized", "fired", "struck", "attacked", "met", "resumed",
    "halted", "ordered", "threatened", "published", "transited", "wounded",
    "sanctioned", "rejected", "accepted", "signed", "renewed", "lapsed",
}

_FACT_ACTOR_TERMS = {
    "trump", "iran", "u.s.", "us", "araghchi", "idf", "centcom", "hezbollah",
    "netanyahu", "iaea", "ofac", "treasury", "china", "beijing", "mehr",
    "tasnim", "wana", "saudi", "hormuz", "lebanon", "israel", "irgc",
}


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _looks_like_meta_boilerplate(text: str) -> bool:
    lowered = _normalize_space(text).lower()
    if not lowered:
        return True
    return any(re.search(pattern, lowered) for pattern in _BANNED_FACT_PATTERNS)


def _split_sentences(text: str) -> List[str]:
    text = _normalize_space(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [_normalize_space(p.strip(" -•\t")) for p in parts if _normalize_space(p.strip(" -•\t"))]


def _sentence_is_fact_candidate(sentence: str) -> bool:
    if not sentence or len(sentence) < 25:
        return False
    if _looks_like_meta_boilerplate(sentence):
        return False

    lowered = sentence.lower()
    has_event = any(term in lowered for term in _FACT_EVENT_TERMS)
    has_actor = any(term in lowered for term in _FACT_ACTOR_TERMS)
    has_date_or_number = bool(re.search(r"\b\d{1,4}\b|\bmay\b|\bapril\b|\bjune\b", lowered))

    if sentence.endswith(":"):
        return False

    if has_actor and (has_event or has_date_or_number):
        return True

    if has_event and has_date_or_number:
        return True

    return False


def _clean_fact_sentence(sentence: str) -> str:
    cleaned = sentence.replace("**", "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(" -•\t")
    return cleaned[:240]


def extract_carry_forward_facts(
    feed_results: List[Dict],
    existing_facts: List[Dict],
    current_date: str,
) -> List[Dict]:
    """Extract carry-forward facts from feed findings.

    Combines new feed findings with existing carry-forward facts.
    Updates staleness and last_verified for facts confirmed by new feeds.
    Prunes facts older than 3 editions.
    Returns list of dicts with: fact, last_verified, ed_action, staleness_editions.
    """
    updated_facts: List[Dict] = []

    for ef in existing_facts:
        edition_age = ef.get("staleness_editions", 0) or 0
        try:
            edition_age = int(edition_age)
        except (TypeError, ValueError):
            edition_age = 0

        if edition_age >= 3:
            continue

        staleness_label, ed_action = grade_staleness(edition_age)

        fact_text = _normalize_space(str(ef.get("fact", "")))
        if fact_text and not _looks_like_meta_boilerplate(fact_text):
            updated_facts.append({
                "fact": fact_text,
                "last_verified": ef.get("last_verified", ""),
                "ed_action": ed_action,
                "staleness_editions": edition_age + 1,
                "staleness_label": staleness_label,
            })

    seen_facts = {f["fact"].lower() for f in updated_facts if f.get("fact")}

    for fr in feed_results:
        findings = fr.get("findings", "") or ""
        feed_name = fr.get("feed_name", "")
        tier = fr.get("tier", 0)

        if not findings:
            continue
        if "NO NEW FINDINGS" in findings:
            continue
        if _looks_like_meta_boilerplate(findings) and len(findings) < 300:
            continue

        for sentence in _split_sentences(findings):
            if not _sentence_is_fact_candidate(sentence):
                continue

            cleaned = _clean_fact_sentence(sentence)
            if not cleaned:
                continue
            if cleaned.lower() in seen_facts:
                continue

            updated_facts.append({
                "fact": cleaned,
                "last_verified": f"{feed_name} Tier {tier}. {current_date}. CURRENT.",
                "ed_action": "Re-verify next edition.",
                "staleness_editions": 0,
            })
            seen_facts.add(cleaned.lower())

    return updated_facts[:30]


def build_heuristic_summary(cases: List[Dict], edition: int) -> str:
    """Build heuristic dominance summary for H1 saturation check."""
    parts = []
    for case in cases:
        cid = case.get("case_id", "")
        if cid == "A":
            parts.append("Case A: H4 primary (narrative vs outcome gap). H1 secondary (incentive). H6 tertiary.")
        elif cid == "B":
            parts.append("Case B: H6 primary (suppressed intersection — blockade/Hormuz). H4 secondary. H1 tertiary.")
        elif cid == "C":
            parts.append("Case C: H4 primary (ceasefire narrative vs violations). H6 secondary. H2 tertiary (timing).")
        elif cid == "D":
            parts.append("Case D: H3 primary (beneficiary asymmetry). H6 secondary. H1 tertiary.")
        elif cid == "E":
            parts.append("Case E: H6 primary (suppressed intersection — multi-case). H3 secondary. H1 tertiary.")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# GATE 0.6 DYNAMIC ABSENCE & THRESHOLD DETECTION (Item 5 + Item 6)
# ═══════════════════════════════════════════════════════════════════════════

# Threshold definitions: each maps a case_id to a list of
# (keyword_pattern, threshold_description, numeric_threshold_if_any)
_THRESHOLD_DEFINITIONS = {
    "C": [
        (["rocket", "barrage", "100"], "100+ rockets at Israeli territory", 100),
        (["hezbollah", "escalat", "massive"], "Hezbollah massive escalation", None),
    ],
    "B": [
        (["hormuz", "blockade", "closed"], "Strait of Hormuz blockade/closure", None),
        (["irgc", "sank", "vessel"], "IRGC kinetic attack on vessel", None),
        (["mine", "hormuz"], "Mine confirmed in Strait of Hormuz", None),
    ],
    "D": [
        (["ofac", "enforcement"], "OFAC enforcement action on Chabahar operators", None),
        (["sanctions", "chabahar", "designat"], "Chabahar sanctions designation", None),
    ],
    "E": [
        (["yanbu", "strike"], "Further IRGC strike on Yanbu/Petroline", None),
        (["petroline", "attack"], "Petroline infrastructure attack", None),
    ],
    "A": [
        (["talks", "collapse", "fail"], "Talks collapse / breakdown", None),
        (["strike", "iran", "resum"], "US/Israeli strikes on Iran resume", None),
    ],
}

# Absence claim definitions: standard claims that must be verified each edition
_ABSENCE_DEFINITIONS = [
    {"claim": "No IRGC Yanbu/Petroline strike", "keywords": ["yanbu", "petroline", "strike", "attack"], "case_id": "E"},
    {"claim": "No Hezbollah 100+ rocket barrage confirmed", "keywords": ["hezbollah", "100", "rocket", "barrage"], "case_id": "C"},
    {"claim": "No OFAC enforcement action", "keywords": ["ofac", "enforcement", "sanctions", "chabahar"], "case_id": "D"},
    {"claim": "No Hormuz blockade or mine event", "keywords": ["hormuz", "blockade", "mine", "closed"], "case_id": "B"},
]


def detect_threshold_events(feed_results: List[Dict]) -> List[Dict]:
    """Item 6: Scan feed findings for threshold breach events.

    Instead of hardcoding threshold events in session_executor, this function
    dynamically detects them from actual feed content.

    Returns list of dicts for Gate 0.6 threshold_events parameter:
      - event: str
      - threshold: str
      - confirmed: bool
      - source: str
      - case_id: str
    """
    events = []

    # Combine all feed findings into a searchable corpus per feed
    for fr in feed_results:
        findings = (fr.get("findings", "") or "").lower()
        feed_name = fr.get("feed_name", "")
        tier = fr.get("tier", 4)

        if not findings or len(findings) < 30 or "no new findings" in findings:
            continue

        for case_id, thresholds in _THRESHOLD_DEFINITIONS.items():
            for keywords, description, numeric_threshold in thresholds:
                # All keywords must appear in the findings
                keyword_hits = sum(1 for kw in keywords if kw in findings)

                if keyword_hits >= len(keywords) - 1 and keyword_hits >= 2:
                    # Check numeric threshold if applicable
                    confirmed = False
                    if numeric_threshold:
                        numbers = re.findall(r'\d+', findings)
                        if numbers:
                            max_num = max(int(n) for n in numbers)
                            if max_num >= numeric_threshold:
                                confirmed = True
                        # Without numeric confirmation, not yet breached
                    else:
                        # Non-numeric threshold: keyword density is the signal
                        # Require all keywords present AND a confirming verb
                        confirm_verbs = ["confirmed", "struck", "attacked",
                                         "closed", "blockade", "sank", "fired",
                                         "launched", "collapsed"]
                        if (keyword_hits >= len(keywords)
                                and any(v in findings for v in confirm_verbs)):
                            confirmed = True

                    events.append({
                        "event": description,
                        "threshold": description,
                        "confirmed": confirmed,
                        "source": feed_name,
                        "case_id": case_id,
                        "tier": tier,
                    })

    # Deduplicate: keep strongest signal per threshold
    seen = {}
    for ev in events:
        key = ev["event"]
        if key not in seen or (ev["confirmed"] and not seen[key]["confirmed"]):
            seen[key] = ev
    return list(seen.values())


def build_dynamic_absence_claims(feed_results: List[Dict]) -> List[Dict]:
    """Item 5: Build absence claims from actual feed sweep results.

    Instead of hardcoded absence claims, verify each standard absence claim
    against the feeds that were actually checked.

    Returns list of dicts for Gate 0.6 absence_claims parameter:
      - claim: str
      - feeds_checked: list of feed names
      - verified: bool (True = feeds checked AND no result returned)
    """
    claims = []

    for absence_def in _ABSENCE_DEFINITIONS:
        claim_text = absence_def["claim"]
        keywords = absence_def["keywords"]

        # Which feeds were checked and had content?
        feeds_checked = []
        evidence_found = False

        for fr in feed_results:
            findings = (fr.get("findings", "") or "").lower()
            feed_name = fr.get("feed_name", "")

            if not findings or "no new findings" in findings:
                # Feed was checked but had no findings — counts as checked
                feeds_checked.append(feed_name)
                continue

            if len(findings) < 30:
                continue

            feeds_checked.append(feed_name)

            # Check if this feed's findings contradict the absence claim
            keyword_hits = sum(1 for kw in keywords if kw in findings)
            confirm_verbs = ["confirmed", "struck", "attacked", "closed",
                             "sank", "fired", "launched"]
            has_confirming_verb = any(v in findings for v in confirm_verbs)

            if keyword_hits >= 2 and has_confirming_verb:
                evidence_found = True

        claims.append({
            "claim": claim_text,
            "feeds_checked": feeds_checked,
            "verified": len(feeds_checked) > 0 and not evidence_found,
        })

    return claims


# ═══════════════════════════════════════════════════════════════════════════
# GRADED STALENESS (Item 20)
# ═══════════════════════════════════════════════════════════════════════════

STALENESS_GRADES = {
    # (min_editions, max_editions): (label, action)
    (0, 0): ("CURRENT", "Re-verify next edition."),
    (1, 1): ("AGEING", "Re-verify before use."),
    (2, 2): ("STALE", "DO NOT CITE WITHOUT RE-VERIFICATION."),
    (3, 4): ("PERMANENTLY STALE", "MUST BE RE-VERIFIED OR DROPPED. Cannot govern."),
}


def grade_staleness(edition_age: int) -> tuple:
    """Return (staleness_label, ed_action) for a given edition age.

    Item 20: Graded staleness system.
    0 editions = CURRENT
    1 edition  = AGEING
    2 editions = STALE (do not cite)
    3-4 editions = PERMANENTLY STALE (cannot govern)
    5+ editions = pruned entirely
    """
    for (lo, hi), (label, action) in STALENESS_GRADES.items():
        if lo <= edition_age <= hi:
            return label, f"{label} ({edition_age} editions). {action}"
    if edition_age >= 5:
        return "PRUNED", "Fact pruned — too stale."
    return "CURRENT", "Re-verify next edition."


# ═══════════════════════════════════════════════════════════════════════════
# PCP NEW CASE DETECTION hardening
# ═══════════════════════════════════════════════════════════════════════════

_EXISTING_CASE_ACTORS = {
    "A": {"trump", "araghchi", "iran", "us", "talks", "ceasefire", "14-point",
          "witkoff", "kushner", "sullivan", "pakistan", "oman", "qatar"},
    "B": {"hormuz", "strait", "mine", "clearance", "naval", "centcom",
          "fifth fleet", "blockade", "shipping", "tanker", "avenger"},
    "C": {"netanyahu", "idf", "hezbollah", "lebanon", "litani", "strike",
          "nasrallah", "unifil", "ceasefire", "kfar giladi"},
    "D": {"gl u", "general license", "sanctions", "ofac", "treasury",
          "chabahar", "india", "waiver", "wind-down"},
    "E": {"yanbu", "petroline", "aramco", "saudi", "houthi", "red sea",
          "proxy", "pipeline", "bab al-mandab"},
}

_STOP_ENTITIES = {
    "the", "this", "that", "based", "according", "however",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march",
    "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "gate", "tier",
    "fact", "inference", "hybrid", "current", "edition",
    "part", "case", "source",
}


def _extract_candidate_entities(text: str) -> List[str]:
    original_tokens = re.findall(r"\b[A-Z][A-Za-z0-9\-]{3,}\b", text or "")
    entities = []
    seen = set()
    for token in original_tokens:
        entity = token.lower().strip(".,;:\"'()[]{}")
        if not entity or entity in _STOP_ENTITIES:
            continue
        if entity not in seen:
            seen.add(entity)
            entities.append(entity)
    return entities


def _covered_by_existing_case(entity: str, findings: str) -> List[str]:
    covered = []
    lowered = (findings or "").lower()

    for case_id, actors in _EXISTING_CASE_ACTORS.items():
        if entity in actors:
            covered.append(case_id)
            continue
        proximity_hits = 0
        for actor in actors:
            if actor in lowered:
                proximity_hits += 1
        if proximity_hits >= 2:
            covered.append(case_id)

    return sorted(set(covered))


def _infer_distribution_independence(entity: str, findings: str, covered_cases: List[str]) -> bool:
    lowered = (findings or "").lower()

    if covered_cases:
        return False

    if entity in lowered and any(
        kw in lowered for kw in ["summit", "sanctions", "seized", "attacked", "talks", "ceasefire", "shipment"]
    ):
        return True

    return False


def _infer_disconfirmation_expressible(entity: str, findings: str, covered_cases: List[str]) -> bool:
    lowered = (findings or "").lower()

    if covered_cases:
        return True

    if any(kw in lowered for kw in ["talks", "ceasefire", "summit", "shipment", "sanctions", "strike"]):
        return False

    return True


def detect_new_case_signals(
    feed_results: List[Dict],
    existing_cases: List[Dict],
) -> List[Dict]:
    """PCP Step 1.5 — Detect signals that may require a new case.

    Three conditions must ALL be met for a new case recommendation:
    1. New actor not from any active case
    2. Independent probability distribution from existing hypotheses
    3. Disconfirmation cannot be expressed within existing cases

    Returns candidate signals with explicit decision reasons.
    """
    actor_map: Dict[str, Dict] = {}

    for fr in feed_results:
        findings = fr.get("findings", "") or ""
        if not findings or len(findings) < 50:
            continue
        if "NO NEW FINDINGS" in findings:
            continue
        if _looks_like_meta_boilerplate(findings):
            continue

        entities = _extract_candidate_entities(findings)
        for entity in entities:
            if entity in _STOP_ENTITIES:
                continue

            if entity not in actor_map:
                actor_map[entity] = {
                    "actor": entity,
                    "feeds": set(),
                    "sample_texts": [],
                }

            actor_map[entity]["feeds"].add(fr.get("feed_name", ""))
            if len(actor_map[entity]["sample_texts"]) < 3:
                actor_map[entity]["sample_texts"].append(findings[:240])

    signals = []
    for actor, row in actor_map.items():
        mention_count = len(row["feeds"])
        if mention_count < 2:
            continue

        joined_text = " ".join(row["sample_texts"])
        covered_cases = _covered_by_existing_case(actor, joined_text)
        independent_distribution = _infer_distribution_independence(actor, joined_text, covered_cases)
        disconfirmation_expressible = _infer_disconfirmation_expressible(actor, joined_text, covered_cases)

        decision = "MONITOR"
        reasons = []

        if covered_cases:
            reasons.append(f"Covered by existing case(s): {', '.join(covered_cases)}")
        else:
            reasons.append("Actor not directly covered by existing case actors")

        if independent_distribution:
            reasons.append("Appears to introduce an independent probability distribution")
        else:
            reasons.append("Does not yet demonstrate independent distribution from existing cases")

        if disconfirmation_expressible:
            reasons.append("Disconfirmation still expressible within existing cases")
        else:
            reasons.append("Disconfirmation not cleanly expressible within existing cases")

        if (not covered_cases) and independent_distribution and (not disconfirmation_expressible) and mention_count >= 3:
            decision = "NEW_CASE"
            reasons.append("All three new-case conditions satisfied at multi-feed threshold")
        else:
            reasons.append("Conservative hold: monitor unless all three conditions are satisfied")

        signals.append({
            "actor": actor,
            "description": f"Candidate actor '{actor}' appeared across {mention_count} feed(s)",
            "feeds": sorted(row["feeds"]),
            "mention_count": mention_count,
            "covered_by_existing_case": covered_cases,
            "independent_distribution": independent_distribution,
            "disconfirmation_expressible": disconfirmation_expressible,
            "decision_reason": " | ".join(reasons),
            "recommendation": decision,
        })

    signals.sort(key=lambda s: (-s["mention_count"], s["actor"]))
    return signals[:5]
