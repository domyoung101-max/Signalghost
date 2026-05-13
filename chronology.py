"""chronology.py — Signalghost chronology verification.

CHRONOLOGY VERIFICATION RULE — MANDATORY:
  - War start date: 28 February 2026 = War Day 1.  Verified.  Do not assume.
  - War day calculated arithmetically and verified online at every session open.
  - Formula: War Day = (current date - 28 February 2026) + 1
  - Online verification governs.  SESSION_STATE value overridden if contradicted online.

This module enforces:
  1.  Arithmetic war-day calculation
  2.  Cross-check against prior SESSION_STATE value
  3.  PLM entry generation on mismatch
  4.  Edition chronology ordering (no edition may be out of sequence)
"""

import datetime
from typing import Dict, Optional, List
from config import WAR_START_YEAR, WAR_START_MONTH, WAR_START_DAY


def compute_war_day(date: datetime.date) -> int:
    """Compute war day from a given date.

    Formula: War Day = (date − 28 February 2026) + 1
    """
    war_start = datetime.date(WAR_START_YEAR, WAR_START_MONTH, WAR_START_DAY)
    return (date - war_start).days + 1


def verify_war_day(ts: Dict, session_state_war_day: Optional[int] = None) -> Dict:
    """Verify war day arithmetic and cross-check with SESSION_STATE.

    Returns dict with:
      computed_war_day   : int
      session_state_day  : int or None
      match              : bool
      plm_required       : bool
      plm_message        : str (if mismatch)
    """
    computed = compute_war_day(ts["gmt_now"].date())
    result = {
        "computed_war_day": computed,
        "session_state_day": session_state_war_day,
        "match": True,
        "plm_required": False,
        "plm_message": "",
    }

    if session_state_war_day is not None and computed != session_state_war_day:
        result["match"] = False
        result["plm_required"] = True
        result["plm_message"] = (
            f"War Day mismatch: SESSION_STATE carried {session_state_war_day} "
            f"but arithmetic yields {computed} for {ts['gmt_now'].date()}. "
            f"Online verification governs.  SESSION_STATE value overridden."
        )

    return result


def verify_edition_chronology(
    current_edition: int,
    prior_editions: List[Dict],
) -> Dict:
    """Verify that edition numbering is strictly sequential.

    Returns dict with:
      valid           : bool
      expected_edition: int
      plm_required    : bool
      plm_message     : str (if invalid)
    """
    if not prior_editions:
        expected = 1
    else:
        max_prior = max(e["edition_number"] for e in prior_editions)
        expected = max_prior + 1

    result = {
        "valid": current_edition == expected,
        "expected_edition": expected,
        "plm_required": current_edition != expected,
        "plm_message": "",
    }

    if not result["valid"]:
        result["plm_message"] = (
            f"Edition chronology error: expected {expected}, got {current_edition}."
        )

    return result


def compute_staleness_days(
    fact_date: datetime.date,
    current_date: datetime.date,
) -> int:
    """Compute staleness in days for a carry-forward fact."""
    return (current_date - fact_date).days


def check_temporal_currency(
    fact_verified_date: datetime.date,
    current_date: datetime.date,
    max_staleness_days: int = 3,
) -> Dict:
    """Gate 0.1 — Temporal Currency Check.

    Before any carry-forward fact is cited as governing, it must be within
    temporal currency window for its claim type.

    Returns:
      current  : bool
      staleness: int (days)
    """
    staleness = compute_staleness_days(fact_verified_date, current_date)
    return {
        "current": staleness <= max_staleness_days,
        "staleness": staleness,
    }
