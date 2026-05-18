"""calibration_pipeline.py — Signalghost 13-stage calibration pipeline.

CALIBRATION PIPELINE — EXECUTION ORDER (v1.3.0)

Every probability assignment passes through this pipeline in order before
publication.  No stage may be skipped silently.

Stage 1:  AI-010    Single-cluster H5 discount
Stage 2:  AI-009    Bayesian update (LR table applied to prior)
Stage 3:  AI-012-1  Causal edge smoothing (0.7 x old + 0.3 x new)
Stage 4:  AI-012-2  Delta statistics update
Stage 5:  AI-012-3  Change point detection (|z| > 2.0)
Stage 6:  AI-012-4  Correlation matrix update (Pearson + shrinkage)
Stage 7:  AI-012-5  Cross-case propagation (auto-adjust if |delta| > 0.05)
Stage 8:  AI-012-7  Brier/EMA calibration (0.9 x old + 0.1 x new per band)
Stage 9:  AI-012-9  Per-band lookup table adjustment
Stage 10: AI-012-8  Band adjustment (half-width x factor)
Stage 11: AI-007    Hard ceiling check (85% cap)
Stage 12: AI-012-6  RL Bandit advisory note
Stage 13: AI-012-10 Publication Integrity Lock

AI-007 hard ceiling at Stage 11 applies before Stage 13.
Stage 13 is the final publication-layer lock.  No downstream stage may override it.
"""

import math
import statistics
from typing import List, Dict, Optional, Tuple
from config import (
    AI_010_DISCOUNT_MIN_PP,
    CAUSAL_EDGE_OLD_WEIGHT, CAUSAL_EDGE_NEW_WEIGHT,
    CAUSAL_EDGE_ESTABLISHED_THRESHOLD,
    DELTA_BUFFER_SIZE, DELTA_MIN_ENTRIES_FOR_CHANGE_POINT,
    CHANGE_POINT_Z_THRESHOLD,
    CORRELATION_SHRINKAGE_N_MAX, CORRELATION_MIN_N,
    PROPAGATION_DELTA_THRESHOLD,
    EMA_OLD_WEIGHT, EMA_NEW_WEIGHT, EMA_MIN_N_FULL_RANGE, EMA_MIN_N_CAP, EMA_CAP_VALUE,
    RL_ALPHA, RL_EPSILON, RL_GOVERNING_N,
    AI_007_HARD_CEILING,
    PUB_LOCK_H4_GAP_CAP, PUB_LOCK_CHAIN_CAP,
    CONFIDENCE_BANDS,
)
from models import Hypothesis


# ── STAGE 1: AI-010 — SINGLE-CLUSTER H5 DISCOUNT ────────────────────────────

def ai_010_single_cluster_h5_discount(
    hyp: Hypothesis,
    source_cluster_info: Dict,
) -> Tuple[Hypothesis, str]:
    """AI-010 RULE: Single-cluster H5 discount — minimum 10 percentage points
    where Tier 2 corroboration is single state-attributed cluster AND H5
    contradiction present from hardliner bloc within same 24-hour window.
    Cannot be bypassed.
    """
    log = ""
    if not hyp.single_cluster_h5:
        log = "S1(AI-010): Not triggered."
        return hyp, log

    is_single_cluster = source_cluster_info.get("single_cluster", False)
    has_h5 = source_cluster_info.get("h5_contradiction", False)

    if is_single_cluster and has_h5:
        discount = max(AI_010_DISCOUNT_MIN_PP, 0.10)
        hyp.point_estimate -= discount
        hyp.range_lower -= discount
        hyp.range_upper -= discount
        log = f"S1(AI-010): Single-cluster H5 discount applied: -{discount:.0%}"
    else:
        log = "S1(AI-010): Conditions not met. No discount."

    return hyp, log


# ── STAGE 1B: H7 — MECHANICAL ANCHORING TEST ────────────────────────────────

# H7 anchoring risk thresholds
H7_MIN_EDITIONS = 5       # Minimum editions to trigger anchoring detection
H7_DRIFT_THRESHOLD = 0.03 # Max drift from initial value to flag anchoring


