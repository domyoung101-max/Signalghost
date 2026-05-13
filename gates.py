"""gates.py — Signalghost gate registry.

GATE REGISTRY — FULL (v1.1.0 — Gates 0.2, 0.3, 0.4 added 26 April 2026)

Updated Gate Execution Order:
  Seq 1: Gate 0.1 — Temporal Currency Check (Pre-analysis)
  Seq 2: Gate 0.2 — Source Corroboration Requirement (Pre-analysis)
  Seq 3: Gate 0.5 — Cluster Risk Check (Pre-analysis)
  Seq 4: Gate 0.3 — Incentive Analysis Completion (Pre-publication >60%)
  Seq 5: Gate 0.4 — Cross-Case Consistency Check (Pre-publication >70%)
  Seq 6: Gate 0.6 — Absence / Threshold Gate (Per-edition verification)
  Seq 7: Gate 5  — Resolution Gate (Prediction resolution only)

Gates 0.1, 0.2, 0.5 checked at feed
sweep stage.
Gates 0.3, 0.4 checked at pre-publication stage after 12-stage pipeline.
Gate 0.6 checked per-edition for all absence claims and threshold events.
Gate 5 checked only at formal prediction resolution.
"""

from typing import List, Dict, Optional
from config import (
    GATE_0_2_TIER3_PP_TRIGGER,
    GATE_0_3_THRESHOLD,
    GATE_0_4_THRESHOLD,
    GATE_0_4_CORRELATION_THRESHOLD,
    GATE_0_4_PARTNER_FLOOR,
    GATE_0_6_ROCKET_THRESHOLD,
)
from models import GateRecord, Hypothesis
from persistence import insert_row


def _record_gate(record: GateRecord):
    """Persist a gate record."""
    insert_row("gate_records", {
        "gate_id": record.gate_id,
        "gate_name": record.gate_name,
        "edition": record.edition,
        "passed": 1 if record.passed else 0,
        "details": record.details,
        "hyp_id": record.hyp_id,
    })
    return record


# ── GATE 0.1 — TEMPORAL CURRENCY CHECK ──────────────────────────────────────

def gate_0_1_temporal_currency_check(
    carry_forward_facts: List[Dict],
    current_date,
    edition: int,
) -> GateRecord:
    """Gate 0.1 — Temporal Currency Check (Pre-analysis).

    Before any carry-forward fact is cited as governing, it must be within
    temporal currency window for its claim type.  Stale facts must be flagged
    and re-verified before use.  Absence claims require Gate 0.6 confirmation.
    """
    stale_facts = []
    for fact in carry_forward_facts:
        staleness = fact.get("staleness_days", 0)
        if staleness is not None and staleness > 3:
            stale_facts.append(
                f"{fact.get('fact', 'UNKNOWN')[:60]}... ({staleness}d stale)"
            )

    passed = len(stale_facts) == 0
    details = "All facts current." if passed else (
        f"{len(stale_facts)} stale facts flagged for re-verification: "
        + "; ".join(stale_facts[:5])
    )

    return _record_gate(GateRecord(
        gate_id="Gate 0.1",
        gate_name="Temporal Currency Check",
        edition=edition,
        passed=passed,
        details=details,
    ))


# ── GATE 0.2 — SOURCE CORROBORATION REQUIREMENT ─────────────────────────────

def gate_0_2_source_corroboration_requirement(
    tier3_claims: List[Dict],
    edition: int,
) -> GateRecord:
    """Gate 0.2 — Source Corroboration Requirement (Pre-analysis).

    Before a Tier 3 source can influence a Tier 2 probability assessment,
    at least one independent Tier 1 or Tier 2 source must corroborate the
    same claim through a different evidential chain.

    Trigger condition: Any Tier 3 source cited in support of a probability
    adjustment above 5pp.

    Action if failed: Tier 3 source noted but carries zero governing weight.
    Probability adjustment is not applied.

    PMM relevance: PMM-003.

    tier3_claims: list of dicts with keys:
      - source_name: str
      - adjustment_pp: float
      - corroborated: bool
      - corroboration_source: str (Tier 1/2 source name if corroborated)
    """
    failures = []
    for claim in tier3_claims:
        if claim["adjustment_pp"] > GATE_0_2_TIER3_PP_TRIGGER:
            if not claim.get("corroborated", False):
                failures.append(
                    f"{claim['source_name']}: +{claim['adjustment_pp']:.0%} "
                    f"adjustment — NO independent Tier 1/2 corroboration. "
                    f"Zero governing weight applied."
                )

    passed = len(failures) == 0
    details = "No Tier 3 sources above 5pp trigger." if passed else (
        f"{len(failures)} uncorroborated Tier 3 claims blocked: "
        + "; ".join(failures)
    )

    return _record_gate(GateRecord(
        gate_id="Gate 0.2",
        gate_name="Source Corroboration Requirement",
        edition=edition,
        passed=passed,
        details=details,
    ))


# ── GATE 0.3 — INCENTIVE ANALYSIS COMPLETION ────────────────────────────────

