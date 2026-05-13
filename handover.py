"""handover.py — Signalghost session handoff generator.

SESSION HANDOFF — MANDATORY AT EACH EDITION CLOSE:
  1. LIVE GMT TIMESTAMP — FIRST ACTION
  2. Full AI-012 pipeline executed (12 stages)
  3-11. All registers updated
  12. Calibration map documented
  13. Prediction log entries updated
  14. Carry-forward facts flagged
  15. New rules added to SYSTEM CHANGE LOG
  16. Next edition mandatory sweep actions
  17-18. Deviation/prediction failures as PLM/PMM
  19. All 10 mandatory PDF items verified
  20. War day verified online
  21. Resolved prediction log updated
  22. Gate 0.2/0.3/0.4 verified executed
"""

import datetime
from typing import Dict, List, Optional
from config import (
    PRODUCT_NAME, CODEBASE_NAME, ARCHITECTURE_VERSION,
    DEVIATION_AUDIT_ITEMS, SESSION_HANDOFF_ITEMS,
    MANDATORY_PDF_ITEMS, PIPELINE_STAGES,
    GATE_EXECUTION_ORDER, HEURISTICS,
    AI_SELF_EXAMINATION_LIMITATION, AI_005_RULE,
)
from timestamping import capture_timestamp, format_session_state_header