def h7_anchoring_test(
    hyp: Hypothesis,
    point_estimate_series: List[float],
) -> Tuple[bool, str]:
    """H7: Mechanical Anchoring Risk Test.

    Detects whether a hypothesis has remained within ±3pp of its initial
    point estimate across 5+ editions, which suggests anchoring bias
    rather than genuine analytical stability.

    Does not modify the hypothesis — raises a flag for narration to address.
    Narration should explicitly justify why the value hasn't moved, or the
    pipeline should apply a widening adjustment to the range.

    Returns: (anchoring_flag, log)
    """
    if len(point_estimate_series) < H7_MIN_EDITIONS:
        return False, (
            f"H7: {hyp.hyp_id} — insufficient history "
            f"({len(point_estimate_series)} editions, need {H7_MIN_EDITIONS}). "
            f"Anchoring test suspended."
        )

    initial = point_estimate_series[0]
    max_drift = max(abs(pt - initial) for pt in point_estimate_series)

    if max_drift <= H7_DRIFT_THRESHOLD:
        return True, (
            f"H7: {hyp.hyp_id} ANCHORING FLAG — max drift {max_drift:.3f} "
            f"from initial {initial:.3f} across {len(point_estimate_series)} editions. "
            f"Narration must justify stability or range should widen."
        )

    return False, (
        f"H7: {hyp.hyp_id} — max drift {max_drift:.3f} > {H7_DRIFT_THRESHOLD}. "
        f"No anchoring concern."
    )


# ── STAGE 2: AI-009 — BAYESIAN UPDATE ────────────────────────────────────────

def ai_009_bayesian_update(
    hyp: Hypothesis,
    likelihood_ratios: List[Dict],
) -> Tuple[Hypothesis, str]:
    """AI-009: Bayesian update — LR table applied to prior.

    likelihood_ratios: list of dicts with:
      - description: str
      - lr: float (likelihood ratio)
    """
    log_parts = []
    current = hyp.point_estimate

    for lr_entry in likelihood_ratios:
        lr = lr_entry["lr"]
        desc = lr_entry["description"]
        prior_odds = current / (1 - current) if current < 1.0 else float('inf')
        posterior_odds = prior_odds * lr
        posterior = posterior_odds / (1 + posterior_odds) if posterior_odds != float('inf') else 1.0
        posterior = max(0.0, min(1.0, posterior))
        log_parts.append(f"LR={lr} ({desc}): {current:.3f}→{posterior:.3f}")
        current = posterior

    hyp.point_estimate = current
    log = "S2(AI-009 Bayes): " + "; ".join(log_parts) if log_parts else "S2(AI-009): No LR updates."
    return hyp, log


# ── STAGE 3: AI-012-1 — CAUSAL EDGE SMOOTHING ───────────────────────────────

def ai_012_1_causal_edge_tracking(
    edges: List[Dict],
) -> Tuple[List[Dict], str]:
    """AI-012-1: Causal Edge Tracking (Exponential Smoothing 0.7/0.3).

    Rule: Edge_strength_new = 0.7 x Edge_strength_old + 0.3 x observed_signal
    Where observed_signal = 1.0 (confirmed) / 0.0 (contradicted) / 0.5 (ambiguous)

    FIX (Item 19): Once an edge is ESTABLISHED (strength > 0.70), it is
    locked — the smoothed value cannot drop below the established threshold.
    Only explicit contradictory evidence (observed_signal = 0.0) from a
    Tier 1 source can break the lock, and even then the floor is 0.50.
    """
    log_parts = []
    for edge in edges:
        old = edge["prior_strength"]
        signal = edge["observed_signal"]
        new = CAUSAL_EDGE_OLD_WEIGHT * old + CAUSAL_EDGE_NEW_WEIGHT * signal

        # Item 19: ESTABLISHED edge lock
        was_established = old >= CAUSAL_EDGE_ESTABLISHED_THRESHOLD
        if was_established and new < CAUSAL_EDGE_ESTABLISHED_THRESHOLD:
            if signal == 0.0:
                # Explicit contradictory evidence — allow decay but floor at 0.50
                new = max(0.50, new)
                lock_note = " LOCK-BROKEN(contradicted→floor 0.50)"
            else:
                # Ambiguous or supporting signal — lock holds
                new = CAUSAL_EDGE_ESTABLISHED_THRESHOLD
                lock_note = " LOCKED(established, floor held)"
        else:
            lock_note = ""

        edge["new_strength"] = round(new, 4)
        established = "ESTABLISHED" if new >= CAUSAL_EDGE_ESTABLISHED_THRESHOLD else ""
        log_parts.append(
            f"{edge['cause']}→{edge['effect']}: {old:.2f}→{new:.2f} {established}{lock_note}"
        )

    log = "S3(AI-012-1): " + "; ".join(log_parts) if log_parts else "S3(AI-012-1): No edges."
    return edges, log


# ── STAGE 4: AI-012-2 — DELTA STATISTICS UPDATE ─────────────────────────────

