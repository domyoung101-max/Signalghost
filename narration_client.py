"""narration_client.py — Signalghost Claude API narration (v2.2.0).

Generates grounded analytical prose for the edition PDF.

KEY PRINCIPLES:
- Prose references SPECIFIC actors, dates, sources — not abstract pipeline mechanics
- Hypothesis names come from SESSION_STATE, not AI-invented generic labels
- Claim-type labelling: [FACT], [INFERENCE], [FACT / INFERENCE hybrid]
- No pipeline jargon in prose
- Pipeline stage annotations go in calibration products ONLY
- Gate 0.4 confidence assessments per fact
- Dominant heuristic identification per case
- Post-generation rhetorical discipline: [FACT] sentences must read as facts
- Post-generation traceability discipline: [FACT] sentences must contain a
  named source anchor from the current feed sweep or be downgraded
"""

import os
import re
import time
from typing import Dict, List, Optional, Set


# ═══════════════════════════════════════════════════════════════════════════
# API AVAILABILITY
# ═══════════════════════════════════════════════════════════════════════════

def get_api_key() -> Optional[str]:
    return os.environ.get("ANTHROPIC_API_KEY")


def is_narration_available() -> bool:
    key = get_api_key()
    if not key:
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False



def _call_api(prompt: str, system_msg: str = "", max_tokens: int = 2048) -> str:
    key = get_api_key()
    if not key:
        return "[Narration unavailable — ANTHROPIC_API_KEY not set.]"

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)

        if not system_msg:
            system_msg = (
                "You are a senior geopolitical analyst writing for the Signalghost "
                "forecasting system. Your writing style is precise, factual, and "
                "grounded in specific actors, dates, and named sources.\n\n"
                "CURRENCY AND ANTI-HALLUCINATION RULES (CRITICAL):\n"
                "- The current date is May 2026. War Day count is in the high 60s.\n"
                "- Do NOT reference any person, event, or date that is not present in the user-provided feed findings or hypothesis context.\n"
                "- Do NOT reference Biden — he is no longer president. Trump is.\n"
                "- Do NOT reference Nasrallah, Haniyeh, or Sinwar — they are dead.\n"
                "- Do NOT reference December 2024, January 2025, or any pre-2026 date unless that date is explicitly in the feed findings.\n"
                "- Do NOT invent diplomatic actors (Hochstein, Sullivan, Witkoff) unless they appear in the current feed findings.\n"
                "- Do NOT reference 'Biden administration', 'Trump transition', or 'January 20 transition' — that transition has long since happened.\n"
                "- If you only have generic hypothesis information and no fresh feed evidence, write LESS prose, not more. Concise is honest.\n\n"
                "FORMATTING RULES:\n"
                "- Prefix facts with [FACT], inferences with [INFERENCE], hybrid statements with [FACT / INFERENCE hybrid]\n"
                "- A [FACT] tag MUST trace to a specific named source from the current feed sweep. If you cannot trace it, use [INFERENCE].\n"
                "- Reference specific current people (Trump, Araghchi, Netanyahu, Khamenei, Salami, Ghalibaf, Pezeshkian, Sharif), specific places (Islamabad, Hormuz, Kfar Giladi, Yanbu, Beijing), specific 2026 dates\n"
                "- NEVER write about pipeline stages, Bayesian updates, S2/S3/S7, propagation effects, or calibration mechanics — those are internal\n"
                "- NEVER use phrases like 'probability architecture', 'buffer variance', 'analytical tension', 'pipeline annotations'\n"
                "- Write like a senior intelligence analyst briefing a minister, not like a data scientist describing a model\n"
                "- Do not generate probabilities — use only the numbers provided\n"
                "- Do not invent facts not provided in the prompt\n"
                "- If a sentence is interpretive, label it [INFERENCE] or [FACT / INFERENCE hybrid], not [FACT]\n"
                "- Every [FACT] sentence must name the source explicitly, such as the feed name or a direct attribution phrase anchored to the current feed sweep"
            )

        for attempt in range(5):
            try:
                message = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=max_tokens,
                    system=system_msg,
                    messages=[{"role": "user", "content": prompt}],
                )
                time.sleep(3)
                return message.content[0].text
            except anthropic.RateLimitError:
                wait = 10 * (attempt + 1)
                print(f"Rate limited — waiting {wait}s (attempt {attempt + 1}/5)...")
                time.sleep(wait)
        return "[Narration unavailable — rate limit exceeded after 5 attempts.]"
    except Exception as e:
        # CF-5: Log error to console but return clean placeholder for PDF.
        # Raw error strings must never appear in published output.
        print(f"  NARRATION ERROR (logged, not published): {str(e)[:200]}")
        return "[Analysis unavailable for this section. See next edition.]"


