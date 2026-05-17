"""predictions.py — Signalghost prediction tracking and scoring.

Implements:
  - Brier Score: BS = (1/n) x sum(fi - oi)^2
  - Log Score:   LS = (1/n) x sum(ln(pi))
  - Spherical Score: SS = (1/n) x sum(pi / sqrt(sum(fi^2)))
  - Prediction resolution via Gate 5
  - Running score tables
  - PMM-004 mandatory rule check
"""

import math
from typing import List, Dict, Optional, Tuple
from config import (
    BS_TARGET_OPERATIONAL, BS_TARGET_SUSTAINED, BS_TARGET_ELITE, BSS_REFERENCE,
    LS_BASELINE, SS_BASELINE,
    PMM_004_ADJUSTMENT_PP,
    PredictionOutcome, OUTCOME_VALUES,
)
from persistence import (
    get_all_brier_rows, insert_row, fetch_all,
)


def compute_brier_score(rows: List[Dict]) -> Tuple[float, int]:
    """Compute Brier score from list of brier_table rows.

    BS = (1/n) x sum(fi - oi)^2.  Lower is better.
    """
    if not rows:
        return 0.0, 0
    total = sum(r["squared_error"] for r in rows)
    n = len(rows)
    return total / n, n


def compute_log_score(rows: List[Dict]) -> Tuple[float, int]:
    """Compute Log Score from resolved predictions.

    LS = (1/n) x sum(ln(pi))
    where pi = probability assigned to the outcome that occurred.
    CONFIRMED: pi = fi.  CONTRADICTED: pi = 1 - fi.  PARTIAL: pi = 0.5.
    """
    if not rows:
        return 0.0, 0

    total = 0.0
    n = 0
    for r in rows:
        fi = r.get("fi")
        oi = r.get("oi")
        if fi is None or oi is None:
            continue
        if oi == 1.0:
            pi = max(fi, 1e-10)
        elif oi == 0.0:
            pi = max(1.0 - fi, 1e-10)
        else:
            pi = 0.5
        total += math.log(pi)
        n += 1

    return (total / n if n > 0 else 0.0), n


def compute_spherical_score(rows: List[Dict]) -> Tuple[float, int]:
    """Compute Spherical Score.

    SS = (1/n) x sum(pi / sqrt(fi^2 + (1-fi)^2))
    """
    if not rows:
        return 0.0, 0

    total = 0.0
    n = 0
    for r in rows:
        fi = r.get("fi")
        oi = r.get("oi")
        if fi is None or oi is None:
            continue
        if oi == 1.0:
            pi = fi
        elif oi == 0.0:
            pi = 1.0 - fi
        else:
            pi = 0.5
        denom = math.sqrt(fi**2 + (1.0 - fi)**2)
        if denom > 0:
            total += pi / denom
        n += 1

    return (total / n if n > 0 else 0.0), n


def compute_all_scores() -> Dict:
    """Compute all three scoring metrics from the brier_table."""
    rows = get_all_brier_rows()
    bs, bs_n = compute_brier_score(rows)
    ls, ls_n = compute_log_score(rows)
    ss, ss_n = compute_spherical_score(rows)

    bss = 1 - (bs / BSS_REFERENCE) if bs_n > 0 else 0.0

    return {
        "brier_score": round(bs, 4),
        "brier_n": bs_n,
        "brier_status": _bs_status(bs),
        "brier_skill_score": round(bss, 4),
        "brier_skill_prose": _bss_prose(bss, bs_n),
        "log_score": round(ls, 4),
        "log_n": ls_n,
        "spherical_score": round(ss, 4),
        "spherical_n": ss_n,
    }


def _bs_status(bs: float) -> str:
    if bs < BS_TARGET_ELITE:
        return "ELITE"
    elif bs < BS_TARGET_SUSTAINED:
        return "SUSTAINED"
    elif bs < BS_TARGET_OPERATIONAL:
        return "OPERATIONAL"
    else:
        return "DEGRADED"
    
def _bss_prose(bss: float, n: int) -> str:
    """Generate concise prose interpretation of Brier Skill Score."""
    if n < 1:
        return "No resolved predictions. BSS pending."
    if n < 5:
        qualifier = "Early-stage assessment"
    elif n < 15:
        qualifier = "Developing track record"
    else:
        qualifier = "Established baseline"
    if bss >= 0.6:
        return f"{qualifier}: substantial skill over coin-flip ({bss:.1%} improvement). System delivers strong predictive value."
    elif bss >= 0.3:
        return f"{qualifier}: moderate skill over coin-flip ({bss:.1%} improvement). Forecasts outperform guessing but calibration gaps remain."
    elif bss >= 0.0:
        return f"{qualifier}: marginal skill over coin-flip ({bss:.1%} improvement). System performs above baseline but within noise range at low n."
    else:
        return f"{qualifier}: negative skill ({bss:.1%}). System currently underperforms coin-flip baseline. Calibration review required."