def ai_012_2_delta_statistics(
    hyp_id: str,
    new_point_estimate: float,
    prior_point_estimate: float,
    buffer: List[float],
) -> Tuple[List[float], float, float, float, str]:
    """AI-012-2: Delta Statistics (Rolling Mean/Std of Last 5 Δp).

    Returns: (updated_buffer, delta_p, mean_delta, std_delta, log)
    """
    delta_p = new_point_estimate - prior_point_estimate
    buffer.append(delta_p)
    if len(buffer) > DELTA_BUFFER_SIZE:
        buffer = buffer[-DELTA_BUFFER_SIZE:]

    if len(buffer) >= 2:
        mean_d = statistics.mean(buffer)
        std_d = statistics.stdev(buffer) if len(buffer) >= 2 else 0.0
    else:
        mean_d = delta_p
        std_d = 0.0

    log = (
        f"S4(AI-012-2): {hyp_id} Δp={delta_p:+.3f}, "
        f"buffer={[round(x,3) for x in buffer]}, "
        f"mean={mean_d:.3f}, std={std_d:.3f}"
    )
    return buffer, delta_p, mean_d, std_d, log


# ── STAGE 5: AI-012-3 — CHANGE POINT DETECTION ──────────────────────────────

def ai_012_3_change_point_detection(
    hyp_id: str,
    delta_p: float,
    mean_delta: float,
    std_delta: float,
    buffer_len: int,
) -> Tuple[bool, float, str]:
    """AI-012-3: Change Point Detection (2-Sigma Anomaly Flagging |z| > 2.0).

    Rule: z = (Δp_current − mean(Δp)) / std(Δp)
    If |z| > 2.0: raise CHANGE POINT FLAG.

    Returns: (flag_raised, z_score, log)
    """
    if buffer_len < DELTA_MIN_ENTRIES_FOR_CHANGE_POINT:
        return False, 0.0, (
            f"S5(AI-012-3): {hyp_id} — insufficient data ({buffer_len} entries). "
            f"Change point detection suspended."
        )

    if std_delta == 0.0 or std_delta < 1e-10:
        return False, 0.0, (
            f"S5(AI-012-3): {hyp_id} — std=0. No flag."
        )

    z = (delta_p - mean_delta) / std_delta
    flag = abs(z) > CHANGE_POINT_Z_THRESHOLD

    log = (
        f"S5(AI-012-3): {hyp_id} z={z:.2f} "
        f"({'CHANGE POINT FLAG RAISED' if flag else 'No flag'})"
    )
    return flag, z, log


# ── STAGE 6: AI-012-4 — CORRELATION MATRIX UPDATE ───────────────────────────

def ai_012_4_correlation_matrix(
    point_estimate_series: Dict[str, List[float]],
    n: int,
) -> Tuple[Dict[Tuple[str, str], float], str]:
    """AI-012-4: Correlation Matrix (Pearson + Shrinkage confidence = n/20).

    Rule: effective_correlation = raw_correlation x (n/20)
    At n < 5: correlation treated as zero.

    Returns: (matrix_dict, log)
    """
    hyp_ids = sorted(point_estimate_series.keys())
    matrix = {}
    log_parts = []
    shrinkage = min(n / CORRELATION_SHRINKAGE_N_MAX, 1.0)

    for i, ha in enumerate(hyp_ids):
        for j, hb in enumerate(hyp_ids):
            if i >= j:
                if i == j:
                    matrix[(ha, hb)] = 1.0
                continue

            series_a = point_estimate_series[ha]
            series_b = point_estimate_series[hb]
            min_len = min(len(series_a), len(series_b))

            if min_len < CORRELATION_MIN_N:
                matrix[(ha, hb)] = 0.0
                matrix[(hb, ha)] = 0.0
                continue

            sa = series_a[-min_len:]
            sb = series_b[-min_len:]

            if len(set(sa)) <= 1 or len(set(sb)) <= 1:
                raw = 0.0
            else:
                mean_a = statistics.mean(sa)
                mean_b = statistics.mean(sb)
                std_a = statistics.stdev(sa)
                std_b = statistics.stdev(sb)
                if std_a == 0 or std_b == 0:
                    raw = 0.0
                else:
                    covar = sum((a - mean_a) * (b - mean_b) for a, b in zip(sa, sb)) / (min_len - 1)
                    raw = covar / (std_a * std_b)

            eff = raw * shrinkage
            matrix[(ha, hb)] = round(eff, 4)
            matrix[(hb, ha)] = round(eff, 4)
            log_parts.append(f"{ha}/{hb}: raw={raw:.2f}, eff={eff:.2f}")

    log = f"S6(AI-012-4): n={n}, shrinkage={shrinkage:.2f}. " + "; ".join(log_parts[:5])
    return matrix, log


# ── STAGE 7: AI-012-5 — CROSS-CASE PROPAGATION ──────────────────────────────

