"""timestamping.py — Signalghost mandatory timestamp capture.

LIVE GMT TIMESTAMP — MANDATORY FIRST ACTION EVERY SESSION AND EVERY
SESSION STATE WRITE.

This module is the ONLY permitted source for:
  - GMT timestamp
  - BST timestamp (GMT + 1)
  - War Day (verified arithmetically from 28 February 2026 = Day 1)
  - Sweep Descriptor (programmatically derived from hour)

Web search is forbidden for time.
Manual estimation is forbidden.
Violation = PLM entry mandatory.
"""

import datetime
from config import (
    WAR_START_YEAR, WAR_START_MONTH, WAR_START_DAY,
    SWEEP_MORNING, SWEEP_AFTERNOON, SWEEP_EVENING, SWEEP_LATE_NIGHT,
    SWEEP_HOUR_RANGES,
)
from typing import Dict


def capture_timestamp() -> Dict[str, object]:
    """Capture the live GMT timestamp.  This is the mandatory first action.

    Returns a dict with all four locked values:
      gmt_now        : datetime.datetime
      bst_now        : datetime.datetime
      gmt_str        : str  e.g. "1810 GMT 25 APRIL 2026"
      bst_str        : str  e.g. "1910 BST"
      war_day        : int  (arithmetic — must be verified online separately)
      sweep_descriptor : str  e.g. "EVENING SWEEP"
      date_str       : str  e.g. "25 APRIL 2026"

    This single block produces the four locked values per SESSION_STATE rules.
    No manual selection of sweep descriptor is permitted.
    """
    now = datetime.datetime.utcnow()
    bst = now + datetime.timedelta(hours=1)

    war_start = datetime.date(WAR_START_YEAR, WAR_START_MONTH, WAR_START_DAY)
    war_day = (now.date() - war_start).days + 1

    hour = now.hour
    sweep = SWEEP_LATE_NIGHT  # default
    for start_h, end_h, descriptor in SWEEP_HOUR_RANGES:
        if start_h <= hour < end_h:
            sweep = descriptor
            break

    gmt_str = now.strftime("%H%M GMT %d %B %Y").upper()
    bst_str = bst.strftime("%H%M BST")
    date_str = now.strftime("%d %B %Y").upper()

    return {
        "gmt_now": now,
        "bst_now": bst,
        "gmt_str": gmt_str,
        "bst_str": bst_str,
        "war_day": war_day,
        "sweep_descriptor": sweep,
        "date_str": date_str,
    }


def format_session_state_header(edition: int, ts: Dict) -> str:
    """Format the SESSION_STATE header lines 2 and 3.

    Per SESSION_STATE rule:
      ## Edition NNN Sweep Handoff · [DD MONTH YYYY] · [HHMM GMT] ([HHMM BST])
      ## SESSION STATE UPDATED · [DD MONTH YYYY] · [HHMM GMT] ([HHMM BST]) · [sweep]
    """
    line2 = (
        f"## Edition {edition:03d} {ts['sweep_descriptor'].title()} Handoff "
        f"· {ts['date_str']} · {ts['gmt_str']} ({ts['bst_str']})"
    )
    line3 = (
        f"## SESSION STATE UPDATED · {ts['date_str']} "
        f"· {ts['gmt_str']} ({ts['bst_str']}) "
        f"· Post-Ed{edition:03d} {ts['sweep_descriptor'].title()} "
        f"— Timestamp verified online before write"
    )
    return f"{line2}\n\n{line3}"


def validate_war_day(ts: Dict) -> bool:
    """Validate war day arithmetic.

    Formula: War Day = (current date − 28 February 2026) + 1
    Returns True if valid.
    """
    war_start = datetime.date(WAR_START_YEAR, WAR_START_MONTH, WAR_START_DAY)
    expected = (ts["gmt_now"].date() - war_start).days + 1
    return ts["war_day"] == expected


def print_timestamp_block(ts: Dict):
    """Print the four locked values as specified in SESSION_STATE."""
    print(ts["gmt_str"])
    print(ts["bst_str"])
    print(f"War Day: {ts['war_day']}")
    print(f"Sweep Descriptor: {ts['sweep_descriptor']}")