def gate_0_3_incentive_analysis_completion(
    hypotheses: List[Hypothesis],
    h1_analyses_completed: Dict[str, bool],
    edition: int,
) -> List[GateRecord]:
    """Gate 0.3 — Incentive Analysis Completion (Pre-publication >60%).

    Before any hypothesis involving a named actor's stated intent can advance
    above 60%, a completed H1 (Incentive Mismatch) analysis must be documented.

    Trigger: Any hypothesis above 60% resting materially on named actor's
    stated intent or public declaration.

    Action if failed: Hypothesis capped at 60% until H1 completed.

    PMM relevance: PMM-001, PMM-004.

    Returns list of GateRecords (one per triggered hypothesis).
    """
    records = []
    for hyp in hypotheses:
        if hyp.point_estimate > GATE_0_3_THRESHOLD:
            h1_done = h1_analyses_completed.get(hyp.hyp_id, False)
            passed = h1_done
            details = (
                f"{hyp.hyp_id} at {hyp.point_estimate:.0%} — "
                + ("H1 bilateral analysis completed. PASS." if passed
                   else f"H1 analysis NOT completed. CAPPED at {GATE_0_3_THRESHOLD:.0%}.")
            )
            records.append(_record_gate(GateRecord(
                gate_id="Gate 0.3",
                gate_name="Incentive Analysis Completion",
                edition=edition,
                passed=passed,
                details=details,
                hyp_id=hyp.hyp_id,
            )))
    return records


# ── GATE 0.4 — CROSS-CASE CONSISTENCY CHECK ─────────────────────────────────

def gate_0_4_cross_case_consistency_check(
    hypotheses: List[Hypothesis],
    correlation_matrix: Dict,
    edition: int,
) -> List[GateRecord]:
    """Gate 0.4 — Cross-Case Consistency Check (Pre-publication >70%).

    Before any hypothesis above 70% can be published, its point estimate must
    be checked for consistency with all positively correlated hypotheses
    (Pearson correlation > 0.30).  If a positively correlated hypothesis sits
    below 35%, the discrepancy must be explained.

    Trigger: Any hypothesis above 70% with a positively correlated partner
    below 35%.

    Action if failed: Resolve discrepancy before publication.

    PMM relevance: Edition 032.

    correlation_matrix: dict mapping (hyp_a, hyp_b) -> effective_correlation
    """
    records = []
    hyp_map = {h.hyp_id: h for h in hypotheses}

    for hyp in hypotheses:
        if hyp.point_estimate <= GATE_0_4_THRESHOLD:
            continue
        # Check all positively correlated partners
        discrepancies = []
        for (ha, hb), corr in correlation_matrix.items():
            partner_id = None
            if ha == hyp.hyp_id and corr > GATE_0_4_CORRELATION_THRESHOLD:
                partner_id = hb
            elif hb == hyp.hyp_id and corr > GATE_0_4_CORRELATION_THRESHOLD:
                partner_id = ha

            if partner_id and partner_id in hyp_map:
                partner = hyp_map[partner_id]
                if partner.point_estimate < GATE_0_4_PARTNER_FLOOR:
                    discrepancies.append(
                        f"{partner_id} at {partner.point_estimate:.0%} "
                        f"(corr {corr:.2f})"
                    )

        passed = len(discrepancies) == 0
        details = (
            f"{hyp.hyp_id} at {hyp.point_estimate:.0%} — "
            + ("No inconsistent correlated partners. PASS." if passed
               else f"Discrepancies: {'; '.join(discrepancies)}. "
                    f"Must reconcile before publication.")
        )
        records.append(_record_gate(GateRecord(
            gate_id="Gate 0.4",
            gate_name="Cross-Case Consistency Check",
            edition=edition,
            passed=passed,
            details=details,
            hyp_id=hyp.hyp_id,
        )))
    return records


# ── GATE 0.5 — CLUSTER RISK CHECK ───────────────────────────────────────────

def gate_0_5_cluster_risk_check(
    hypotheses: List[Hypothesis],
    source_clusters: Dict[str, Dict],
    edition: int,
) -> GateRecord:
    """Gate 0.5 — Cluster Risk Check (Pre-analysis).

    Before any hypothesis reaches HIGH confidence on the basis of multiple
    sources, verify that those sources are genuinely independent and not a
    single-cluster echo.  A cluster of Tier 3 sources all tracing to the
    same original claim counts as one source, not multiple confirmations.

    source_clusters: dict mapping hyp_id -> {
        "source_count": int,
        "independent_clusters": int,
        "single_cluster": bool,
        "h5_contradiction": bool,
    }
    """
    failures = []
    for hyp in hypotheses:
        cluster = source_clusters.get(hyp.hyp_id, {})
        if cluster.get("single_cluster", False) and hyp.point_estimate >= 0.70:
            failures.append(
                f"{hyp.hyp_id}: HIGH confidence on single-cluster sources. "
                f"AI-010 discount required."
            )

    passed = len(failures) == 0
    details = "No single-cluster HIGH confidence detected." if passed else (
        "; ".join(failures)
    )

    return _record_gate(GateRecord(
        gate_id="Gate 0.5",
        gate_name="Cluster Risk Check",
        edition=edition,
        passed=passed,
        details=details,
    ))