def ai_012_5_cross_case_propagation(
    hypotheses: Dict[str, Hypothesis],
    propagation_register: List[Dict],
    deltas: Dict[str, float],
) -> Tuple[Dict[str, Hypothesis], List[str], str]:
    """AI-012-5: Cross-Case Propagation (auto-adjust if |Δ| > 0.05).

    Rule: When any hypothesis point estimate changes by |Δ| > 0.05,
    check propagation register for named downstream effects.
    Apply stated adjustment automatically.

    Returns: (updated_hypotheses, applied_propagations, log)
    """
    applied = []
    log_parts = []

    for rule in propagation_register:
        trigger = rule["trigger_hyp"]
        direction = rule["direction"]
        downstream = rule["downstream_hyp"]
        adj = rule["adjustment"]

        delta = deltas.get(trigger, 0.0)

        triggered = False
        if direction == "UP" and delta > PROPAGATION_DELTA_THRESHOLD:
            triggered = True
        elif direction == "DOWN" and delta < -PROPAGATION_DELTA_THRESHOLD:
            triggered = True

        if triggered and downstream in hypotheses:
            hyp = hypotheses[downstream]
            if direction == "DOWN":
                actual_adj = -abs(adj)
            else:
                actual_adj = abs(adj)
            hyp.point_estimate += actual_adj
            hyp.point_estimate = max(0.0, min(1.0, hyp.point_estimate))
            applied.append(
                f"{trigger} Δ={delta:+.3f} → {downstream} {actual_adj:+.3f}"
            )
            log_parts.append(
                f"{trigger}→{downstream}: {actual_adj:+.3f} applied"
            )

    log = "S7(AI-012-5): " + ("; ".join(log_parts) if log_parts else "No propagations triggered.")
    return hypotheses, applied, log


# ── STAGE 8: AI-012-7 — BRIER/EMA CALIBRATION ───────────────────────────────

def ai_012_7_brier_ema_calibration(
    band_errors: Dict[str, Dict],
    new_resolutions: List[Dict],
) -> Tuple[Dict[str, Dict], str]:
    """AI-012-7: Brier/EMA Calibration (0.9 x old + 0.1 x new per band).

    RETIREMENT NOTICE: AI-009 old shrinkage rule RETIRED — replaced by this EMA.

    Rule: EMA_error(band) = 0.9 x EMA_error_old + 0.1 x current_error

    Minimum n caveat: n<5 per band → adjustments capped at +/-3%.

    new_resolutions: list of dicts with:
      - band: str
      - predicted: float (fi)
      - observed: float (oi)
    """
    log_parts = []

    for res in new_resolutions:
        band = res["band"]
        error = res["predicted"] - res["observed"]

        if band in band_errors:
            old_ema = band_errors[band]["ema_error"]
            new_ema = EMA_OLD_WEIGHT * old_ema + EMA_NEW_WEIGHT * error
            band_errors[band]["ema_error"] = new_ema
            band_errors[band]["n"] = band_errors[band].get("n", 0) + 1
            log_parts.append(f"{band}: EMA {old_ema:.3f}→{new_ema:.3f}")
        else:
            band_errors[band] = {"ema_error": error * EMA_NEW_WEIGHT, "n": 1}
            log_parts.append(f"{band}: NEW EMA={error * EMA_NEW_WEIGHT:.3f}")

    log = "S8(AI-012-7): " + ("; ".join(log_parts) if log_parts else "No new resolutions.")
    return band_errors, log


# ── STAGE 9: AI-012-9 — PER-BAND LOOKUP TABLE ADJUSTMENT ────────────────────

def ai_012_9_per_band_lookup(
    raw_prob: float,
    band: str,
    band_errors: Dict[str, Dict],
) -> Tuple[float, str]:
    """AI-012-9: Per-Band Calibration Lookup Table.

    Rule: Published probability = Raw probability x (1 + adjustment)
    Adjustments from bands with n<5 capped at +/-3%.
    """
    if band not in band_errors:
        return raw_prob, f"S9(AI-012-9): {band} — no data. No adjustment."

    entry = band_errors[band]
    ema = entry["ema_error"]
    n = entry.get("n", 0)

    # Determine adjustment
    if n < EMA_MIN_N_CAP:
        adjustment = max(-EMA_CAP_VALUE, min(EMA_CAP_VALUE, ema))
        cap_note = f"capped at +/-{EMA_CAP_VALUE:.0%} (n={n})"
    elif n < EMA_MIN_N_FULL_RANGE:
        adjustment = max(-EMA_CAP_VALUE, min(EMA_CAP_VALUE, ema))
        cap_note = f"capped (n={n}, need {EMA_MIN_N_FULL_RANGE} for full range)"
    else:
        adjustment = max(-0.10, min(0.10, ema))
        cap_note = f"full range (n={n})"

    adjusted = raw_prob * (1 + adjustment)
    adjusted = max(0.0, min(1.0, adjusted))

    log = (
        f"S9(AI-012-9): {band} adj={adjustment:+.3f} ({cap_note}). "
        f"Raw {raw_prob:.3f} → {adjusted:.3f}"
    )
    return adjusted, log


# ── STAGE 10: AI-012-8 — BAND ADJUSTMENT ────────────────────────────────────

