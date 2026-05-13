"""calibration_state.py — Signalghost Ed033 carry-forward seed data.

Contains all named register values from the SESSION_STATE Ed033 Evening Sweep
that must be loaded into SQLite on first run.  This is the companion .py
data layer referenced in the SESSION_STATE workflow section.
"""


def SEED_DATA(conn):
    """Seed all carry-forward data from Ed033 SESSION_STATE into the database."""
    c = conn.cursor()

    # ── EDITION RECORD ───────────────────────────────────────────────────
    c.execute("""INSERT OR IGNORE INTO editions
        (edition_number, sweep_descriptor, gmt_timestamp, bst_timestamp,
         war_day, brier_score, n_predictions, architecture_version)
        VALUES (33, 'EVENING SWEEP', '1810 GMT 25 APRIL 2026', '1910 BST',
                57, 0.2151, 15, 'v1.3.0')""")

    # ── HYPOTHESES — Ed033 ───────────────────────────────────────────────
    hyps = [
        ("H-A1", "A", 33, 0.50, 0.62, 0.56, "", "S2 S3 S5 S7 S9 S11", "PRED-031-A CONTRADICTED", 1, 1, 1, 2, 0),
        ("H-A2", "A", 33, 0.05, 0.10, 0.07, "", "S3", "Graham military signal", 0, 0, 0, 2, 0),
        ("H-A3", "A", 33, 0.75, 0.85, 0.80, "NEAR-CONFIRMED PROVISIONAL", "Standard", "Ceasefire still in force", 0, 0, 0, 2, 0),
        ("H-B1", "B", 33, 0.12, 0.22, 0.17, "", "S7 S9 S11", "Mine clearance 6-month floor", 0, 0, 0, 2, 0),
        ("H-B2", "B", 33, 0.22, 0.35, 0.29, "", "Standard", "No new kinetic", 0, 0, 0, 2, 0),
        ("H-B3", "B", 33, 0.38, 0.50, 0.44, "PARTIAL", "Standard", "Germany Fulda deploying", 0, 0, 0, 2, 0),
        ("H-C1", "C", 33, 0.62, 0.75, 0.68, "PROVISIONAL", "S3 S5 S7 S10 S11", "Netanyahu strike order", 0, 0, 0, 2, 0),
        ("H-C2", "C", 33, 0.15, 0.24, 0.20, "", "S3", "Netanyahu + Hezbollah escalation", 0, 0, 0, 2, 0),
        ("H-C3", "C", 33, 0.14, 0.22, 0.18, "", "S3", "Kfar Giladi barrage approaching Gate 0.6", 0, 0, 0, 2, 0),
        ("H-D1", "D", 33, 0.00, 0.00, 0.00, "CONTRADICTED", "N/A", "Established", 0, 0, 0, 2, 0),
        ("H-D2", "D", 33, 0.97, 0.99, 0.98, "CONFIRMED", "Standard", "ICICI closed. GL U lapsed.", 0, 0, 0, 2, 0),
        ("H-D3", "D", 33, 0.02, 0.05, 0.04, "", "S3", "No OFAC enforcement", 0, 0, 0, 2, 0),
        ("H-E1", "E", 33, 0.40, 0.53, 0.47, "", "S7 S11", "Dual propagation triggered", 0, 0, 0, 2, 0),
        ("H-E2", "E", 33, 0.32, 0.46, 0.38, "", "S7", "Mirror of H-E1", 0, 0, 0, 2, 0),
        ("H-E3", "E", 33, 0.12, 0.18, 0.15, "", "Standard", "No new GCC infrastructure strike", 0, 0, 0, 2, 0),
    ]
    for h in hyps:
        c.execute("""INSERT OR IGNORE INTO hypotheses
            (hyp_id, case_id, edition, range_lower, range_upper, point_estimate,
             status, pipeline_stages, correction_basis, h4_gap_active,
             tier1_denial_active, no_observable_prep_action, independent_chains,
             single_cluster_h5)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", h)

    # ── CAUSAL EDGE REGISTER — Ed033 ─────────────────────────────────────
    edges = [
        ("US blockade continues", "Iran closes Hormuz", 0.90, 1.0, 0.93, 33),
        ("Hormuz closed", "H-B1 suppressed", 0.86, 1.0, 0.90, 33),
        ("Lebanon ceasefire holds", "H-E1 suppressed", 0.79, 0.5, 0.70, 33),
        ("Talks imminent", "H-B2 suppressed", 0.65, 0.0, 0.46, 33),
        ("Ghalibaf absent / stepped down", "H5 partially resolved", 0.30, 1.0, 0.51, 33),
        ("GL U lapsed", "ICICI channel closed", 0.72, 1.0, 0.80, 33),
        ("Mine clearance 6-month floor", "H-B1 structurally capped", 0.00, 1.0, 0.30, 33),
        ("Oman channel active", "H-A1/H-B1 partial signal", 0.00, 0.5, 0.15, 33),
        ("Hezbollah barrage Kfar Giladi", "H-C2/H-C3 risk elevated", 0.30, 1.0, 0.51, 33),
        ("Talks deadlock", "H-B1 suppression entrenched", 0.50, 1.0, 0.65, 33),
    ]
    for e in edges:
        c.execute("""INSERT OR IGNORE INTO causal_edges
            (cause, effect, prior_strength, observed_signal, new_strength, edition)
            VALUES (?,?,?,?,?,?)""", e)

    # ── DELTA BUFFER — Ed033 ─────────────────────────────────────────────
    delta_data = [
        ("H-A1", [(29,0.00),(30,-0.07),(31,0.10),(32,0.05),(33,-0.21)]),
        ("H-B1", [(29,-0.25),(30,-0.13),(31,0.06),(32,0.04),(33,-0.06)]),
        ("H-C1", [(29,0.06),(30,0.12),(31,0.00),(32,-0.02),(33,-0.07)]),
        ("H-E1", [(29,-0.07),(30,0.04),(31,0.06),(32,-0.03),(33,-0.045)]),
        ("H-E2", [(29,0.07),(30,-0.04),(31,-0.07),(32,0.03),(33,0.045)]),
        ("H-C2", [(29,0.00),(30,0.00),(31,0.02),(32,0.03),(33,0.05)]),
        ("H-C3", [(29,0.00),(30,0.00),(31,0.02),(32,0.02),(33,0.04)]),
    ]
    for hyp_id, entries in delta_data:
        for ed, dp in entries:
            c.execute("""INSERT OR IGNORE INTO delta_buffer
                (hyp_id, edition, delta_p) VALUES (?,?,?)""", (hyp_id, ed, dp))

    # ── CHANGE POINT FLAGS — Ed033 ───────────────────────────────────────
    c.execute("""INSERT OR IGNORE INTO change_point_flags
        (hyp_id, edition, delta_p, mean_delta, std_delta, z_score,
         flag_raised, resolution, active)
        VALUES ('H-A1', 33, -0.21, -0.026, 0.117, -1.57, 1,
                'Evidentially justified: PRED-031-A CONTRADICTED', 0)""")
    c.execute("""INSERT OR IGNORE INTO change_point_flags
        (hyp_id, edition, delta_p, mean_delta, std_delta, z_score,
         flag_raised, resolution, active)
        VALUES ('H-C1', 33, -0.07, 0.018, 0.068, -2.45, 1,
                'Evidentially justified: Netanyahu strike order + Hezbollah Kfar Giladi barrage', 1)""")

    # ── CORRELATION MATRIX — Ed033 (shrinkage n=7, factor=0.35) ──────────
    corr_pairs = [
        ("H-A1","H-B1",0.38), ("H-A1","H-C1",0.29), ("H-A1","H-E1",0.27), ("H-A1","H-E2",-0.27),
        ("H-B1","H-C1",0.17), ("H-B1","H-E1",0.20), ("H-B1","H-E2",-0.20),
        ("H-C1","H-E1",0.49), ("H-C1","H-E2",-0.49),
        ("H-E1","H-E2",-0.98),
    ]
    for ha, hb, eff in corr_pairs:
        c.execute("""INSERT OR IGNORE INTO correlation_matrix
            (hyp_a, hyp_b, raw_correlation, shrinkage_factor,
             effective_correlation, n, edition)
            VALUES (?,?,?,0.35,?,7,33)""", (ha, hb, eff/0.35, eff))

    # ── PROPAGATION REGISTER — Ed033 ─────────────────────────────────────
    props = [
        ("H-B2","UP","H-E2",0.03,"H-B2 rises > 0.05"),
        ("H-C3","UP","H-E2",0.08,"H-C3 rises > 0.05"),
        ("H-A1","UP","H-B1",0.04,"H-A1 rises > 0.05"),
        ("H-A1","DOWN","H-B1",-0.04,"H-A1 falls > 0.05"),
        ("H-A1","DOWN","H-A2",0.03,"H-A1 falls > 0.05"),
        ("H-C1","DOWN","H-E2",0.05,"H-C1 falls > 0.05"),
        ("H-B1","UP","H-A1",0.02,"H-B1 rises > 0.05"),
    ]
    for p in props:
        c.execute("""INSERT OR IGNORE INTO propagation_register
            (trigger_hyp, direction, downstream_hyp, adjustment, condition_text)
            VALUES (?,?,?,?,?)""", p)

    # ── EMA BAND ERRORS — Ed033 ──────────────────────────────────────────
    ema_rows = [
        ("0-10%", -0.045, 0.00, -0.045, 33),
        ("70-80%", -0.077, -0.77, -0.146, 33),
        ("90-100%", 0.045, 0.00, 0.045, 33),
    ]
    for row in ema_rows:
        c.execute("""INSERT OR IGNORE INTO ema_band_errors
            (band, ema_error_prior, current_error, ema_error_updated, edition)
            VALUES (?,?,?,?,?)""", row)

    # ── PER-BAND LOOKUP TABLE — Ed033 ────────────────────────────────────
    lookup_rows = [
        ("0-10%",  2, 0, 0.00, -0.045, -0.03, "INDICATIVE", 33),
        ("10-20%", 0, 0, None, 0.000,   0.00, "NO DATA", 33),
        ("20-30%", 1, 0, 0.00, -0.040, -0.03, "INDICATIVE", 33),
        ("30-40%", 0, 0, None, 0.000,   0.00, "NO DATA", 33),
        ("40-60%", 0, 0, None, 0.000,   0.00, "NO DATA", 33),
        ("60-70%", 2, 2, 1.00, 0.045,   0.03, "INDICATIVE", 33),
        ("70-80%", 7, 0, 0.00, -0.146, -0.03, "INDICATIVE", 33),
        ("90-100%",3, 3, 1.00, 0.045,   0.03, "INDICATIVE", 33),
    ]
    for row in lookup_rows:
        c.execute("""INSERT OR IGNORE INTO per_band_lookup
            (band, pred_freq, obs_freq, obs_rate, ema_error, adjustment,
             min_n_status, edition)
            VALUES (?,?,?,?,?,?,?,?)""", row)

    # ── RL BANDIT Q-TABLE — Ed033 ────────────────────────────────────────
    q_rows = [
        ("0-10%",  1.00,  0.000, "INDICATIVE", 33),
        ("10-20%", 1.00,  0.000, "INDICATIVE", 33),
        ("20-30%", 0.95, -0.040, "INDICATIVE", 33),
        ("40-60%", 1.00,  0.000, "INDICATIVE", 33),
        ("70-80%", 0.88, -0.146, "INDICATIVE", 33),
        ("90-100%",1.02, -0.003, "INDICATIVE", 33),
    ]
    for row in q_rows:
        c.execute("""INSERT OR IGNORE INTO rl_q_table
            (band, current_factor, q_value, status, edition)
            VALUES (?,?,?,?,?)""", row)

    # ── BRIER TABLE — cumulative through Ed033 ───────────────────────────
    brier_rows = [
        ("PRED-022-C",     0.95, 1.0, 0.0025,  28, "GL U lapse CONFIRMED"),
        ("PRED-023-B",     0.95, 1.0, 0.0025,  28, "GL U lapse CONFIRMED"),
        ("PRED-026-D",     0.95, 1.0, 0.0025,  28, "GL U lapse CONFIRMED"),
        ("PRED-027-B",     0.55, 0.0, 0.3025,  29, "Iran Hormuz closure CONTRADICTED"),
        ("PRED-028-B",     0.55, 0.0, 0.3025,  29, "Same basis"),
        ("PRED-026-E",     0.65, 0.0, 0.4225,  27, "First Yanbu strike PMM-002"),
        ("PRED-025-C",     0.70, 0.5, 0.0400,  28, "Paris Summit PARTIAL"),
        ("PRED-026-B",     0.70, 0.5, 0.0400,  28, "Northwood PARTIAL"),
        ("PRED-022-A-x1",  0.77, 0.0, 0.5929,  30, "PMM-003 x1"),
        ("PRED-023-A-x1",  0.77, 0.0, 0.5929,  30, "PMM-003 x2"),
        ("PRED-024-A-x1",  0.77, 0.0, 0.5929,  30, "PMM-003 x3"),
        ("PRED-025-A-x1",  0.77, 0.0, 0.5929,  30, "PMM-003 x4"),
        ("PRED-028-A-x1",  0.77, 0.0, 0.5929,  30, "PMM-003 x5"),
        ("PRED-029-A-x1",  0.77, 0.0, 0.5929,  30, "PMM-003 x6"),
        ("PRED-031-A",     0.77, 0.0, 0.5929,  33, "CONTRADICTED. PMM-004."),
    ]
    for row in brier_rows:
        c.execute("""INSERT OR IGNORE INTO brier_table
            (pred_ref, fi, oi, squared_error, edition, notes)
            VALUES (?,?,?,?,?,?)""", row)

    # ── PLM ENTRIES ──────────────────────────────────────────────────────
    from config import PLM_ENTRIES
    for entry in PLM_ENTRIES:
        c.execute("""INSERT OR IGNORE INTO plm_entries
            (entry_id, edition, issue) VALUES (?,?,?)""",
            (entry["entry"], entry["edition"], entry["issue"]))

    # ── PMM ENTRIES ──────────────────────────────────────────────────────
    from config import PMM_ENTRIES
    for entry in PMM_ENTRIES:
        c.execute("""INSERT OR IGNORE INTO pmm_entries
            (entry_id, pred_ref, outcome, what_failed, why, system_change, heuristic)
            VALUES (?,?,?,?,?,?,?)""",
            (entry["entry"], entry["pred_ref"], entry["outcome"],
             entry["what_failed"], entry["why"], entry["system_change"],
             entry["heuristic"]))

    # ── CASES — Ed033 ────────────────────────────────────────────────────
    cases = [
        ("A", "TALKS DEADLOCKED", "ESCALATING", "MEDIUM", "Trump Cancelled. Araghchi Muscat.", 33),
        ("B", "Hormuz CLOSED / Mine Clearance 6 Months", "ESCALATING", "HIGH", "Dual blockade unchanged.", 33),
        ("C", "ESCALATING — Netanyahu Strike Order", "ESCALATING", "MEDIUM", "Change Point Flag Active.", 33),
        ("D", "GL U LAPSED", "DEVELOPING", "HIGH", "IPGL Divestment Proceeding.", 33),
        ("E", "Double Suppressor / Dual Propagation", "ESCALATING", "MEDIUM", "Day 18+ No Yanbu Strike.", 33),
    ]
    for cs in cases:
        c.execute("""INSERT OR IGNORE INTO cases
            (case_id, title, tag, confidence, notes, edition)
            VALUES (?,?,?,?,?,?)""", cs)

    # ── HPT ENTRIES ──────────────────────────────────────────────────────
    hpt_rows = [
        ("Ed029 Evening", "H6/H5/H1", "H4/H5/H6", "H6/H4/H1", "H3/H6/H1", "H6/H3/H1",
         "H4 gap confirmed Case B. H6 intersection A/B/C/E confirmed."),
        ("Ed030 Morning", "H6/H4/H5/H1", "H4/H6/H1", "H6/H4/H1", "H3/H6/H1", "H6/H3/H1",
         "H4 dominant Case A: ceasefire without talks."),
        ("Ed031 Evening", "H6/H4/H5-partial/H2/H1", "H4/H6/H1", "H6/H4/H1", "H3/H6/H1", "H6/H3/H1",
         "H5 partially resolving Case A. Triple H6 suppressor Case E."),
        ("Ed032 Morning", "H4/H1/H6/H2/H5-partial", "H6/H4/H1", "H6/H4", "H3/H6/H1", "H6/H3",
         "H4 dominant. PMM-003 warning active."),
        ("Ed033 Evening", "H4/H1/PMM-004/H5-partial", "H6/H1/H4", "H4/H6/CP-flag", "H3/H6", "H6/H3/propagation",
         "H4 fully materialised: PRED-031-A CONTRADICTED. First AI-012-3 change point flag."),
    ]
    for row in hpt_rows:
        c.execute("""INSERT OR IGNORE INTO hpt_entries
            (edition, case_a, case_b, case_c, case_d, case_e, outcome_correlation)
            VALUES (?,?,?,?,?,?,?)""", row)

    # ── SYSTEM CHANGE LOG ────────────────────────────────────────────────
    from config import SYSTEM_CHANGE_LOG_ENTRIES
    for entry in SYSTEM_CHANGE_LOG_ENTRIES:
        c.execute("""INSERT OR IGNORE INTO system_change_log
            (entry_id, summary, in_force) VALUES (?,?,?)""",
            (entry["entry"], entry["summary"], entry["in_force"]))

    # ── PREDICTIONS OPEN — Ed033 ─────────────────────────────────────────
    open_preds = [
        ("PRED-034-A", "Second round formally convenes", "Before 30 Apr",
         "OPENED Ed033", "Araghchi proceeds to Moscow without Islamabad return AND no Oman framework = CONTRADICTED"),
        ("PRED-031-B", "Case A talks produce formal Hormuz instrument", "Before 30 Apr",
         "PENDING", "Window closes 30 Apr without instrument = CONTRADICTED"),
        ("PRED-031-C", "Lebanon 3-week ceasefire holds through ~14 May", "~14 May",
         "AT RISK", "Hezbollah confirmed barrage 100+ rockets at Israel = CONTRADICTED"),
        ("PRED-031-D", "OFAC enforcement or India Chabahar divestment confirmed", "Before 15 May",
         "PARTIALLY PROGRESSING", "Neither enforcement nor confirmed divestment by 15 May = CONTRADICTED"),
        ("PRED-031-E", "IRGC follow-on Yanbu/Petroline strike", "Before 7 May",
         "PENDING", "Window closes 7 May without strike = CONTRADICTED"),
        ("PRED-030-B", "Northwood deployment schedule published", "Before 30 Apr",
         "PENDING", "Window closes 30 Apr without schedule = CONTRADICTED"),
        ("PRED-030-A", "Iran unified proposal + formal second round", "Before 30 Apr",
         "NEAR-CONTRADICTED", "Window closes 30 Apr without second round = CONTRADICTED"),
        ("PRED-029-B", "Hormuz sustained transit 24h+ (unrestricted)", "Ongoing",
         "PENDING", "Full 24h+ unrestricted transit = CONFIRMED"),
        ("PRED-025-C/026-B", "Summit deployment plan and Northwood timeline", "Ongoing",
         "PARTIAL MAINTAINED", "Named deployment timeline + joint statement = CONFIRMED"),
        ("PRED-022-B", "IRGC kinetic response to USN vessel", "Through resolution",
         "PARTIAL", "Direct IRGC kinetic strike on USN vessel = CONFIRMED"),
        ("PRED-025-B", "Abdollahi total blockade activation", "Through resolution",
         "PENDING", "Abdollahi announces total blockade activation = CONFIRMED"),
        ("PRED-006-A", "GCC emergency meeting", "Post-ceasefire",
         "WATCH", "Formal GCC statement declining to convene = CONTRADICTED"),
    ]
    for p in open_preds:
        c.execute("""INSERT OR IGNORE INTO predictions_open
            (pred_ref, flag, window, status, disconfirmation)
            VALUES (?,?,?,?,?)""", p)

    # ── PREDICTIONS RESOLVED — cumulative through Ed033 ──────────────────
    resolved = [
        ("PRED-031-A", "CONTRADICTED", "Trump cancelled Witkoff/Kushner trip. PMM-004.", 0.77, 0.0, 0.5929, 33),
        ("PRED-026-C", "CONFIRMED", "Lebanon 72-hr window closed. Gate 0.6.", 0.64, 1.0, 0.1296, 30),
        ("PRED-028-C", "CONFIRMED", "Same basis.", 0.64, 1.0, 0.1296, 30),
        ("PRED-015-A", "PARTIAL", "Trump extended ceasefire 21 April.", 0.53, 0.5, 0.0009, 30),
        ("PRED-022-B-res", "PARTIAL", "IRGC seized non-USN vessels.", 0.23, 0.5, 0.0729, 30),
        ("PRED-012-B", "CONTRADICTED", "PMM-001 triggered.", None, None, None, None),
        ("PRED-027-B", "CONTRADICTED", "Iran closed Hormuz 18 April.", 0.55, 0.0, 0.3025, 29),
        ("PRED-028-B", "CONTRADICTED", "Same basis.", 0.55, 0.0, 0.3025, 29),
        ("PRED-026-D", "CONFIRMED", "GL U lapsed.", 0.95, 1.0, 0.0025, 28),
        ("PRED-023-B", "CONFIRMED", "Same basis.", 0.95, 1.0, 0.0025, 28),
        ("PRED-022-C", "CONFIRMED", "Same basis.", 0.95, 1.0, 0.0025, 28),
        ("PRED-026-E", "CONTRADICTED", "First Yanbu strike. PMM-002.", 0.65, 0.0, 0.4225, 27),
        ("PRED-025-C-res", "PARTIAL", "Paris Summit confirmed. No deployment timeline.", 0.70, 0.5, 0.0400, 28),
        ("PRED-026-B-res", "PARTIAL", "Named assets. No timeline.", 0.70, 0.5, 0.0400, 28),
        ("PRED-022-E", "AMBIGUOUS", "Insufficient evidence.", None, None, None, None),
        ("PRED-027-E", "CONTRADICTED", "22 April window closed without Yanbu strike.", None, None, None, None),
        ("PRED-028-E", "CONTRADICTED", "Same basis.", None, None, None, None),
        ("PRED-018-E", "CONFIRMED", "IRGC struck East-West Pipeline 8 April.", None, None, None, 27),
        ("PRED-022-D", "CONFIRMED", "Same basis.", None, None, None, 27),
    ]
    for r in resolved:
        c.execute("""INSERT OR IGNORE INTO predictions_resolved
            (pred_ref, outcome, notes, fi, oi, brier_contribution, resolution_edition)
            VALUES (?,?,?,?,?,?,?)""", r)

    # ── DISCONFIRMATION THRESHOLDS ───────────────────────────────────────
    thresholds = [
        ("A", "Araghchi returns Islamabad + both parties confirm second round", "PRED-034-A CONFIRMED. H-A1 recovers to 65-75%"),
        ("A", "Araghchi proceeds to Moscow without return AND no Oman framework", "PRED-034-A CONTRADICTED. H-A1 falls to 38-50%"),
        ("A", "Oman channel produces Hormuz face-saving formula", "H-B1 recovers to 20-30%"),
        ("A", "Jalili confirmed as Iranian negotiating lead", "H5 re-activated. H-A1 falls further."),
        ("A", "Iran abandons blockade-lift precondition", "H-A1 rises to 65-75%"),
        ("A", "IRGC/SNSC repudiates Araghchi framework", "H-A1 falls to 28-40%"),
        ("A", "Trump resumes strikes", "Gate 5 Case A. H-A2 CONFIRMED."),
        ("A", "Phone call Trump-Araghchi (direct)", "H-A1 rises sharply"),
        ("B", "Oman channel Hormuz framework agreed", "H-B1 recovers to 20-30%"),
        ("B", "Mine clearance estimate revised (faster)", "H-B1 rises"),
        ("B", "IRGC direct kinetic attack on USN vessel", "PRED-022-B CONFIRMED. Gate 5."),
        ("B", "Northwood deployment schedule published", "H-B3 to 45-58%. PRED-030-B CONFIRMED."),
        ("B", "SNSC endorses toll-booth as permanent", "H-B1 falls to 5-12%"),
        ("B", "IRGC announces new vessel seizures + toll expansion", "H-B1 falls to 8-15%"),
        ("C", "Ceasefire holds through 14 May + Washington visit confirms diplomatic track", "PRED-031-C CONFIRMED"),
        ("C", "Netanyahu backs down from strike order under US pressure", "H-C1 recovers marginally"),
        ("C", "Hezbollah confirmed barrage >=100 rockets at Israeli territory", "Gate 0.6 BREACHED. H-C3 CONFIRMED."),
        ("C", "IDF major operation north of Litani River", "H-C2 approaches dominant"),
        ("C", "UNIFIL withdrawal", "Monitoring collapses. H-C2 rises sharply."),
        ("C", "Lebanon army deploys under ceasefire terms", "H-C1 stabilises"),
        ("D", "OFAC enforcement on Chabahar operators", "PRED-031-D CONFIRMED"),
        ("D", "India formally divests Chabahar (confirmed)", "Strategic channel severed"),
        ("D", "OFAC issues new waiver / sanctions lifted", "H-D1 partially revives"),
        ("E", "IRGC Yanbu/Petroline strike", "PRED-031-E CONFIRMED. Gate 5 CRITICAL."),
        ("E", "Lebanon collapses (H-C3 confirmed)", "H-E2 rises to 50-65%"),
        ("E", "Talks resume second round (H-A1 confirmed)", "H-E1 suppressor partially restored"),
        ("E", "Talks fail and ceasefire lapses", "H-E2 dominance reasserts"),
    ]
    for t in thresholds:
        c.execute("""INSERT OR IGNORE INTO disconfirmation_thresholds
            (case_id, threshold, effect) VALUES (?,?,?)""", t)

    conn.commit()