# ═══════════════════════════════════════════════════════════════════════════
# HALLUCINATION GUARD
# ═══════════════════════════════════════════════════════════════════════════

STALE_ENTITIES = {
    "biden", "biden administration", "biden's", "haniyeh", "sinwar",
    "nasrallah", "nasrallah's successor", "december 2024", "january 2025",
    "february 2025", "march 2025", "october 7", "october 26",
    "biden's final-weeks", "biden transition", "january 20 transition",
    "trump transition", "pre-inauguration", "trump's january 20",
    "october 2024", "november 2024", "december 31", "january 20",
    "before january 20", "biden's willingness", "lloyd austin",
    "antony blinken", "rishi sunak", "olaf scholz", "october 7 anniversary",
    "ali khamenei's elimination",
}

CURRENT_2026_ENTITIES = {
    "trump", "araghchi", "netanyahu", "khamenei", "salami", "ghalibaf",
    "pezeshkian", "sharif", "rubio", "wang yi", "pakistan", "islamabad",
    "hormuz", "kfar giladi", "yanbu", "beijing", "moscow", "muscat",
    "chabahar", "centcom", "irgc", "idf", "snsc", "irna", "tasnim",
    "project freedom", "epic fury", "ofac", "hezbollah", "war day",
    "may 2026", "april 2026", "march 2026", "2026",
}


# ═══════════════════════════════════════════════════════════════════════════
# CLAIM TAGS / RHETORICAL DISCIPLINE / TRACEABILITY DISCIPLINE
# ═══════════════════════════════════════════════════════════════════════════

FACT_TAG = "[FACT]"
INFERENCE_TAG = "[INFERENCE]"
HYBRID_TAG = "[FACT / INFERENCE hybrid]"

FACT_INTERPRETIVE_HEDGES = [
    "appears to", "appears", "seems to", "seems", "suggests that", "suggests",
    "indicates that", "indicates", "likely reflects", "likely signals",
    "likely indicates", "may indicate", "may reflect", "could indicate",
    "could reflect", "points to", "implies that", "implies",
    "raises the prospect of", "raises the possibility of",
]

FACT_FILLER_HEDGES = ["reportedly", "apparently", "notably"]

# FIX (Item 1 — Rule 4): Extended rhetorical hedge list.
# These are stripped from ALL narration regardless of tag — they add nothing
# to intelligence prose. Uncertainty is expressed via probability ranges,
# not weasel words.
RHETORICAL_FILLERS = [
    "reportedly", "apparently", "notably", "arguably", "perhaps",
    "potentially", "it is worth noting that", "it should be noted that",
    "it is important to note that", "it bears mentioning that",
    "interestingly", "unsurprisingly", "predictably",
]

# Multi-word hedges that need substitution (not just deletion) to
# preserve grammar.  Format: (pattern, replacement).
HEDGE_SUBSTITUTIONS = [
    ("appears to be", "is"),
    ("seem to be", "are"),
    ("seems to be", "is"),
    ("appears to have", "has"),
    ("seems to have", "has"),
    ("appears to", ""),
    ("seems to", ""),
    ("it appears that", ""),
    ("it seems that", ""),
]

INTERPRETIVE_VERBS = [
    "suggests", "indicates", "reflects", "implies", "signals", "points to",
    "demonstrates", "underscoring", "highlighting",
]

SOURCE_CUES = [
    "according to", "reported by", "stated", "said", "announced", "confirmed",
    "reported", "told", "declared", "per ", "via ",
]

ATTRIBUTION_VERBS = [
    "said", "stated", "announced", "reported", "confirmed", "declared", "told",
]



def _split_tagged_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r'\s+(?=\[(?:FACT|INFERENCE|FACT / INFERENCE hybrid)\])', text.strip())
    return [p.strip() for p in parts if p and p.strip()]



def _detect_tag(sentence: str) -> str:
    s = sentence.lstrip()
    if s.startswith(HYBRID_TAG):
        return HYBRID_TAG
    if s.startswith(FACT_TAG):
        return FACT_TAG
    if s.startswith(INFERENCE_TAG):
        return INFERENCE_TAG
    return ""



def _replace_leading_tag(sentence: str, new_tag: str) -> str:
    return re.sub(r'^\[(?:FACT|INFERENCE|FACT / INFERENCE hybrid)\]', new_tag, sentence.strip(), count=1)



def _strip_leading_tag(sentence: str) -> str:
    return re.sub(r'^\[(?:FACT|INFERENCE|FACT / INFERENCE hybrid)\]\s*', '', sentence.strip(), count=1)



def _contains_any(text: str, phrases: List[str]) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in phrases)



def _count_matches(text: str, phrases: List[str]) -> int:
    lowered = text.lower()
    return sum(1 for p in phrases if p in lowered)



def _clean_prose_spacing(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r'\s+,', ',', cleaned)
    cleaned = re.sub(r'\s+\.', '.', cleaned)
    cleaned = re.sub(r'\s+;', ';', cleaned)
    cleaned = re.sub(r'\s+:', ':', cleaned)
    cleaned = re.sub(r'\(\s+', '(', cleaned)
    cleaned = re.sub(r'\s+\)', ')', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = re.sub(r',\s*,', ', ', cleaned)
    return cleaned.strip()



def _remove_filler_hedges_from_fact(body: str) -> str:
    cleaned = body
    for hedge in FACT_FILLER_HEDGES:
        cleaned = re.sub(rf'\b{re.escape(hedge)}\b\s*', '', cleaned, flags=re.IGNORECASE)
    return _clean_prose_spacing(cleaned)



def _fact_sentence_is_interpretive(body: str) -> bool:
    lowered = body.lower()
    if _contains_any(lowered, FACT_INTERPRETIVE_HEDGES):
        return True
    if _count_matches(lowered, INTERPRETIVE_VERBS) >= 2:
        return True
    if any(tok in lowered for tok in ["suggesting", "indicating", "implying"]):
        return True
    return False



def _fact_sentence_is_plainly_sourced(body: str) -> bool:
    lowered = body.lower()
    if _contains_any(lowered, SOURCE_CUES):
        return True
    if any(token in lowered for token in [" tier 1", " tier 2", " tier 3", " gate 0.4", " confidence "]):
        return True
    return False



def _normalize_source_name(name: str) -> str:
    n = (name or "").strip().lower()
    n = re.sub(r'\s+', ' ', n)
    n = n.replace("-", " ")
    n = re.sub(r'[^a-z0-9 ]+', '', n)
    return n.strip()



def _source_variants(name: str) -> Set[str]:
    base = _normalize_source_name(name)
    variants = set()
    if not base:
        return variants
    variants.add(base)
    parts = [p for p in base.split() if p]
    if len(parts) >= 2:
        variants.add(" ".join(parts[:2]))
        variants.add(parts[0])
        variants.add(parts[-1])
    elif len(parts) == 1:
        variants.add(parts[0])
    return {v for v in variants if len(v) >= 3}



def _collect_valid_source_anchors(feed_findings: List[Dict]) -> Set[str]:
    anchors: Set[str] = set()
    if not feed_findings:
        return anchors
    for f in feed_findings:
        name = f.get("feed_name", "") or f.get("name", "") or ""
        anchors.update(_source_variants(name))
    return anchors



def _sentence_has_valid_source_anchor(body: str, source_anchors: Set[str]) -> bool:
    lowered = _normalize_source_name(body)
    if not lowered:
        return False

    for anchor in source_anchors:
        if anchor and anchor in lowered:
            return True

    if any(cue in body.lower() for cue in SOURCE_CUES):
        return True

    for verb in ATTRIBUTION_VERBS:
        if re.search(rf'\b[A-Z][A-Za-z0-9&./-]+(?:\s+[A-Z][A-Za-z0-9&./-]+)*\s+{verb}\b', body):
            return True

    return False



def _enforce_rhetorical_discipline(text: str) -> str:
    if not text:
        return text

    sentences = _split_tagged_sentences(text)
    if not sentences:
        return text

    rewritten: List[str] = []
    for sent in sentences:
        tag = _detect_tag(sent)
        if not tag:
            rewritten.append(_clean_prose_spacing(sent))
            continue

        body = _strip_leading_tag(sent)

        if tag == FACT_TAG:
            body = _remove_filler_hedges_from_fact(body)
            interpretive = _fact_sentence_is_interpretive(body)
            plainly_sourced = _fact_sentence_is_plainly_sourced(body)

            if interpretive and plainly_sourced:
                rewritten.append(f"{HYBRID_TAG} {_clean_prose_spacing(body)}")
                continue
            if interpretive:
                rewritten.append(f"{INFERENCE_TAG} {_clean_prose_spacing(body)}")
                continue

            rewritten.append(f"{FACT_TAG} {_clean_prose_spacing(body)}")
            continue

        if tag == HYBRID_TAG:
            body = _clean_prose_spacing(body)
            if _count_matches(body, FACT_INTERPRETIVE_HEDGES) >= 3:
                rewritten.append(f"{INFERENCE_TAG} {body}")
            else:
                rewritten.append(f"{HYBRID_TAG} {body}")
            continue

        rewritten.append(f"{INFERENCE_TAG} {_clean_prose_spacing(body)}")

    return " ".join(rewritten).strip()



def _enforce_fact_traceability(text: str, feed_findings: List[Dict] = None) -> str:
    if not text:
        return text

    source_anchors = _collect_valid_source_anchors(feed_findings or [])
    if not source_anchors:
        return text

    sentences = _split_tagged_sentences(text)
    rewritten: List[str] = []

    for sent in sentences:
        tag = _detect_tag(sent)
        if tag != FACT_TAG:
            rewritten.append(sent.strip())
            continue

        body = _strip_leading_tag(sent)
        has_anchor = _sentence_has_valid_source_anchor(body, source_anchors)
        plainly_sourced = _fact_sentence_is_plainly_sourced(body)

        if has_anchor and plainly_sourced:
            rewritten.append(f"{FACT_TAG} {_clean_prose_spacing(body)}")
        elif has_anchor:
            rewritten.append(f"{HYBRID_TAG} {_clean_prose_spacing(body)}")
        else:
            rewritten.append(f"{INFERENCE_TAG} {_clean_prose_spacing(body)}")

    return " ".join(rewritten).strip()



def _strip_rhetorical_hedges(text: str) -> str:
    """FIX (Item 1 — Rule 4): Strip rhetorical hedging from ALL narration.

    Intelligence prose expresses uncertainty through probability ranges,
    not through weasel words.  This function:
    1. Removes filler hedges from all sentences regardless of tag
    2. Applies grammar-preserving substitutions for structural hedges
    3. Caps hedge density: if 2+ interpretive hedges remain in one
       sentence after stripping, removes all but the first

    Called in _post_process_narration AFTER tag discipline so that
    retagging decisions have already been made.
    """
    if not text:
        return text

    # Phase 1: Strip filler words from entire text
    cleaned = text
    for filler in RHETORICAL_FILLERS:
        cleaned = re.sub(
            rf'\b{re.escape(filler)}\b[,]?\s*',
            '', cleaned, flags=re.IGNORECASE)

    # Phase 2: Apply grammar-preserving substitutions
    for pattern, replacement in HEDGE_SUBSTITUTIONS:
        cleaned = re.sub(
            rf'\b{re.escape(pattern)}\b',
            replacement, cleaned, flags=re.IGNORECASE)

    # Phase 3: Cap hedge density per sentence
    # Split on sentence boundaries (rough — [TAG] markers help)
    sentences = _split_tagged_sentences(cleaned)
    result_parts: List[str] = []
    for sent in sentences:
        tag = _detect_tag(sent)
        body = _strip_leading_tag(sent) if tag else sent

        # Count remaining interpretive hedges
        hedge_count = _count_matches(body, FACT_INTERPRETIVE_HEDGES)
        if hedge_count >= 2:
            # Strip all but the first occurrence
            lowered = body.lower()
            kept_one = False
            for hedge in FACT_INTERPRETIVE_HEDGES:
                if hedge in lowered:
                    if not kept_one:
                        kept_one = True
                        continue  # keep the first
                    # Remove subsequent occurrences
                    body = re.sub(
                        rf'\b{re.escape(hedge)}\b[,]?\s*',
                        '', body, count=1, flags=re.IGNORECASE)

        body = _clean_prose_spacing(body)
        if tag:
            result_parts.append(f"{tag} {body}")
        else:
            result_parts.append(body)

    return " ".join(result_parts).strip()



def _strip_hallucinations(text: str, feed_findings_text: str = "") -> str:
    if not text:
        return text

    feed_text_lower = feed_findings_text.lower() if feed_findings_text else ""
    sentences = _split_tagged_sentences(text)
    cleaned: List[str] = []

    for sent in sentences:
        sent_lower = sent.lower()
        is_fact = sent_lower.startswith(FACT_TAG.lower())

        if is_fact:
            stale_hit = next((stale for stale in STALE_ENTITIES if stale in sent_lower), None)
            if stale_hit:
                cleaned.append(_replace_leading_tag(sent, INFERENCE_TAG))
                continue

            unknown_year_hit = re.search(r'\b(2024|2025)\b', sent_lower)
            if unknown_year_hit and unknown_year_hit.group(1) not in feed_text_lower:
                cleaned.append(_replace_leading_tag(sent, INFERENCE_TAG))
                continue

        cleaned.append(sent)

    return " ".join(cleaned).strip()



def _markdown_to_reportlab(text: str) -> str:
    """Convert lightweight markdown in LLM-generated narratives to the
    inline HTML subset that ReportLab's Paragraph understands.
    """
    if not text:
        return text
    import re as _re

    glyph_map = {
        "\u25A1": "\u25A0",
        "\u2610": "\u25A0",
        "\u2022\uFE0E": "\u2022",
    }
    for bad, good in glyph_map.items():
        text = text.replace(bad, good)

    text = _re.sub(r"-{3,}\s*", "", text)
    text = _re.sub(r"^[ \t]*#{1,6}[ \t]+", "", text, flags=_re.MULTILINE)
    text = _re.sub(r"\*\*([^*\n]+?)\*\*", r"<b>\1</b>", text)
    text = _re.sub(
        r"(?<![\*\w])\*([^*\n]+?)\*(?!\*)",
        r"<i>\1</i>",
        text,
    )

    def _style_tag(m):
        tag = m.group(1).strip()
        return f'<b><font size="7">[{tag.upper()}]</font></b>'
    text = _re.sub(
        r"\[(FACT|INFERENCE|FACT\s*/\s*INFERENCE\s+hybrid)\]",
        _style_tag, text, flags=_re.IGNORECASE,
    )

    return text


def _post_process_narration(text: str, feed_findings: List[Dict] = None) -> str:
    if not text:
        return text
    feed_text = ""
    if feed_findings:
        feed_text = " ".join((f.get("findings", "") or "") for f in feed_findings)
    text = _strip_hallucinations(text, feed_text)
    text = _enforce_rhetorical_discipline(text)
    text = _enforce_fact_traceability(text, feed_findings)
    text = _strip_rhetorical_hedges(text)  # Item 1: Rule 4 enforcement
    text = _markdown_to_reportlab(text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════
# FEED TEXT CLEANING / SOURCE ATTRIBUTION SUPPORT
# ═══════════════════════════════════════════════════════════════════════════

def _clean_feed_text(text: str) -> str:
    if not text:
        return ""

    cleaned = text.strip()
    prefixes = [
        "Based on the search results,", "Based on the latest,", "Based on my search,",
        "Based on recent search,", "Based on Bloomberg,", "Based on Al Jazeera,",
        "Based on NPR,", "Based on CBS,", "Based on NBC,", "Let me search,",
        "Here are the verifiable facts,", "here are the key verifiable facts,",
    ]
    for prefix in prefixes:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
            break

    markers = ["[FACT]", "Trump", "Iran", "IRGC", "IDF", "CENTCOM", "Hormuz", "Hezbollah", "Netanyahu", "Araghchi", "OFAC", "The"]
    for marker in markers:
        idx = cleaned.find(marker)
        if idx > 0:
            cleaned = cleaned[idx:]
            break

    cleaned = cleaned.replace("**", "")
    cleaned = re.sub(r'^#+\s*', '', cleaned)
    return cleaned.strip()



def generate_source_attribution(feed_results: List[Dict]) -> List[Dict]:
    sources = []
    category_map = {
        1: "Government primary source",
        2: "Named journalist, editorial standards",
        3: "State-affiliated corroboration required",
        4: "Aggregator; directional only",
    }
    incentive_map = {
        1: "Official government position; monitor for framing.",
        2: "Commercial news incentive. Monitor for sourcing attribution.",
        3: "State-affiliated editorial alignment. Zero governing weight without Tier 1/2 corroboration per Gate 0.2.",
        4: "Aggregator downstream from Tier 1/2 feeds. Cannot be load-bearing.",
    }
    for fr in feed_results:
        findings = fr.get("findings", "")
        if findings and "NO NEW FINDINGS" not in findings and "API unavailable" not in findings:
            tier = int(fr.get("tier", 0) or 0)
            sources.append({
                "name": fr.get("feed_name", ""),
                "tier": str(tier),
                "category": category_map.get(tier, "Unknown"),
                "body": _clean_feed_text(findings)[:300],
                "incentive": incentive_map.get(tier, ""),
            })
    return sources


# ═══════════════════════════════════════════════════════════════════════════
# NON-CASE SECTIONS
# ═══════════════════════════════════════════════════════════════════════════

def generate_situation_overview(gmt_str: str, war_day: int, edition: int, sweep: str, key_developments: List[str], cases: List[Dict], hypothesis_summary: str) -> str:
    devs = "\n".join(f"- {d}" for d in key_developments[:8])
    case_summary = "\n".join(f"- Case {c.get('case_id', '')}: {c.get('title', '')}" for c in cases)
    prompt = (
        f"Write a Situation Overview for Signalghost Edition {edition:03d} ({sweep}, {gmt_str}, War Day {war_day}).\n\n"
        f"Key developments from today's feed sweep:\n{devs}\n\n"
        f"Active cases:\n{case_summary}\n\n"
        f"Current hypothesis positions:\n{hypothesis_summary}\n\n"
        "Write 200-300 words. Lead with the most significant development. Reference specific actors and dates. Use [FACT] and [INFERENCE] prefixes. Do NOT mention pipeline stages, Bayesian updates, or calibration mechanics."
    )
    return _call_api(prompt)



def generate_pcp_step_1_5(feed_findings: List[Dict], cases: List[Dict]) -> str:
    findings = "\n".join(
        f"- [{f.get('feed_name', '')}]: {f.get('findings', '')[:120]}"
        for f in feed_findings
        if f.get("findings") and "NO NEW FINDINGS" not in f.get("findings", "")
    )[:2000]
    case_list = ", ".join(f"Case {c.get('case_id', '')}: {c.get('title', '')}" for c in cases)
    prompt = (
        "Write a PCP Step 1.5 — New Signal Check.\n\n"
        f"Active cases: {case_list}\n\n"
        f"New signals:\n{findings}\n\n"
        "For each significant new signal, assess: (1) Is the actor from an active case or new? (2) Independent distribution from existing hypotheses? (3) Disconfirmation expressible within existing cases? Write 100-150 words. Conclude with 'No new case opened' or flag new case. Reference specific actors and events."
    )
    return _call_api(prompt)



def generate_h1_saturation_check(heuristic_summary: str, cases: List[Dict]) -> str:
    case_list = "\n".join(f"- Case {c.get('case_id', '')}: {c.get('title', '')}" for c in cases)
    prompt = (
        "Write an H1 Saturation Check (80-120 words).\n\n"
        f"Current heuristic dominance:\n{heuristic_summary}\n\n"
        f"Cases:\n{case_list}\n\n"
        "Question: Is H1 (Incentive Mismatch) being over-applied or is it correctly subordinate to H4/H5/H6 where those have stronger explanatory power? End with 'Calibration audit: PASS' or identify concern."
    )
    return _call_api(prompt, max_tokens=1024)



def generate_executive_summary(edition: int, sweep: str, war_day: int, brier_score: float, key_developments: List[str]) -> str:
    devs = "; ".join(str(d)[:80] for d in key_developments[:5])
    prompt = (
        f"Write a 100-word executive summary for Signalghost Edition {edition:03d} ({sweep}, War Day {war_day}). Key developments: {devs}. Brier accuracy score: {brier_score:.4f}. Lead with the single most important development. Use [FACT] prefixes. No pipeline jargon."
    )
    return _call_api(prompt, max_tokens=1024)



def generate_critical_windows(predictions_open: List[Dict], edition: int, current_date: str) -> str:
    pred_text = "\n".join(
        f"- {p.get('pred_ref', p.get('predref', ''))}: {p.get('flag', '')[:60]} Window {p.get('window', '')}, Status {p.get('status', '')}"
        for p in predictions_open[:10]
    )
    prompt = (
        f"Write Critical Windows for Edition {edition:03d}.\n\n"
        f"Current date: {current_date}\n\n"
        f"Predictions:\n{pred_text}\n\n"
        "For each critical window, state: (1) What the window is; (2) Current status; (3) Next edition mandatory action. Write 150-200 words. Prioritise by urgency. Reference specific dates and actors. No pipeline jargon."
    )
    return _call_api(prompt)



def generate_domain_quality_assessment(case_id: str, case_title: str, feed_count: int, tier1_count: int, tier2_count: int, tier3_count: int) -> str:
    prompt = (
        f"Write a one-paragraph domain quality assessment 40-60 words for Case {case_id}: {case_title}. Sources: {feed_count} total. Tier 1: {tier1_count}, Tier 2: {tier2_count}, Tier 3: {tier3_count}. Assess source diversity, independence, Gate 0.2 compliance, cluster risk. End with 'Overall assessment: HIGH/MEDIUM/LOW confidence in source base.'"
    )
    return _call_api(prompt, max_tokens=512)


# ═══════════════════════════════════════════════════════════════════════════
# PER-CASE CDIT — 6 PARTS
# ═══════════════════════════════════════════════════════════════════════════

def generate_case_part1_facts(case_id: str, case_title: str, feed_findings: List[Dict], carry_forward_facts: List[Dict]) -> str:
    findings = "\n".join(
        f"- [{f.get('feed_name', '')} Tier {f.get('tier', 0)}]: {f.get('findings', '')[:200]}"
        for f in feed_findings
        if f.get("findings") and "NO NEW FINDINGS" not in f.get("findings", "")
    )[:3000]
    carry = "\n".join(f"- {cf.get('fact', '')[:120]}" for cf in carry_forward_facts[:6])
    prompt = (
        f"Write the analytical narrative for Part 1 — Fact Table, Case {case_id}: {case_title}.\n\n"
        f"Feed findings:\n{findings}\n\n"
        f"Carry-forward facts:\n{carry}\n\n"
        "Write 200-350 words. For each key fact: start with [FACT]; name the specific source and tier; include a Gate 0.4 confidence assessment (HIGH/MEDIUM-HIGH/MEDIUM); reference specific actors, dates, and locations. Do NOT write about pipeline stages or API errors. Do NOT include phrases like 'based on the search results'. Write as if briefing a senior official."
    )
    return _call_api(prompt)



def generate_case_part2_incongruity(case_id: str, case_title: str, hypotheses_named: List[Dict], heuristics_applied: str, disconf_thresholds: List[Dict] = None, pmm_lessons: List[Dict] = None) -> str:
    hyp_text = "\n".join(
        f"- {h.get('hyp_id', '')}: {h.get('name', '')}: {h.get('range', '')} (pt={h.get('point_estimate', 0):.2f})"
        for h in hypotheses_named
    )
    disconf_context = ""
    if disconf_thresholds:
        relevant = [d for d in disconf_thresholds if d.get("case_id") == case_id]
        if relevant:
            disconf_context = "\nDisconfirmation thresholds for this case:\n" + "\n".join(
                f"- {d.get('threshold', '')[:100]}" for d in relevant[:4]
            )
    pmm_context = ""
    if pmm_lessons:
        pmm_context = "\nPast prediction failures (PMM lessons) — avoid repeating:\n" + "\n".join(
            f"- {p.get('entry_id', '')}: {p.get('outcome', '')[:80]} — {p.get('what_failed', '')[:80]}"
            for p in pmm_lessons[:4]
        )
    prompt = (
        f"Write Part 2 — Incongruity Analysis for Case {case_id}: {case_title}.\n\n"
        f"Hypotheses:\n{hyp_text}\n\n"
        f"Heuristic context: {heuristics_applied}\n"
        f"{disconf_context}\n{pmm_context}\n\n"
        "Write 200-300 words. Apply H1-H7 where relevant. "
        "BILATERAL H1 MANDATE: For ANY hypothesis above 60%, you MUST address BOTH "
        "(a) the stated incentive or declared intent of the named actor, AND "
        "(b) the counter-incentive, alternative explanation, or reason the stated intent "
        "may not translate to action. Use phrases like 'however', 'against this', "
        "'the counter-argument is', 'working against this' to mark the opposing side. "
        "One-sided incentive analysis is not sufficient for hypotheses above 60%. "
        "If disconfirmation thresholds are close to triggering, discuss which ones. If PMM lessons apply, address them. Use [INFERENCE] and [FACT / INFERENCE hybrid] prefixes. End with: 'Dominant heuristic: [name]. [secondary]. [tertiary].' Reference specific actors and events, not abstract concepts. Do NOT mention pipeline stages, S2, S3, S7, buffer variance, etc."
    )
    return _call_api(prompt)



def generate_case_part3_hypotheses(case_id: str, hypotheses_named: List[Dict], carry_forward_facts: List[Dict] = None) -> str:
    hyp_text = "\n".join(
        f"- {h.get('hyp_id', '')}: \"{h.get('name', '')}\": {h.get('range', '')} (pt={h.get('point_estimate', 0):.2f}, status={h.get('status', '')}). Correction basis: {h.get('correction_basis', 'No material change.')}"
        for h in hypotheses_named
    )
    facts_context = ""
    if carry_forward_facts:
        facts_context = "\nCarry-forward facts:\n" + "\n".join(
            f"- {cf.get('fact', '')[:150]}" for cf in carry_forward_facts[:8]
        )
    prompt = (
        f"Write Part 3 — Hypothesis Set for Case {case_id}.\n\n"
        f"Hypotheses with their computed ranges:\n{hyp_text}\n"
        f"{facts_context}\n\n"
        "For each hypothesis, write 50-80 words explaining: what specific evidence supports this probability; what suppresses it; and what would change it significantly (reference disconfirmation triggers). Use the EXACT names, ranges, and point estimates provided. Ground explanations in the carry-forward facts above. Reference specific events. Do NOT rename the hypotheses. Do NOT mention pipeline stages."
    )
    return _call_api(prompt)



def generate_case_part4_tql(case_id: str, case_title: str, hypotheses_named: List[Dict]) -> str:
    hyp_text = "\n".join(
        f"- {h.get('hyp_id', '')}: {h.get('name', '')}: {h.get('range', '')} (pt={h.get('point_estimate', 0):.2f})"
        for h in hypotheses_named
    )
    prompt = (
        f"Write Part 4 — Truth Quality Check (TQL) for Case {case_id}: {case_title}.\n\n"
        f"Hypotheses:\n{hyp_text}\n\n"
        "Write exactly 4 items, each 40-60 words: Item 1 Key Assumption; Item 2 Fragile Fact; Item 3 High-Impact Uncertainty; Item 4 Tier 4 Dependency Test. Reference specific actors and events. No pipeline jargon."
    )
    return _call_api(prompt)



def generate_case_part5_disconfirmation(case_id: str, disconf_thresholds: List[Dict]) -> str:
    thresholds = "\n".join(
        f"- {d.get('threshold', '')[:100]} — {d.get('effect', '')[:100]}"
        for d in disconf_thresholds if d.get("case_id") == case_id
    )
    prompt = (
        f"Write a brief analytical comment (80-120 words) on the disconfirmation landscape for Case {case_id}.\n\n"
        f"Standing thresholds:\n{thresholds}\n\n"
        "Which threshold is closest to being triggered? Which would have the largest impact? Reference specific actors and events. No pipeline jargon."
    )
    return _call_api(prompt, max_tokens=1024)



def generate_case_part6_forward_flag(case_id: str, predictions_open: List[Dict], edition: int) -> str:
    relevant = [
        p for p in predictions_open
        if case_id.lower() in str(p.get('pred_ref', p.get('predref', ''))).lower() or case_id.lower() in str(p.get('flag', '')).lower()
    ]
    pred_text = "\n".join(
        f"- {p.get('pred_ref', p.get('predref', ''))}: {p.get('flag', '')[:80]} Window {p.get('window', '')}, Status {p.get('status', '')}"
        for p in relevant
    )
    prompt = (
        f"Write a brief monitoring note (60-100 words) for Case {case_id} forward flags, Edition {edition:03d}.\n\n"
        f"Open predictions:\n{pred_text}\n\n"
        "What should the next edition prioritise monitoring? Reference specific actors and deadlines. No pipeline jargon."
    )
    return _call_api(prompt, max_tokens=1024)



def generate_full_case_narrative(case_id: str, case_title: str, case_tag: str, case_confidence: str, hypotheses: List[Dict], feed_findings: List[Dict], carry_forward_facts: List[Dict], heuristics_applied: str, pipeline_log: List[str], disconf_thresholds: List[Dict], predictions_open: List[Dict], edition: int, pmm_lessons: List[Dict] = None) -> Dict[str, str]:
    return {
        "part1_facts": _post_process_narration(generate_case_part1_facts(case_id, case_title, feed_findings, carry_forward_facts), feed_findings),
        "part2_incongruity": _post_process_narration(generate_case_part2_incongruity(case_id, case_title, hypotheses, heuristics_applied, disconf_thresholds=disconf_thresholds, pmm_lessons=pmm_lessons), feed_findings),
        "part3_hypotheses": _post_process_narration(generate_case_part3_hypotheses(case_id, hypotheses, carry_forward_facts=carry_forward_facts), feed_findings),
        "part4_tql": _post_process_narration(generate_case_part4_tql(case_id, case_title, hypotheses), feed_findings),
        "part5_disconfirmation": _post_process_narration(generate_case_part5_disconfirmation(case_id, disconf_thresholds), feed_findings),
        "part6_forward_flag": _post_process_narration(generate_case_part6_forward_flag(case_id, predictions_open, edition), feed_findings),
    }