def ai_012_8_band_adjustment(
    lower: float, upper: float,
    q_table_factor: float,
) -> Tuple[float, float, str]:
    """AI-012-8: Band Adjustment (Half-Width x Factor).

    Rule:
      midpoint = (lower + upper) / 2
      half_width = (upper - lower) / 2
      adjusted_half_width = half_width x factor
      published_range = [midpoint - adjusted, midpoint + adjusted]
    """
    midpoint = (lower + upper) / 2
    half_width = (upper - lower) / 2
    adjusted_hw = half_width * q_table_factor
    new_lower = max(0.0, midpoint - adjusted_hw)
    new_upper = min(1.0, midpoint + adjusted_hw)

    log = (
        f"S10(AI-012-8): mid={midpoint:.3f}, hw={half_width:.3f}, "
        f"factor={q_table_factor:.2f}, adj_hw={adjusted_hw:.3f}, "
        f"range=[{new_lower:.3f}, {new_upper:.3f}]"
    )
    return new_lower, new_upper, log


# ── STAGE 11: AI-007 — HARD CEILING CHECK ───────────────────────────────────

def ai_007_hard_ceiling_check(
    hyp: Hypothesis,
) -> Tuple[Hypothesis, str, str]:
    """AI-007: Hard Ceiling Check (85% cap, confidence label assignment).

    No hypothesis above 85% without named formal evidence.
    AI-007 hard ceilings cannot be overridden by AI-012 under any circumstances.

    Returns: (hyp, confidence_label, log)
    """
    capped = False
    if hyp.point_estimate > AI_007_HARD_CEILING and hyp.status not in ("CONFIRMED", "NEAR-CONFIRMED PROVISIONAL"):
        hyp.point_estimate = AI_007_HARD_CEILING
        if hyp.range_upper > AI_007_HARD_CEILING:
            hyp.range_upper = AI_007_HARD_CEILING
        capped = True

    # Assign confidence label per band governance
    pt = hyp.point_estimate
    label = "MEDIUM"  # default
    for band_name, (lo, hi) in CONFIDENCE_BANDS.items():
        if lo <= pt <= hi:
            label = band_name.replace("_", "-")
            break

    log = (
        f"S11(AI-007): {hyp.hyp_id} pt={pt:.3f} → {label}"
        + (" [CAPPED at 85%]" if capped else " [PASS]")
    )
    return hyp, label, log


# ── STAGE 12: AI-012-6 — RL BANDIT ADVISORY NOTE ────────────────────────────

def ai_012_6_rl_bandit(
    band: str,
    q_table: Dict[str, Dict],
    resolution: Optional[Dict] = None,
) -> Tuple[Dict[str, Dict], float, str]:
    """AI-012-6: RL Bandit (epsilon-Greedy Q-Learning for Band Factors).

    STATUS: ADVISORY ONLY — n<30.  Governing at n>=30.

    Rule: Q(band, factor) <- Q(band, factor) + alpha x (reward - Q(band, factor))
    where reward = -(fi - oi)^2, alpha=0.1, epsilon=0.1.

    Hard constraint: Cannot override AI-007 hard ceilings.

    Returns: (updated_q_table, recommended_factor, log)
    """
    if band not in q_table:
        q_table[band] = {"factor": 1.0, "q_value": 0.0, "n": 0}

    entry = q_table[band]

    if resolution:
        fi = resolution["fi"]
        oi = resolution["oi"]
        reward = -(fi - oi) ** 2
        entry["q_value"] = entry["q_value"] + RL_ALPHA * (reward - entry["q_value"])
        entry["n"] = entry.get("n", 0) + 1

    factor = entry["factor"]
    status = "INDICATIVE"
    if entry.get("n", 0) >= RL_GOVERNING_N:
        status = "GOVERNING"
    elif entry.get("n", 0) >= 10:
        status = "OPERATIONAL"

    log = (
        f"S12(AI-012-6): {band} factor={factor:.2f}, "
        f"Q={entry['q_value']:.3f}, status={status}"
    )
    return q_table, factor, log


# ── STAGE 13: AI-012-10 — PUBLICATION INTEGRITY LOCK ────────────────────────