def generate_session_state(
    edition: int,
    ts: Dict,
    hypotheses: List[Dict],
    cases: List[Dict],
    predictions_open: List[Dict],
    predictions_resolved: List[Dict],
    brier_data: Dict,
    causal_edges: List[Dict],
    delta_buffer: Dict[str, List[float]],
    change_point_flags: List[Dict],
    correlation_matrix: List[Dict],
    propagation_register: List[Dict],
    ema_band_errors: List[Dict],
    per_band_lookup: List[Dict],
    q_table: List[Dict],
    plm_entries: List[Dict],
    pmm_entries: List[Dict],
    hpt_entries: List[Dict],
    carry_forward_facts: List[Dict],
    gate_records: List[Dict],
    deviation_audit: List[Dict],
    calibration_map: List[Dict],
    pipeline_log: List[str],
    narration: str = "",
) -> str:
    """Generate the full SESSION_STATE markdown for the next edition.

    This is the handover document that governs the next edition's sweep.
    """
    lines = []

    # ── HEADER (lines 1-3 per SESSION_STATE rules) ───────────────────────
    lines.append(f"# {PRODUCT_NAME} SESSION STATE")
    lines.append("")
    lines.append(format_session_state_header(edition, ts))
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── WHAT THIS SYSTEM IS ──────────────────────────────────────────────
    lines.append("## WHAT THIS SYSTEM IS")
    lines.append("")
    lines.append(
        "Signalghost is a highly disciplined forecasting engine, rulebook, and "
        "live geopolitical probability tracker. It is not a simulation, a creative "
        "exercise, or a casual intelligence digest. It is designed to reduce "
        "prediction errors over time, enforce analytical consistency across editions, "
        "and prevent bias and sloppy reasoning through a structured, self-correcting "
        "architecture. Every probability published has passed through a 13-stage "
        "calibration pipeline. Every prediction is falsifiable, tracked, and scored. "
        "The primary objective is Brier score reduction toward elite forecasting "
        "performance (BS < 0.10)."
    )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── PLATFORM ─────────────────────────────────────────────────────────
    lines.append("## PLATFORM")
    lines.append("")
    lines.append(
        f"- Product: {PRODUCT_NAME} · Codebase: {CODEBASE_NAME} · Operator: UK-based, BST (UTC+1)"
    )
    lines.append(
        f"- Architecture: {ARCHITECTURE_VERSION} · GMT primary · "
        f"War day: {ts['war_day']} (as of {ts['date_str']} — system clock verified)"
    )
    lines.append(
        f"- Current: **BS = {brier_data.get('brier_score', 'N/A')} "
        f"(n={brier_data.get('brier_n', 0)}, {brier_data.get('brier_status', 'N/A')})**"
    )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── CURRENT EDITION ──────────────────────────────────────────────────
    lines.append("## CURRENT EDITION")
    lines.append("")
    lines.append(
        f"- Last completed: Edition {edition:03d} · {ts['sweep_descriptor']} · "
        f"{ts['date_str']} · {ts['gmt_str']} ({ts['bst_str']}) — Timestamp verified"
    )
    lines.append(f"- Next: Edition {edition+1:03d} · MANDATORY at sweep open")
    lines.append(f"- Intelligence cutoff: {ts['gmt_str']} (sweep open)")
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── HYPOTHESIS STATE ─────────────────────────────────────────────────
    lines.append(f"## HYPOTHESIS STATE — POST-EDITION {edition:03d}")
    lines.append("")
    current_case = None
    for hyp in sorted(hypotheses, key=lambda h: h.get("hyp_id", "")):
        case = hyp.get("case_id", "")
        if case != current_case:
            lines.append(f"### Case {case}")
            current_case = case
        status = hyp.get("status", "")
        status_str = f" {status}" if status else ""
        lines.append(
            f"- {hyp['hyp_id']}: **{hyp['range_lower']*100:.0f}-"
            f"{hyp['range_upper']*100:.0f}%{status_str} "
            f"(pt est: {hyp['point_estimate']:.2f})**"
        )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── CALIBRATION MAP ──────────────────────────────────────────────────
    lines.append(f"## CALIBRATION MAP — Ed{edition:03d}")
    lines.append("")
    lines.append("|Hypothesis|Prior Range|New Range|Pt Est|Pipeline Stages|Correction Basis|")
    lines.append("|----------|-----------|---------|------|---------------|----------------|")
    for entry in calibration_map:
        lines.append(
            f"|{entry.get('hyp_id','')}|{entry.get('prior_range','')}|"
            f"{entry.get('new_range','')}|{entry.get('point_estimate',0):.2f}|"
            f"{entry.get('pipeline_stages','')}|{entry.get('correction_basis','')}|"
        )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── AI-012 REGISTERS ─────────────────────────────────────────────────
    # Causal Edge Register
    lines.append("## AI-012-1: CAUSAL EDGE REGISTER")
    lines.append("")
    lines.append("|Cause|Effect|Prior|Observed|New|")
    lines.append("|-----|------|-----|--------|---|")
    for edge in causal_edges:
        lines.append(
            f"|{edge.get('cause','')}|{edge.get('effect','')}|"
            f"{edge.get('prior_strength',0):.2f}|{edge.get('observed_signal',0):.1f}|"
            f"{edge.get('new_strength',0):.2f}|"
        )
    lines.append("")

    # Delta Buffer
    lines.append("## AI-012-2: DELTA BUFFER")
    lines.append("")
    for hyp_id, buf in delta_buffer.items():
        lines.append(f"- {hyp_id}: {[round(x,3) for x in buf]}")
    lines.append("")

    # Change Point Flags
    if change_point_flags:
        lines.append("## AI-012-3: CHANGE POINT FLAGS")
        lines.append("")
        for flag in change_point_flags:
            active = "ACTIVE" if flag.get("active") else "RESOLVED"
            lines.append(
                f"- {flag.get('hyp_id','')}: z={flag.get('z_score',0):.2f} "
                f"[{active}] {flag.get('resolution','')}"
            )
        lines.append("")

    # Correlation Matrix
    lines.append("## AI-012-4: CORRELATION MATRIX")
    lines.append("")
    for entry in correlation_matrix:
        lines.append(
            f"- {entry.get('hyp_a','')}/{entry.get('hyp_b','')}: "
            f"{entry.get('effective_correlation',0):.2f}"
        )
    lines.append("")

    # EMA Errors
    lines.append("## AI-012-7: EMA BAND ERRORS")
    lines.append("")
    for entry in ema_band_errors:
        lines.append(
            f"- {entry.get('band','')}: EMA={entry.get('ema_error_updated',0):.3f}"
        )
    lines.append("")

    # Q-Table
    lines.append("## AI-012-6: RL BANDIT Q-TABLE")
    lines.append("")
    for entry in q_table:
        lines.append(
            f"- {entry.get('band','')}: factor={entry.get('current_factor',1.0):.2f}, "
            f"Q={entry.get('q_value',0):.3f}, {entry.get('status','INDICATIVE')}"
        )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── PREDICTION LOG — OPEN ────────────────────────────────────────────
    lines.append("## PREDICTION LOG — OPEN")
    lines.append("")
    for pred in predictions_open:
        lines.append(
            f"- **{pred.get('pred_ref','')}**: {pred.get('flag','')} | "
            f"Window: {pred.get('window','')} | Status: {pred.get('status','')}"
        )
    lines.append("")

    # ── PREDICTION LOG — RESOLVED ────────────────────────────────────────
    lines.append("## PREDICTION LOG — RESOLVED (CUMULATIVE)")
    lines.append("")
    for pred in predictions_resolved:
        lines.append(
            f"- {pred.get('pred_ref','')}: {pred.get('outcome','')} — "
            f"{pred.get('notes','')}"
        )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── CARRY-FORWARD FACTS ──────────────────────────────────────────────
    lines.append("## CARRY-FORWARD FACTS")
    lines.append("")
    for fact in carry_forward_facts:
        lines.append(
            f"- {fact.get('fact','')} | Last verified: {fact.get('last_verified','')} "
            f"| Next: {fact.get('ed_action','')}"
        )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── PLM / PMM ────────────────────────────────────────────────────────
    lines.append("## PLM ENTRIES")
    lines.append("")
    for entry in plm_entries:
        lines.append(f"- {entry.get('entry_id','')}: {entry.get('issue','')}")
    lines.append("")

    lines.append("## PMM ENTRIES")
    lines.append("")
    for entry in pmm_entries:
        lines.append(
            f"- {entry.get('entry_id','')}: {entry.get('pred_ref','')} — "
            f"{entry.get('outcome','')} — {entry.get('what_failed','')}"
        )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── GATE RECORDS ─────────────────────────────────────────────────────
    lines.append("## GATE RECORDS")
    lines.append("")
    for rec in gate_records:
        status = "PASS" if rec.get("passed") else "FAIL"
        lines.append(
            f"- {rec.get('gate_id','')}: [{status}] {rec.get('details','')[:80]}"
        )
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── PIPELINE LOG ─────────────────────────────────────────────────────
    lines.append("## PIPELINE EXECUTION LOG")
    lines.append("")
    for entry in pipeline_log:
        lines.append(f"- {entry}")
    lines.append("")
    lines.append("-----")
    lines.append("")

    # ── BRIER SCORES ─────────────────────────────────────────────────────
    lines.append("## SCORING METRICS")
    lines.append("")
    lines.append(
        f"- Brier Score: {brier_data.get('brier_score','N/A')} "
        f"(n={brier_data.get('brier_n',0)}, {brier_data.get('brier_status','N/A')})"
    )
    lines.append(
        f"- Log Score: {brier_data.get('log_score','INDICATIVE')}"
    )
    lines.append(
        f"- Spherical Score: {brier_data.get('spherical_score','INDICATIVE')}"
    )
    lines.append("")

    # ── FOOTER ───────────────────────────────────────────────────────────
    lines.append("-----")
    lines.append("")
    lines.append(
        f"*SESSION_STATE.md · {PRODUCT_NAME} · {CODEBASE_NAME} · "
        f"Edition {edition:03d} {ts['sweep_descriptor']} Handoff · "
        f"Updated {ts['date_str']} · {ts['gmt_str']} ({ts['bst_str']}) — "
        f"Timestamp verified · {ARCHITECTURE_VERSION} · War Day {ts['war_day']}*"
    )

    return "\n".join(lines)


def write_session_state(content: str, edition: int) -> str:
    """Write SESSION_STATE to file."""
    filename = f"SESSION_STATE_ED{edition:03d}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename
