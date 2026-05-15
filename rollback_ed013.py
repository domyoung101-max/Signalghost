"""rollback_ed013.py — Complete rollback of Ed013.

Ed013 ran with three critical bugs:
1. PRED-01-C resolved incorrectly (ceasefire was still in place)
2. Prediction window was wrong (14 May vs actual 17 May)
3. fi used post-calibration value (0.83) instead of pre-calibration (0.76)
4. PDF self-contradicted (CONTRADICTED on p1, "resolved affirmatively" on p14)

This script removes ALL Ed013 data from every table so the system
can re-run Ed013 from scratch with the corrected code.
"""

import sqlite3
import os

DB_PATH = os.environ.get("SIGNALGHOST_DB", os.environ.get("ATOLLSPHERE_DB", "atollsphere.db"))


def rollback():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("=" * 60)
    print("FULL ROLLBACK: Removing all Ed013 data")
    print("=" * 60)

    # All tables with edition-keyed data
    edition_tables = [
        "hypotheses",
        "causal_edges",
        "delta_buffer",
        "change_point_flags",
        "correlation_matrix",
        "propagation_register",
        "ema_band_errors",
        "per_band_lookup",
        "rl_q_table",
        "feed_sweep_results",
        "gate_records",
        "carry_forward_facts",
        "calibration_map",
        "hpt_entries",
        "deviation_audit",
        "system_change_log",
    ]

    for table in edition_tables:
        try:
            c.execute(f"DELETE FROM {table} WHERE edition = 13")
            print(f"  {table}: deleted {c.rowcount} row(s)")
        except Exception as e:
            print(f"  {table}: skipped ({e})")

    # Remove Ed013 from editions table
    c.execute("DELETE FROM editions WHERE edition = 13")
    print(f"  editions: deleted {c.rowcount} row(s)")

    # Remove any PLM entries from Ed013
    c.execute("DELETE FROM plm_entries WHERE edition = 13")
    print(f"  plm_entries (ed013): deleted {c.rowcount} row(s)")

    # Remove the fix PLM if it was already added
    c.execute("DELETE FROM plm_entries WHERE entry_id = 'PLM-013-FIX'")
    print(f"  plm_entries (fix entry): deleted {c.rowcount} row(s)")

    # Remove PRED-01-C from brier_table and predictions_resolved
    c.execute("DELETE FROM brier_table WHERE pred_ref = 'PRED-01-C'")
    print(f"  brier_table (PRED-01-C): deleted {c.rowcount} row(s)")

    c.execute("DELETE FROM predictions_resolved WHERE pred_ref = 'PRED-01-C'")
    print(f"  predictions_resolved (PRED-01-C): deleted {c.rowcount} row(s)")

    # Restore PRED-01-C to clean open state
    c.execute("""UPDATE predictions_open SET
        status = 'OPENED Ed01',
        outcome = NULL,
        oi = NULL,
        brier_contribution = NULL,
        resolution_edition = NULL,
        fi = 0.76,
        window = 'Before 17 May 2026'
        WHERE pred_ref = 'PRED-01-C'""")
    print(f"  predictions_open (PRED-01-C): restored to OPENED, fi=0.76, window=Before 17 May 2026")

    # Add PLM entry documenting the retraction (at Ed012 so it persists)
    try:
        c.execute("""INSERT INTO plm_entries (entry_id, edition, issue)
            VALUES (?, ?, ?)""",
            ("PLM-013-RETRACT", 12,
             "Ed013 RETRACTED AND ROLLED BACK. Three bugs: "
             "(1) PRED-01-C resolved as CONTRADICTED but ceasefire was still in place per AFP/Al Jazeera, "
             "(2) window was 14 May but actual extension runs to 17 May, "
             "(3) fi used post-calibration value 0.83 instead of pre-calibration 0.76 (circular scoring). "
             "Code fix: session_executor now snapshots fi before Step 6.5 dynamic linkage. "
             "Ed013 will re-run fresh with corrected state."))
        print(f"  PLM: added PLM-013-RETRACT at Ed012")
    except Exception as e:
        print(f"  PLM: skipped ({e})")

    conn.commit()

    # ── VERIFICATION ──────────────────────────────────────────────────
    print()
    print("VERIFICATION:")

    # Check latest edition is now 12
    c.execute("SELECT MAX(edition) FROM editions")
    latest = c.fetchone()[0]
    print(f"  Latest edition: {latest} (should be 12)")

    # Check PRED-01-C state
    c.execute("SELECT pred_ref, fi, window, status, outcome FROM predictions_open WHERE pred_ref = 'PRED-01-C'")
    row = c.fetchone()
    print(f"  PRED-01-C: {row}")

    # Check Brier state
    c.execute("SELECT COUNT(*) FROM brier_table")
    n = c.fetchone()[0]
    print(f"  Brier table entries: {n} (should be 0)")

    # Check no Ed013 data remains
    for table in edition_tables:
        try:
            c.execute(f"SELECT COUNT(*) FROM {table} WHERE edition = 13")
            count = c.fetchone()[0]
            if count > 0:
                print(f"  WARNING: {table} still has {count} Ed013 rows!")
            else:
                pass  # Clean
        except:
            pass

    # Count Ed012 hypotheses to confirm prior state exists
    c.execute("SELECT COUNT(*) FROM hypotheses WHERE edition = 12")
    h_count = c.fetchone()[0]
    print(f"  Ed012 hypotheses: {h_count} (should be 15)")

    conn.close()

    print()
    print("Rollback complete. System will run Ed013 fresh on next python main.py")
    print()
    print("IMPORTANT: Rename the bad PDF to Signalghost_Ed013_RETRACTED.pdf")
    print("The corrected session_executor.py includes the fi-snapshot fix.")


if __name__ == "__main__":
    rollback()