def ai_012_10_publication_integrity_lock(
    hyp: Hypothesis,
) -> Tuple[Hypothesis, str]:
    """AI-012-10: Publication Integrity Lock.

    Two independent sub-conditions — both checked:

    (a) If H4 gap active AND Tier 1 denial active AND no observable
        preparatory action: p_pub = min(p_pub, 0.50)

    (b) If independent evidential chains < 2 (per Gate 0.2 definition):
        p_pub = min(p_pub, 0.60)

    This stage is the final numerical constraint before publication.
    No downstream stage may override it.  Violation = PLM entry mandatory.
    """
    log_parts = []
    original = hyp.point_estimate

    # Sub-condition (a)
    if (hyp.h4_gap_active and hyp.tier1_denial_active
            and hyp.no_observable_prep_action):
        if hyp.point_estimate > PUB_LOCK_H4_GAP_CAP:
            hyp.point_estimate = PUB_LOCK_H4_GAP_CAP
            hyp.range_upper = min(hyp.range_upper, PUB_LOCK_H4_GAP_CAP + 0.06)
            log_parts.append(
                f"Sub-condition (a) TRIGGERED: H4 gap + Tier 1 denial + "
                f"no prep action → capped at {PUB_LOCK_H4_GAP_CAP:.0%}"
            )
        else:
            log_parts.append("Sub-condition (a): checked, not binding.")

    # Sub-condition (b)
    if hyp.independent_chains < 2:
        if hyp.point_estimate > PUB_LOCK_CHAIN_CAP:
            hyp.point_estimate = PUB_LOCK_CHAIN_CAP
            hyp.range_upper = min(hyp.range_upper, PUB_LOCK_CHAIN_CAP + 0.05)
            log_parts.append(
                f"Sub-condition (b) TRIGGERED: {hyp.independent_chains} "
                f"independent chains < 2 → capped at {PUB_LOCK_CHAIN_CAP:.0%}"
            )
        else:
            log_parts.append("Sub-condition (b): checked, not binding.")

    if not log_parts:
        log_parts.append("No sub-conditions triggered.")

    final_note = ""
    if hyp.point_estimate != original:
        final_note = f" [{original:.3f}→{hyp.point_estimate:.3f}]"

    log = "S13(AI-012-10): " + "; ".join(log_parts) + final_note
    return hyp, log


# ── POST-PIPELINE: RANGE-POINT ESTIMATE RECONCILIATION ───────────────────────

def _reconcile_range_and_point(
    hyp: Hypothesis,
) -> Tuple[Hypothesis, str]:
    """Ensure point estimate falls within published range after all 13 stages.

    Strategy:
      - If pt is above range_upper: shift range upward, keeping the same width.
      - If pt is below range_lower: shift range downward, keeping the same width.
      - Clamp final range to [0.0, 1.0].
      - Special cases: CONFIRMED (pt=1.0) and CONTRADICTED (pt=0.0) are exempt.

    This runs AFTER Stage 13 so it cannot violate Publication Integrity Lock —
    it only moves the range, never the point estimate.
    """
    if hyp.status in ("CONFIRMED", "CONTRADICTED"):
        return hyp, "RECONCILE: Exempt (CONFIRMED/CONTRADICTED)."

    pt = hyp.point_estimate
    lo = hyp.range_lower
    hi = hyp.range_upper
    width = hi - lo

    if lo <= pt <= hi:
        return hyp, f"RECONCILE: pt={pt:.3f} within [{lo:.3f}, {hi:.3f}]. No adjustment."

    old_range = f"[{lo:.3f}, {hi:.3f}]"

    if pt > hi:
        # Shift range up: centre on pt, keep width, but ensure pt is inside
        new_upper = min(1.0, pt + width * 0.35)
        new_lower = max(0.0, new_upper - width)
        # Ensure pt is inside the new range
        if pt > new_upper:
            new_upper = min(1.0, pt + 0.03)
        if pt < new_lower:
            new_lower = max(0.0, pt - 0.03)
    else:  # pt < lo
        # Shift range down: centre on pt, keep width, but ensure pt is inside
        new_lower = max(0.0, pt - width * 0.35)
        new_upper = min(1.0, new_lower + width)
        # Ensure pt is inside the new range
        if pt < new_lower:
            new_lower = max(0.0, pt - 0.03)
        if pt > new_upper:
            new_upper = min(1.0, pt + 0.03)

    hyp.range_lower = round(new_lower, 4)
    hyp.range_upper = round(new_upper, 4)

    log = (
        f"RECONCILE: pt={pt:.3f} outside {old_range} → "
        f"range shifted to [{hyp.range_lower:.3f}, {hyp.range_upper:.3f}]"
    )
    return hyp, log


# ── TQL TIER 4 DEPENDENCY TEST (Gap 5 fix) ───────────────────────────────────

def tql_tier4_dependency_test(
    case_hypotheses: List[Hypothesis],
    tier4_lrs: Dict[str, List[Dict]],
) -> Dict[str, Dict]:
    """TQL Item 4 — Mechanical Tier 4 Dependency Test.

    Tests whether removing Tier 4 sources changes the dominant hypothesis
    for a case. This makes the TQL Item 4 check reproducible rather than
    relying on narration to guess.

    Args:
        case_hypotheses: All hypotheses for one case.
        tier4_lrs: Dict mapping hyp_id -> list of LR entries that came
                   from Tier 4 sources (Wikipedia, ACLED, etc).

    Returns dict mapping hyp_id -> {
        pt_with_t4: float,
        pt_without_t4: float,
        delta: float,
        dominant_holds: bool,
    }
    """
    if not case_hypotheses:
        return {}

    result = {}

    # Find the dominant hypothesis (highest pt)
    dominant = max(case_hypotheses, key=lambda h: h.point_estimate)

    for hyp in case_hypotheses:
        pt_with = hyp.point_estimate
        lrs = tier4_lrs.get(hyp.hyp_id, [])

        # Reverse the Tier 4 LR effects
        pt_without = pt_with
        for lr_entry in lrs:
            lr = lr_entry.get("lr", 1.0)
            if lr == 1.0 or lr <= 0:
                continue
            # Reverse: posterior -> prior by dividing by LR
            if pt_without <= 0 or pt_without >= 1.0:
                continue
            posterior_odds = pt_without / (1 - pt_without)
            prior_odds = posterior_odds / lr
            pt_without = prior_odds / (1 + prior_odds)
            pt_without = max(0.0, min(1.0, pt_without))

        result[hyp.hyp_id] = {
            "pt_with_t4": round(pt_with, 4),
            "pt_without_t4": round(pt_without, 4),
            "delta": round(pt_with - pt_without, 4),
            "dominant_holds": True,  # Updated below
        }

    # Check if the dominant hypothesis changes when Tier 4 is removed
    if len(result) > 1:
        pts_without = {hid: r["pt_without_t4"] for hid, r in result.items()}
        new_dominant = max(pts_without, key=pts_without.get)
        for hid in result:
            result[hid]["dominant_holds"] = (new_dominant == dominant.hyp_id)

    return result


# ── TIER 4 DEPENDENCY LEG CHECK (Architecture Section 4 — Fix #12) ───────────

def tier4_dependency_leg_check(
    hyp: Hypothesis,
    tier4_lr_count: int,
    other_lr_count: int,
) -> Tuple[Hypothesis, str]:
    """Architecture Section 4 line 121:
    "Where any hypothesis relies on Tier 4 data, corroboration legs must be
    explicitly separated: Leg 1 (Tier 1/2 only) and Leg 2 (Tier 4 directional).
    Leg 1 must independently sustain the stated probability range.
    If it cannot, reduce the range."

    Mechanical implementation: if Tier 4 LRs constitute the majority of
    evidence for a hypothesis, narrow the range upper bound by 5pp to reflect
    that Tier 1/2 alone cannot fully sustain the higher probability.
    """
    if tier4_lr_count == 0:
        return hyp, f"TIER4-LEG: {hyp.hyp_id} — no Tier 4 dependency."

    # If Tier 4 dominates, that violates the architecture.  Narrow.
    if tier4_lr_count > other_lr_count and other_lr_count == 0:
        # Pure Tier 4 evidence — collapse range upper by 5pp
        old_upper = hyp.range_upper
        hyp.range_upper = max(hyp.range_lower + 0.02, hyp.range_upper - 0.05)
        # Also ensure pt is within new range
        if hyp.point_estimate > hyp.range_upper:
            hyp.point_estimate = hyp.range_upper
        return hyp, (
            f"TIER4-LEG: {hyp.hyp_id} — Tier 4 dominant ({tier4_lr_count} vs "
            f"{other_lr_count}). Range upper reduced {old_upper:.3f}→{hyp.range_upper:.3f}."
        )

    return hyp, (
        f"TIER4-LEG: {hyp.hyp_id} — Tier 4 present but not dominant "
        f"({tier4_lr_count} Tier 4 vs {other_lr_count} other). No adjustment."
    )


# ── FULL PIPELINE EXECUTOR ───────────────────────────────────────────────────