def resolve_prediction(
    pred_ref: str,
    outcome: str,
    fi: float,
    oi: float,
    edition: int,
    notes: str = "",
) -> Dict:
    """Resolve a prediction and add to Brier table.

    Writes to three tables atomically:
      1. predictions_open  — UPDATE status to RESOLVED
      2. predictions_resolved — INSERT resolution record
      3. brier_table — INSERT scoring entry

    All three writes are wrapped in a single transaction. If any
    write fails, the entire transaction rolls back and an exception
    propagates to the caller. No partial state is possible.

    Returns the Brier contribution dict.
    """
    # ── Input validation ──
    valid_outcomes = ("CONFIRMED", "CONTRADICTED", "PARTIAL", "AMBIGUOUS")
    if outcome not in valid_outcomes:
        raise ValueError(
            f"resolve_prediction: invalid outcome '{outcome}' for {pred_ref}. "
            f"Must be one of {valid_outcomes}."
        )
    if fi is None or not isinstance(fi, (int, float)):
        raise ValueError(
            f"resolve_prediction: fi must be a number, got {fi!r} for {pred_ref}."
        )
    if oi is None or not isinstance(oi, (int, float)):
        raise ValueError(
            f"resolve_prediction: oi must be a number, got {oi!r} for {pred_ref}."
        )

    squared_error = (fi - oi) ** 2

    from persistence import get_connection
    conn = get_connection()
    try:
        # Write 1: UPDATE predictions_open → mark resolved
        cursor = conn.execute("""UPDATE predictions_open SET
            outcome = ?, fi = ?, oi = ?, brier_contribution = ?,
            resolution_edition = ?, status = ?
            WHERE pred_ref = ?""",
            (outcome, fi, oi, squared_error, edition,
             f"RESOLVED Ed{edition:03d}", pred_ref))
        if cursor.rowcount == 0:
            raise RuntimeError(
                f"resolve_prediction: UPDATE predictions_open matched 0 rows "
                f"for pred_ref='{pred_ref}'. Prediction may not exist in DB."
            )

        # Write 2: INSERT into resolved log
        conn.execute("""INSERT OR REPLACE INTO predictions_resolved
            (pred_ref, outcome, notes, fi, oi, brier_contribution, resolution_edition)
            VALUES (?,?,?,?,?,?,?)""",
            (pred_ref, outcome, notes, fi, oi, squared_error, edition))

        # Write 3: INSERT into Brier table
        conn.execute("""INSERT INTO brier_table
            (pred_ref, fi, oi, squared_error, edition, notes)
            VALUES (?,?,?,?,?,?)""",
            (pred_ref, fi, oi, squared_error, edition, notes))

        conn.commit()
        print(f"    → PERSISTED: {pred_ref} {outcome} fi={fi:.4f} oi={oi:.1f} "
              f"BS_contribution={squared_error:.4f} (3/3 writes OK)")

    except Exception as e:
        conn.rollback()
        print(f"    → PERSISTENCE FAILURE for {pred_ref}: {e}")
        print(f"    → Transaction rolled back. No partial state written.")
        raise
    finally:
        conn.close()

    return {
        "pred_ref": pred_ref,
        "outcome": outcome,
        "fi": fi,
        "oi": oi,
        "squared_error": round(squared_error, 4),
    }


def check_pmm_004(
    hyp_id: str,
    point_estimate: float,
    h4_gap_active: bool,
    tier1_denial_active: bool,
    no_observable_prep_action: bool,
    prior_point_estimate: float,
) -> Tuple[float, bool, str]:
    """PMM-004 Mandatory Rule Check.

    When H4 gap is active (Tier 1 US assertion vs Tier 1 Iranian denial)
    AND no observable Iranian-side preparatory action AND hypothesis above 60%:
    mandatory -10pp minimum downward adjustment from prior.
    Cannot be bypassed.

    Returns: (adjusted_estimate, was_applied, log_message)
    """
    if h4_gap_active and tier1_denial_active and no_observable_prep_action:
        if point_estimate > 0.60:
            adjusted = prior_point_estimate + PMM_004_ADJUSTMENT_PP
            adjusted = max(0.0, min(1.0, adjusted))
            if adjusted < point_estimate:
                return adjusted, True, (
                    f"PMM-004 APPLIED to {hyp_id}: H4 gap active + Tier 1 denial + "
                    f"no prep action → mandatory {PMM_004_ADJUSTMENT_PP:+.0%} from "
                    f"prior {prior_point_estimate:.2f} = {adjusted:.2f}"
                )
            else:
                return point_estimate, False, (
                    f"PMM-004 checked for {hyp_id}: conditions met but "
                    f"current estimate already below adjusted. No further reduction."
                )
    return point_estimate, False, f"PMM-004 checked for {hyp_id}: conditions not met."


def get_band_for_prediction(fi: float) -> str:
    """Map a forecast probability to its lookup band."""
    bands = [
        (0.00, 0.10, "0-10%"),
        (0.10, 0.20, "10-20%"),
        (0.20, 0.30, "20-30%"),
        (0.30, 0.40, "30-40%"),
        (0.40, 0.60, "40-60%"),
        (0.60, 0.70, "60-70%"),
        (0.70, 0.80, "70-80%"),
        (0.80, 0.90, "80-90%"),
        (0.90, 1.00, "90-100%"),
    ]
    for lo, hi, label in bands:
        if lo <= fi < hi:
            return label
    if fi >= 0.90:
        return "90-100%"
    return "40-60%"


# ═══════════════════════════════════════════════════════════════════════════
# ITEM 10: FIVE-CRITERIA PREDICTION STANDARD (Section 7)
# ═══════════════════════════════════════════════════════════════════════════

def validate_prediction_criteria(pred: Dict) -> Tuple[bool, List[str]]:
    """FIX (Item 10): Validate that a prediction meets all 6 mandatory criteria.

    Section 7 Six-Criteria Prediction Standard:
      1. Specific outcome stated (flag field)
      2. Time window defined (window field)
      3. Disconfirmation threshold stated (disconfirmation field)
      4. Forecast probability assigned (fi field)
      5. Named evidence basis (flag or notes references a source)
      6. Resolution Protocol — mechanically resolvable YES/NO triggers
         with named verification source. No analyst interpretation permitted.

    Returns: (all_valid, list_of_failures)
    """
    failures = []
    pred_ref = pred.get("pred_ref", "UNKNOWN")

    # Criterion 1: Specific outcome stated
    flag = (pred.get("flag", "") or "").strip()
    if not flag or len(flag) < 10:
        failures.append(f"{pred_ref}: Criterion 1 FAIL — no specific outcome stated (flag empty or too short)")

    # Criterion 2: Time window defined
    window = (pred.get("window", "") or "").strip()
    if not window:
        failures.append(f"{pred_ref}: Criterion 2 FAIL — no time window defined")

    # Criterion 3: Disconfirmation threshold stated
    disconf = (pred.get("disconfirmation", "") or "").strip()
    if not disconf or len(disconf) < 10:
        failures.append(f"{pred_ref}: Criterion 3 FAIL — no disconfirmation threshold stated")

    # Criterion 4: Forecast probability assigned
    fi = pred.get("fi")
    if fi is None:
        failures.append(f"{pred_ref}: Criterion 4 FAIL — no forecast probability (fi) assigned")
    elif not (0.0 <= float(fi) <= 1.0):
        failures.append(f"{pred_ref}: Criterion 4 FAIL — fi={fi} out of range [0,1]")

    # Criterion 5: Named evidence basis
    evidence_text = (flag + " " + (pred.get("notes", "") or "")).lower()
    has_named_entity = any(
        term in evidence_text for term in [
            "iran", "trump", "idf", "hezbollah", "centcom", "irgc",
            "netanyahu", "araghchi", "hormuz", "ofac", "yanbu",
            "ceasefire", "talks", "strike", "blockade", "sanctions",
        ]
    )
    if not has_named_entity:
        failures.append(f"{pred_ref}: Criterion 5 FAIL — no named evidence basis in flag or notes")

    # Criterion 6: Resolution Protocol — mechanical YES/NO triggers
    # Every prediction must define observable triggers that can be resolved
    # by checking named sources without analyst interpretation.
    # Required fields: resolution_yes, resolution_no, resolution_source
    res_yes = (pred.get("resolution_yes", "") or "").strip()
    res_no = (pred.get("resolution_no", "") or "").strip()
    res_source = (pred.get("resolution_source", "") or "").strip()

    if not res_yes:
        failures.append(
            f"{pred_ref}: Criterion 6 FAIL — no resolution_yes trigger defined. "
            f"Prediction must specify observable condition(s) that resolve YES "
            f"(e.g. 'Formal government statement extending ceasefire past 14 May "
            f"AND no 100+ rocket barrage in single 24-hour period')."
        )
    elif len(res_yes) < 20:
        failures.append(
            f"{pred_ref}: Criterion 6 FAIL — resolution_yes too vague ({len(res_yes)} chars). "
            f"Must be specific enough for mechanical verification."
        )

    if not res_no:
        failures.append(
            f"{pred_ref}: Criterion 6 FAIL — no resolution_no trigger defined. "
            f"Prediction must specify observable condition(s) that resolve NO "
            f"(e.g. 'Either government formally withdraws OR 100+ rockets in "
            f"24 hours OR IDF crosses Litani in brigade strength')."
        )
    elif len(res_no) < 20:
        failures.append(
            f"{pred_ref}: Criterion 6 FAIL — resolution_no too vague ({len(res_no)} chars). "
            f"Must be specific enough for mechanical verification."
        )

    if not res_source:
        failures.append(
            f"{pred_ref}: Criterion 6 FAIL — no resolution_source defined. "
            f"Must name the verification source(s) used to check triggers "
            f"(e.g. 'IDF official statements, Lebanese government, UNIFIL')."
        )

    return len(failures) == 0, failures


def validate_all_open_predictions() -> Tuple[int, int, List[str]]:
    """Validate all open predictions against the five-criteria standard.

    Returns: (total, failed_count, all_failures)
    """
    from persistence import get_open_predictions
    preds = get_open_predictions()
    all_failures = []
    failed = 0
    for pred in preds:
        valid, failures = validate_prediction_criteria(pred)
        if not valid:
            failed += 1
            all_failures.extend(failures)
    return len(preds), failed, all_failures


# ═══════════════════════════════════════════════════════════════════════════
# ITEM 11: PMM-001 NAMED-SOURCE AUTO-TRIGGER
# ═══════════════════════════════════════════════════════════════════════════

# Named actors — if a prediction references one of these, H1 analysis is required
_NAMED_ACTORS = {
    "trump", "araghchi", "netanyahu", "khamenei", "salami", "ghalibaf",
    "pezeshkian", "sharif", "rubio", "wang yi", "biden",
    "irgc", "centcom", "idf", "hezbollah", "hamas",
}


def check_pmm_001_named_source(pred: Dict, h1_completed: bool) -> Optional[str]:
    """FIX (Item 11): PMM-001 auto-trigger.

    If a prediction names an actor (from _NAMED_ACTORS) without H1
    incentive analysis having been completed, return a warning message
    for PLM logging.

    Returns: warning message string, or None if no issue.
    """
    flag = (pred.get("flag", "") or "").lower()
    pred_ref = pred.get("pred_ref", "UNKNOWN")

    named_actors_found = [actor for actor in _NAMED_ACTORS if actor in flag]

    if named_actors_found and not h1_completed:
        actors_str = ", ".join(named_actors_found[:3])
        return (
            f"PMM-001 AUTO-TRIGGER: {pred_ref} names actor(s) [{actors_str}] "
            f"but H1 incentive analysis not completed. "
            f"Architecture Section 7: named-party predictions require "
            f"incentive analysis before publication."
        )
    return None


# ═══════════════════════════════════════════════════════════════════════════
# CF-1: DYNAMIC fi LINKAGE
# ═══════════════════════════════════════════════════════════════════════════

def update_prediction_fi(hypotheses_map: Dict[str, float]) -> List[str]:
    """CF-1: Update fi for all open predictions based on their tracked hypothesis.

    When the calibration pipeline moves a hypothesis's point_estimate,
    the linked prediction's fi must update to reflect the system's current
    forecast. At resolution time, the stored fi is then the live estimate —
    not a stale value from creation.

    Args:
        hypotheses_map: dict mapping hyp_id -> current point_estimate
            e.g. {"H-C3": 0.69, "H-A1": 0.28, ...}

    Returns:
        List of log messages describing updates made.
    """
    from persistence import get_open_predictions, get_connection

    preds = get_open_predictions()
    log = []

    conn = get_connection()
    for pred in preds:
        pred_ref = pred.get("pred_ref", "")
        tracked = (pred.get("tracked_hyp", "") or "").strip()

        if not tracked:
            log.append(f"{pred_ref}: no tracked_hyp set — fi unchanged.")
            continue

        if tracked not in hypotheses_map:
            log.append(f"{pred_ref}: tracked_hyp '{tracked}' not found in current hypotheses — fi unchanged.")
            continue

        new_pt = hypotheses_map[tracked]
        old_fi = pred.get("fi")
        old_fi_str = f"{old_fi:.4f}" if old_fi is not None else "None"

        # Update fi to match tracked hypothesis point_estimate
        conn.execute(
            "UPDATE predictions_open SET fi = ? WHERE pred_ref = ?",
            (round(new_pt, 4), pred_ref),
        )
        log.append(
            f"{pred_ref}: fi updated {old_fi_str} → {new_pt:.4f} "
            f"(tracking {tracked})."
        )

    conn.commit()
    conn.close()
    return log