# ── GATE 0.6 — ABSENCE / THRESHOLD GATE ─────────────────────────────────────

def gate_0_6_absence_threshold_gate(
    absence_claims: List[Dict],
    threshold_events: List[Dict],
    edition: int,
) -> GateRecord:
    """Gate 0.6 — Absence / Threshold Gate (Per-edition verification).

    For every absence claim (no strike, no barrage, no enforcement action)
    and every threshold event (100+ rockets, kinetic USN attack, etc.),
    a named verification must be documented per edition.

    Absence of evidence is only evidentially valid if the named feeds were
    checked and returned no result.

    absence_claims: list of dicts with:
      - claim: str
      - feeds_checked: List[str]
      - verified: bool

    threshold_events: list of dicts with:
      - event: str
      - threshold: str (e.g. "100+ rockets")
      - confirmed: bool
      - source: str
    """
    failures = []
    for claim in absence_claims:
        if not claim.get("verified", False):
            failures.append(f"Absence claim not verified: {claim['claim']}")

    for event in threshold_events:
        if event.get("confirmed", False):
            failures.append(
                f"Threshold event CONFIRMED: {event['event']} "
                f"({event['threshold']}) — Gate 0.6 BREACHED"
            )

    # Gate 0.6 PASS means no threshold breached and all absences verified
    breached = any(e.get("confirmed", False) for e in threshold_events)
    unverified = any(not c.get("verified", False) for c in absence_claims)

    passed = not breached and not unverified
    details = "All absence claims verified. No thresholds breached." if passed else (
        "; ".join(failures)
    )

    return _record_gate(GateRecord(
        gate_id="Gate 0.6",
        gate_name="Absence / Threshold Gate",
        edition=edition,
        passed=passed,
        details=details,
    ))


# ── GATE 5 — RESOLUTION GATE ────────────────────────────────────────────────

def gate_5_resolution_gate(
    pred_ref: str,
    proposed_outcome: str,
    evidence: List[Dict],
    disconfirmation_threshold: str,
    edition: int,
) -> GateRecord:
    """Gate 5 — Resolution Gate (Prediction resolution only).

    A prediction may only be marked CONFIRMED, CONTRADICTED, PARTIAL,
    AMBIGUOUS, or DIRECTIONAL when Gate 5 conditions are met per the
    disconfirmation threshold table.

    No resolution without named evidence meeting the stated threshold.

    evidence: list of dicts with:
      - source: str
      - tier: int
      - description: str
      - meets_threshold: bool
    """
    evidence_meets = any(e.get("meets_threshold", False) for e in evidence)
    has_named_evidence = len(evidence) > 0

    passed = has_named_evidence and evidence_meets
    details = (
        f"{pred_ref} → {proposed_outcome}. "
        + (f"Evidence meets disconfirmation threshold: {disconfirmation_threshold}. PASS."
           if passed
           else f"Insufficient evidence for resolution. "
                f"Threshold: {disconfirmation_threshold}. FAIL — no resolution.")
    )

    return _record_gate(GateRecord(
        gate_id="Gate 5",
        gate_name="Resolution Gate",
        edition=edition,
        passed=passed,
        details=details,
    ))


# ── GATE EXECUTION ORCHESTRATOR ──────────────────────────────────────────────

def execute_pre_analysis_gates(
    carry_forward_facts: List[Dict],
    tier3_claims: List[Dict],
    hypotheses: List[Hypothesis],
    source_clusters: Dict[str, Dict],
    current_date,
    edition: int,
) -> List[GateRecord]:
    """Execute Gates 0.1, 0.2, 0.5 in sequence (pre-analysis stage)."""
    records = []
    records.append(gate_0_1_temporal_currency_check(
        carry_forward_facts, current_date, edition))
    records.append(gate_0_2_source_corroboration_requirement(
        tier3_claims, edition))
    records.append(gate_0_5_cluster_risk_check(
        hypotheses, source_clusters, edition))
    return records


def execute_pre_publication_gates(
    hypotheses: List[Hypothesis],
    h1_analyses: Dict[str, bool],
    correlation_matrix: Dict,
    edition: int,
) -> List[GateRecord]:
    """Execute Gates 0.3 and 0.4 in sequence (pre-publication stage).

    Called after 12-stage pipeline but before PDF build.
    """
    records = []
    records.extend(gate_0_3_incentive_analysis_completion(
        hypotheses, h1_analyses, edition))
    records.extend(gate_0_4_cross_case_consistency_check(
        hypotheses, correlation_matrix, edition))
    return records


def execute_per_edition_gate(
    absence_claims: List[Dict],
    threshold_events: List[Dict],
    edition: int,
) -> GateRecord:
    """Execute Gate 0.6 (per-edition verification)."""
    return gate_0_6_absence_threshold_gate(
        absence_claims, threshold_events, edition)