def execute_full_pipeline(
    hyp: Hypothesis,
    prior_hyp: Optional[Hypothesis],
    source_cluster_info: Dict,
    likelihood_ratios: List[Dict],
    causal_edges: List[Dict],
    delta_buffer: List[float],
    point_estimate_series: Dict[str, List[float]],
    n_editions: int,
    hypotheses_map: Dict[str, Hypothesis],
    propagation_register: List[Dict],
    deltas: Dict[str, float],
    band_errors: Dict[str, Dict],
    new_resolutions: List[Dict],
    q_table: Dict[str, Dict],
    resolution_for_bandit: Optional[Dict],
    skip_propagation: bool = False,
) -> Dict:
    """Execute the full 13-stage pipeline for one hypothesis.

    Args:
        skip_propagation: If True, Stage 7 (cross-case propagation) is
            deferred — the delta is recorded but propagation is NOT applied.
            The caller is responsible for running a single batch propagation
            pass after all hypotheses complete their individual pipelines.
            This prevents duplicate propagation from the shared deltas dict
            being re-checked on every per-hypothesis call.

    Returns dict with all results and the complete pipeline log.
    """
    pipeline_log = []

    # Stage 1: AI-010
    hyp, s1_log = ai_010_single_cluster_h5_discount(hyp, source_cluster_info)
    pipeline_log.append(s1_log)

    # Stage 1B: H7 Anchoring Test
    hyp_series = point_estimate_series.get(hyp.hyp_id, [])
    h7_flag, h7_log = h7_anchoring_test(hyp, hyp_series)
    pipeline_log.append(h7_log)

    # Stage 2: AI-009
    hyp, s2_log = ai_009_bayesian_update(hyp, likelihood_ratios)
    pipeline_log.append(s2_log)

    # Stage 3: AI-012-1
    edges, s3_log = ai_012_1_causal_edge_tracking(causal_edges)
    pipeline_log.append(s3_log)

    # Stage 4: AI-012-2
    prior_pt = prior_hyp.point_estimate if prior_hyp else hyp.point_estimate
    buffer, delta_p, mean_d, std_d, s4_log = ai_012_2_delta_statistics(
        hyp.hyp_id, hyp.point_estimate, prior_pt, delta_buffer)
    pipeline_log.append(s4_log)

    # Stage 5: AI-012-3
    flag, z_score, s5_log = ai_012_3_change_point_detection(
        hyp.hyp_id, delta_p, mean_d, std_d, len(buffer))
    pipeline_log.append(s5_log)

    # Stage 6: AI-012-4
    correlation_matrix, s6_log = ai_012_4_correlation_matrix(
        point_estimate_series, n_editions)
    pipeline_log.append(s6_log)

    # Stage 7: AI-012-5
    deltas[hyp.hyp_id] = delta_p
    hypotheses_map[hyp.hyp_id] = hyp
    if skip_propagation:
        # Defer to single batch pass after all hypotheses are processed.
        # Record delta and update map, but do NOT apply propagation here.
        applied_props = []
        s7_log = "S7(AI-012-5): Deferred to post-pipeline batch pass."
    else:
        hypotheses_map, applied_props, s7_log = ai_012_5_cross_case_propagation(
            hypotheses_map, propagation_register, deltas)
        hyp = hypotheses_map[hyp.hyp_id]
    pipeline_log.append(s7_log)

    # Stage 8: AI-012-7
    band_errors, s8_log = ai_012_7_brier_ema_calibration(band_errors, new_resolutions)
    pipeline_log.append(s8_log)

    # Determine band for this hypothesis
    band = _get_band(hyp.point_estimate)

    # Stage 9: AI-012-9
    adjusted_pt, s9_log = ai_012_9_per_band_lookup(hyp.point_estimate, band, band_errors)
    hyp.point_estimate = adjusted_pt
    pipeline_log.append(s9_log)

    # Stage 10: AI-012-8
    q_factor = q_table.get(band, {}).get("factor", 1.0)
    new_lower, new_upper, s10_log = ai_012_8_band_adjustment(
        hyp.range_lower, hyp.range_upper, q_factor)
    hyp.range_lower = new_lower
    hyp.range_upper = new_upper
    pipeline_log.append(s10_log)

    # Stage 11: AI-007
    hyp, conf_label, s11_log = ai_007_hard_ceiling_check(hyp)
    pipeline_log.append(s11_log)

    # Stage 12: AI-012-6
    q_table, rec_factor, s12_log = ai_012_6_rl_bandit(band, q_table, resolution_for_bandit)
    pipeline_log.append(s12_log)

    # Stage 13: AI-012-10
    hyp, s13_log = ai_012_10_publication_integrity_lock(hyp)
    pipeline_log.append(s13_log)

    # ── POST-PIPELINE: RANGE-POINT ESTIMATE RECONCILIATION ────────────────
    # Gap 9 fix: After all 13 stages, ensure the published point estimate
    # falls within the published range.  If the pipeline moved the pt outside
    # the range, expand the range to encompass it while preserving the
    # original half-width (uncertainty band).  If the pt was capped by
    # AI-007 or AI-012-10 downward, shrink the range ceiling to match.
    hyp, reconcile_log = _reconcile_range_and_point(hyp)
    pipeline_log.append(reconcile_log)

    return {
        "hypothesis": hyp,
        "confidence_label": conf_label,
        "pipeline_log": pipeline_log,
        "causal_edges": edges,
        "delta_buffer": buffer,
        "delta_p": delta_p,
        "mean_delta": mean_d,
        "std_delta": std_d,
        "change_point_flag": flag,
        "z_score": z_score,
        "correlation_matrix": correlation_matrix,
        "applied_propagations": applied_props,
        "band_errors": band_errors,
        "q_table": q_table,
        "band": band,
        "h7_anchoring_flag": h7_flag,
    }


def _get_band(pt: float) -> str:
    """Map a point estimate to its lookup band string."""
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
        if lo <= pt < hi:
            return label
    if pt >= 0.90:
        return "90-100%"
    return "40-60%"  # fallback
