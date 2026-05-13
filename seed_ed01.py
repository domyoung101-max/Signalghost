"""seed_ed01.py — Signalghost Strategic Reset Seed (Edition 01).

Resets analytical content to Ed01, grounded in live current affairs (06 May 2026).

ARCHITECTURAL INTEGRITY PRESERVED — mirrors calibration_state.py structure:
  Untouched: 13-stage pipeline, 6 gates, CDIT structure, 6+1 heuristics,
             status tag system, three scoring metrics, deviation audit,
             AI-005/006/007/009/010/011/012, all governance rules.
  Reset:     active cases, hypotheses, predictions, Brier history, carry-forward,
             propagation register, EMA tables, HPT, change point flags.
             PMM-001..004 retained as analytical lessons (not data).

Usage: invoked via main.py --init-fresh-ed01.
"""


def SEED_ED01(conn):
    """Seed Edition 01 strategic reset content into the database.

    Architecture-compliant: mirrors calibration_state.py SEED_DATA() structure
    exactly. Same tables, same column orders. Only content differs.
    """
    c = conn.cursor()

    # ── EDITION RECORD — Ed01 ────────────────────────────────────────────
    c.execute("""INSERT OR IGNORE INTO editions
        (edition_number, sweep_descriptor, gmt_timestamp, bst_timestamp,
         war_day, brier_score, n_predictions, architecture_version)
        VALUES (1, 'STRATEGIC RESET', '2300 GMT 06 MAY 2026', '0000 BST 07 MAY 2026',
                68, 0.0, 0, 'v1.3.0-fresh')""")

    # ── HYPOTHESES — Ed01 ────────────────────────────────────────────────
    # Format matches calibration_state.py exactly:
    # (hyp_id, case_id, edition, range_lower, range_upper, point_estimate,
    #  status, pipeline_stages, correction_basis, h4_gap_active,
    #  tier1_denial_active, no_observable_prep_action, independent_chains,
    #  single_cluster_h5)
    hyps = [
        # Case A — US-Iran Memo Trajectory
        ("H-A1", "A", 1, 0.20, 0.35, 0.27, "", "Standard",
         "Initial Ed01 seed. Memo signed within 30 days with substantive concessions.", 0, 0, 0, 2, 0),
        ("H-A2", "A", 1, 0.30, 0.45, 0.37, "", "Standard",
         "Initial Ed01 seed. Memo signed but soft (Hormuz-first, nuclear deferred).", 0, 0, 0, 2, 0),
        ("H-A3", "A", 1, 0.25, 0.40, 0.32, "", "Standard",
         "Initial Ed01 seed. Track collapses; Project Freedom or kinetic resumes.", 0, 0, 0, 2, 0),

        # Case B — Iran Nuclear Stockpile Disposition
        ("H-B1", "B", 1, 0.10, 0.22, 0.16, "", "Standard",
         "Initial Ed01 seed. Stockpile shipped out of Iran.", 0, 1, 1, 2, 0),
        ("H-B2", "B", 1, 0.30, 0.45, 0.37, "", "Standard",
         "Initial Ed01 seed. Stockpile remains in Iran, sealed/monitored.", 0, 0, 0, 2, 0),
        ("H-B3", "B", 1, 0.40, 0.55, 0.47, "", "Standard",
         "Initial Ed01 seed. Stockpile status unresolved at memo signing.", 0, 0, 0, 2, 0),

        # Case C — Lebanon-Israel Ceasefire Durability
        ("H-C1", "C", 1, 0.15, 0.28, 0.22, "", "Standard",
         "Initial Ed01 seed. Ceasefire holds and converts to direct peace track.", 0, 0, 0, 2, 0),
        ("H-C2", "C", 1, 0.35, 0.50, 0.42, "", "Standard",
         "Initial Ed01 seed. Ceasefire fragmented but no formal collapse.", 1, 0, 0, 2, 0),
        ("H-C3", "C", 1, 0.25, 0.40, 0.32, "", "Standard",
         "Initial Ed01 seed. Major IDF operation north of Litani / formal collapse.", 0, 0, 0, 2, 0),

        # Case D — Trump-Xi Beijing Summit (Iran framing)
        ("H-D1", "D", 1, 0.10, 0.22, 0.16, "", "Standard",
         "Initial Ed01 seed. Beijing endorses US-Iran framework explicitly.", 0, 0, 0, 2, 0),
        ("H-D2", "D", 1, 0.45, 0.62, 0.53, "", "Standard",
         "Initial Ed01 seed. Beijing offers tacit non-opposition.", 0, 0, 0, 2, 0),
        ("H-D3", "D", 1, 0.20, 0.35, 0.27, "", "Standard",
         "Initial Ed01 seed. Beijing positions against framework / for veto.", 0, 0, 0, 2, 0),

        # Case E — IRGC/SNSC Constraint on Diplomatic Track
        ("H-E1", "E", 1, 0.30, 0.48, 0.39, "", "Standard",
         "Initial Ed01 seed. IRGC/SNSC publicly back Araghchi posture.", 0, 0, 0, 2, 0),
        ("H-E2", "E", 1, 0.35, 0.50, 0.42, "", "Standard",
         "Initial Ed01 seed. IRGC/SNSC conditional support, autonomy on Hormuz.", 1, 0, 0, 2, 0),
        ("H-E3", "E", 1, 0.12, 0.25, 0.18, "", "Standard",
         "Initial Ed01 seed. IRGC/SNSC repudiate Araghchi framework.", 0, 0, 0, 2, 0),
    ]
    for h in hyps:
        c.execute("""INSERT OR IGNORE INTO hypotheses
            (hyp_id, case_id, edition, range_lower, range_upper, point_estimate,
             status, pipeline_stages, correction_basis, h4_gap_active,
             tier1_denial_active, no_observable_prep_action, independent_chains,
             single_cluster_h5)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", h)

    # ── CAUSAL EDGE REGISTER — Ed01 (fresh, minimal seed) ────────────────
    # Five edges grounded in current evidence. Pipeline will accumulate more.
    edges = [
        ("Trump pauses Project Freedom", "H-A1 supported (memo signed)", 0.55, 1.0, 0.66, 1),
        ("Iranian uranium remains in country", "H-B1 suppressed", 0.70, 1.0, 0.78, 1),
        ("IDF maintains Yellow Line operations", "H-C1 suppressed", 0.60, 1.0, 0.70, 1),
        ("Trump-Xi summit confirmed 14-15 May", "H-D2 supported (tacit non-opposition baseline)", 0.50, 1.0, 0.62, 1),
        ("Salami publicly contradicts Foreign Ministry", "H-E3 elevated", 0.20, 0.0, 0.14, 1),
    ]
    for e in edges:
        c.execute("""INSERT OR IGNORE INTO causal_edges
            (cause, effect, prior_strength, observed_signal, new_strength, edition)
            VALUES (?,?,?,?,?,?)""", e)

    # ── DELTA BUFFER — Ed01 (empty: no prior delta history) ──────────────
    # Pipeline accumulates from Ed02 onward.

    # ── CHANGE POINT FLAGS — Ed01 (none yet) ─────────────────────────────
    # Pipeline accumulates from Ed02 onward.

    # ── CORRELATION MATRIX — Ed01 (initial estimates, n=0 → max shrinkage) ──
    # Architecture: shrinkage_factor = 1.0 means full neutralisation when n=0.
    # Initial correlations are theoretical priors; effective_correlation = 0
    # because shrinkage strips them entirely until data accumulates.
    corr_pairs = [
        # Case A track outcomes are anti-correlated within case
        ("H-A1", "H-A3", -0.50),
        ("H-A2", "H-A3", -0.30),
        # Memo success (A1) supports stockpile shipment (B1)
        ("H-A1", "H-B1",  0.45),
        # Memo collapse (A3) elevates IRGC repudiation (E3)
        ("H-A3", "H-E3",  0.40),
        # Lebanon collapse (C3) correlates with diplomatic track collapse (A3)
        ("H-C3", "H-A3",  0.35),
        # Beijing endorsement (D1) supports memo (A1)
        ("H-D1", "H-A1",  0.30),
        # IRGC backing (E1) supports memo signing (A1)
        ("H-E1", "H-A1",  0.40),
    ]
    for ha, hb, eff in corr_pairs:
        # n=0 at Ed01 — full shrinkage, effective_correlation = 0 until data
        c.execute("""INSERT OR IGNORE INTO correlation_matrix
            (hyp_a, hyp_b, raw_correlation, shrinkage_factor,
             effective_correlation, n, edition)
            VALUES (?,?,?,1.00,0.0,0,1)""", (ha, hb, eff))

    # ── PROPAGATION REGISTER — Ed01 (fresh) ──────────────────────────────
    # Triggers configured but no historical net adjustments.
    props = [
        ("H-A1", "UP",   "H-B1",  0.04, "H-A1 rises > 0.05 (memo signed → stockpile signal)"),
        ("H-A1", "DOWN", "H-A3",  0.03, "H-A1 falls > 0.05 (memo trajectory weakens)"),
        ("H-A3", "UP",   "H-E3",  0.04, "H-A3 rises > 0.05 (collapse → IRGC repudiation risk)"),
        ("H-D1", "UP",   "H-A1",  0.03, "H-D1 rises > 0.05 (Beijing endorsement → memo support)"),
        ("H-E3", "UP",   "H-A3",  0.05, "H-E3 rises > 0.05 (IRGC repudiation → track collapse)"),
        ("H-C3", "UP",   "H-A3",  0.04, "H-C3 rises > 0.05 (Lebanon collapse → diplomatic track erodes)"),
        ("H-E1", "UP",   "H-A1",  0.03, "H-E1 rises > 0.05 (IRGC backing → memo support)"),
    ]
    for p in props:
        c.execute("""INSERT OR IGNORE INTO propagation_register
            (trigger_hyp, direction, downstream_hyp, adjustment, condition_text)
            VALUES (?,?,?,?,?)""", p)

    # ── EMA BAND ERRORS — Ed01 (reset to neutral) ────────────────────────
    # All bands at zero error, awaiting first edition's data.
    ema_rows = [
        ("0-10%",   0.0, 0.0, 0.0, 1),
        ("10-20%",  0.0, 0.0, 0.0, 1),
        ("20-30%",  0.0, 0.0, 0.0, 1),
        ("30-40%",  0.0, 0.0, 0.0, 1),
        ("40-60%",  0.0, 0.0, 0.0, 1),
        ("60-70%",  0.0, 0.0, 0.0, 1),
        ("70-80%",  0.0, 0.0, 0.0, 1),
        ("80-90%",  0.0, 0.0, 0.0, 1),
        ("90-100%", 0.0, 0.0, 0.0, 1),
    ]
    for row in ema_rows:
        c.execute("""INSERT OR IGNORE INTO ema_band_errors
            (band, ema_error_prior, current_error, ema_error_updated, edition)
            VALUES (?,?,?,?,?)""", row)

    # ── PER-BAND LOOKUP TABLE — Ed01 (empty / NO DATA across all bands) ──
    lookup_rows = [
        ("0-10%",   0, 0, None, 0.0, 0.0, "NO DATA", 1),
        ("10-20%",  0, 0, None, 0.0, 0.0, "NO DATA", 1),
        ("20-30%",  0, 0, None, 0.0, 0.0, "NO DATA", 1),
        ("30-40%",  0, 0, None, 0.0, 0.0, "NO DATA", 1),
        ("40-60%",  0, 0, None, 0.0, 0.0, "NO DATA", 1),
        ("60-70%",  0, 0, None, 0.0, 0.0, "NO DATA", 1),
        ("70-80%",  0, 0, None, 0.0, 0.0, "NO DATA", 1),
        ("80-90%",  0, 0, None, 0.0, 0.0, "NO DATA", 1),
        ("90-100%", 0, 0, None, 0.0, 0.0, "NO DATA", 1),
    ]
    for row in lookup_rows:
        c.execute("""INSERT OR IGNORE INTO per_band_lookup
            (band, pred_freq, obs_freq, obs_rate, ema_error, adjustment,
             min_n_status, edition)
            VALUES (?,?,?,?,?,?,?,?)""", row)

    # ── RL BANDIT Q-TABLE — Ed01 (neutral start) ─────────────────────────
    q_rows = [
        ("0-10%",   1.00, 0.000, "NO DATA", 1),
        ("10-20%",  1.00, 0.000, "NO DATA", 1),
        ("20-30%",  1.00, 0.000, "NO DATA", 1),
        ("30-40%",  1.00, 0.000, "NO DATA", 1),
        ("40-60%",  1.00, 0.000, "NO DATA", 1),
        ("60-70%",  1.00, 0.000, "NO DATA", 1),
        ("70-80%",  1.00, 0.000, "NO DATA", 1),
        ("80-90%",  1.00, 0.000, "NO DATA", 1),
        ("90-100%", 1.00, 0.000, "NO DATA", 1),
    ]
    for row in q_rows:
        c.execute("""INSERT OR IGNORE INTO rl_q_table
            (band, current_factor, q_value, status, edition)
            VALUES (?,?,?,?,?)""", row)

    # ── BRIER TABLE — Ed01 (empty) ────────────────────────────────────────
    # No resolutions yet. First entries written when Ed02+ resolves predictions.

    # ── PLM ENTRIES (carry-forward analytical record + reset entry) ──────
    plm_entries = [
        ("PLM-001-Ed01", "Ed01",
         "Strategic reset from Ed034 to Ed01 fresh. Architecture (v1.3.0) "
         "preserved unchanged. Reset reason: stale case architecture and "
         "contaminated calibration history post-cutover; cases no longer "
         "reflected operational reality (Project Freedom pause, 30-day memo "
         "trajectory, Trump-Xi summit window). Brier reset, EMA/per-band "
         "tables reset, HPT cleared, carry-forward facts cleared, propagation "
         "register reseeded. PMM-001..004 retained as analytical lessons. "
         "Operator: Dominic Young, 06 May 2026."),
    ]
    for entry in plm_entries:
        c.execute("""INSERT OR IGNORE INTO plm_entries
            (entry_id, edition, issue) VALUES (?,?,?)""", entry)

    # ── PMM ENTRIES (retained from Ed033 — analytical lessons, not data) ──
    pmm_entries = [
        ("PMM-001", "PRED-012-B (legacy)", "CONTRADICTED",
         "Named-source prediction without bilateral incentive analysis.",
         "Failure to apply H1 incentive mismatch heuristic before publication.",
         "Gate 0.3 mandatory for hypotheses above 60% resting on stated intent.",
         "H1 (Incentive Mismatch)"),
        ("PMM-002", "PRED-026-E (legacy)", "CONTRADICTED",
         "First Yanbu strike carried PENDING through expiring window.",
         "Threshold event treated as ongoing instead of resolved at window close.",
         "Gate 5 enforces resolution at window expiry.",
         "Threshold management"),
        ("PMM-003", "PRED-022-A through PRED-029-A x6 (legacy)", "CONTRADICTED",
         "H-A1 at 72-82% on Iranian-source cluster; six sequential CONTRADICTED "
         "outcomes from same overconfidence pattern.",
         "Tier 1 IRNA + Tier 3 Tasnim/Mehr/WANA do not constitute independent "
         "confirmation when all trace to single-source state messaging.",
         "AI-010 single-cluster H5 discount; cluster detection in feed_analyzer.",
         "H5 (Structural Contradiction) + H6 (Suppressed Intersection)"),
        ("PMM-004", "PRED-031-A (legacy)", "CONTRADICTED",
         "H-A1 at 72-82% with active Tier 1 Iranian denial.",
         "Iranian Foreign Ministry denial of US claim ignored when probability "
         "set high; H4 narrative-outcome gap not formally activated.",
         "PMM-004 mandatory rule check in calibration_pipeline: -10pp adjustment "
         "when H4 gap + Tier 1 denial + no prep action above 60%.",
         "H4 (Narrative vs Outcome Gap)"),
    ]
    for entry in pmm_entries:
        c.execute("""INSERT OR IGNORE INTO pmm_entries
            (entry_id, pred_ref, outcome, what_failed, why, system_change, heuristic)
            VALUES (?,?,?,?,?,?,?)""", entry)

    # ── CASES — Ed01 ─────────────────────────────────────────────────────
    cases = [
        ("A", "US-Iran Memo Trajectory", "DEVELOPING", "MEDIUM",
         "Trump pauses Project Freedom; 14-point response via Pakistan.", 1),
        ("B", "Iran Nuclear Stockpile Disposition", "DEVELOPING", "MEDIUM",
         "Uranium handover provision contested; sequencing dispute.", 1),
        ("C", "Lebanon-Israel Ceasefire Durability", "ESCALATING-PROVISIONAL", "MEDIUM",
         "Yellow Line operations active; 14 May extension threshold.", 1),
        ("D", "Trump-Xi Beijing Summit (Iran framing)", "DEVELOPING", "MEDIUM",
         "Summit 14-15 May; Araghchi-Wang Yi precursor meetings.", 1),
        ("E", "IRGC/SNSC Constraint on Diplomatic Track", "WATCH", "MEDIUM",
         "Salami / Ghalibaf positioning vs Araghchi/Pezeshkian.", 1),
    ]
    for cs in cases:
        c.execute("""INSERT OR IGNORE INTO cases
            (case_id, title, tag, confidence, notes, edition)
            VALUES (?,?,?,?,?,?)""", cs)

    # ── HPT ENTRIES — Ed01 (empty: first row written by Ed01 narration) ──
    # No prior heuristic dominance to record. Pipeline will populate.

    # ── SYSTEM CHANGE LOG (carry-forward from config) ────────────────────
    try:
        from config import SYSTEM_CHANGE_LOG_ENTRIES
        for entry in SYSTEM_CHANGE_LOG_ENTRIES:
            c.execute("""INSERT OR IGNORE INTO system_change_log
                (entry_id, summary, in_force) VALUES (?,?,?)""",
                (entry["entry"], entry["summary"], entry["in_force"]))
    except (ImportError, AttributeError):
        pass

    # ── PREDICTIONS OPEN — Ed01 (5 fresh predictions, one per case) ──────
    open_preds = [
        ("PRED-01-A", "Iran-US framework memo signed within 30 days",
         "Before 5 Jun 2026", "OPENED Ed01",
         "30-day window expires without signed memo OR Trump publicly rejects "
         "Iranian draft OR Araghchi withdraws from Pakistan channel = CONTRADICTED"),
        ("PRED-01-B", "Iranian uranium stockpile shipped out of country",
         "Before 5 Jun 2026", "OPENED Ed01",
         "Memo signed without uranium-export provision OR IAEA confirms "
         "uranium remains in Iran post-memo OR Khamenei publicly rejects "
         "export = CONTRADICTED"),
        ("PRED-01-C", "Lebanon ceasefire holds through 14 May extension",
         "Before 14 May 2026", "OPENED Ed01",
         "IDF major operation north of Litani River OR Hezbollah confirmed "
         "barrage 100+ rockets at Israeli territory OR US announces ceasefire "
         "collapse = CONTRADICTED"),
        ("PRED-01-D", "Trump-Xi Beijing summit produces public Iran-framework reference",
         "Before 16 May 2026", "OPENED Ed01",
         "Summit happens but joint statement omits Iran OR Beijing publicly "
         "opposes US framework OR summit deferred past 16 May = CONTRADICTED"),
        ("PRED-01-E", "IRGC/SNSC publicly endorses Araghchi diplomatic posture",
         "Before 5 Jun 2026", "OPENED Ed01",
         "Salami or Ghalibaf publicly contradict Araghchi framework OR "
         "SNSC issues statement reasserting blockade-lift precondition OR "
         "Khamenei advisor repudiates Pakistan channel = CONTRADICTED"),
    ]
    for p in open_preds:
        c.execute("""INSERT OR IGNORE INTO predictions_open
            (pred_ref, flag, window, status, disconfirmation)
            VALUES (?,?,?,?,?)""", p)

    # Set fi values on predictions_open via UPDATE (column exists in schema)
    fi_values = [
        ("PRED-01-A", 0.27),  # H-A1 point estimate
        ("PRED-01-B", 0.16),  # H-B1 point estimate
        ("PRED-01-C", 0.42),  # H-C1 + H-C2 (ceasefire holds in either clean or fragmented form)
        ("PRED-01-D", 0.53),  # H-D2 point estimate (most likely Beijing posture)
        ("PRED-01-E", 0.39),  # H-E1 point estimate
    ]
    for pred_ref, fi in fi_values:
        c.execute("""UPDATE predictions_open SET fi = ? WHERE pred_ref = ?""",
                  (fi, pred_ref))

    # ── PREDICTIONS RESOLVED — Ed01 (empty) ──────────────────────────────
    # No resolutions yet. Cumulative log starts fresh.

    # ── DISCONFIRMATION THRESHOLDS — Ed01 ────────────────────────────────
    thresholds = [
        # Case A
        ("A", "Memo signed with substantive concessions from both sides",
         "PRED-01-A CONFIRMED. H-A1 to 60-75%."),
        ("A", "Trump cancels Pakistan channel OR resumes Project Freedom kinetically",
         "PRED-01-A CONTRADICTED. H-A3 dominance."),
        ("A", "Iranian withdrawal from negotiations OR draft language shows irreconcilable positions",
         "H-A1 falls to 10-20%. H-A3 to 50-65%."),
        ("A", "Direct Trump-Pezeshkian phone call",
         "H-A1 rises to 50-65%."),

        # Case B
        ("B", "IAEA confirms uranium transfer to third-country custody",
         "PRED-01-B CONFIRMED. H-B1 to CONFIRMED."),
        ("B", "Atomic Energy Organization of Iran publicly rejects export",
         "H-B1 falls to 5-12%. H-B3 dominance."),
        ("B", "Memo signed but uranium provision absent or deferred indefinitely",
         "H-B1 falls to 5-12%. H-B2 or H-B3 dominance."),
        ("B", "Russia or China named as third-party custodian",
         "H-B1 rises to 35-50%."),

        # Case C
        ("C", "Ceasefire extended formally beyond 14 May with Hezbollah quiet response",
         "PRED-01-C CONFIRMED. H-C1 to 40-55%."),
        ("C", "IDF crosses Litani in major operation OR Hezbollah barrage 100+ rockets",
         "Gate 0.6 BREACHED. PRED-01-C CONTRADICTED. H-C3 CONFIRMED."),
        ("C", "Lebanese government publicly withdraws from talks OR Aoun resigns",
         "H-C1 falls to 5-15%."),
        ("C", "UNIFIL withdrawal completed",
         "Monitoring collapses. H-C2 rises sharply."),

        # Case D
        ("D", "Joint Trump-Xi statement explicitly endorses US-Iran framework",
         "PRED-01-D CONFIRMED. H-D1 CONFIRMED."),
        ("D", "China publicly opposes framework OR signals UNSC veto",
         "H-D3 to 50-65%."),
        ("D", "Summit deferred past 16 May without rescheduling",
         "PRED-01-D CONTRADICTED. H-D3 dominance."),
        ("D", "Beijing offers economic guarantee for Iran post-memo",
         "H-D2 rises to 60-75%."),

        # Case E
        ("E", "Khamenei or SNSC public statement endorsing Araghchi posture",
         "PRED-01-E CONFIRMED. H-E1 to 60-75%."),
        ("E", "Salami publicly contradicts Foreign Ministry on Hormuz / blockade-lift",
         "H-E3 to 50-65%. H-A1 propagation -0.05."),
        ("E", "IRGC announces new vessel seizures or expanded toll mechanism after memo signed",
         "Gate 0.6 BREACHED. H-E3 CONFIRMED."),
        ("E", "Jalili named as alternate Iranian negotiating lead",
         "H-E3 rises to 35-50%."),
    ]
    for t in thresholds:
        c.execute("""INSERT OR IGNORE INTO disconfirmation_thresholds
            (case_id, threshold, effect) VALUES (?,?,?)""", t)

    # ── CARRY-FORWARD FACTS — Ed01 (empty: first edition has no carry-fwd) ──
    # Pipeline accumulates from Ed02 onward.

    conn.commit()
