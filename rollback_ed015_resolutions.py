"""rollback_ed015_resolutions.py — Correct PRED-01-C and PRED-01-D outcomes.

Ed015 resolved both predictions as CONTRADICTED. Both should be CONFIRMED.

PRED-01-D: Trump-Xi summit DID produce public Iran-framework reference.
  - White House readout: agreed Hormuz "must remain open"
  - Trump told Fox News Xi offered diplomatic help on Iran
  - Rubio confirmed Iran war discussed at summit
  Sources: Al Jazeera, CNBC, NBC News, CNN, PBS — May 14-15, 2026

PRED-01-C: Lebanon ceasefire DID hold through extension.
  - State Department announced 45-day extension on May 15
  - Talks described as "highly productive"
  - Ceasefire formally held (porous but extended, not collapsed)
  Sources: CNBC, Al Jazeera, Times of Israel, PBS — May 15, 2026

Usage:
  python rollback_ed015_resolutions.py          # dry-run (shows what would change)
  python rollback_ed015_resolutions.py --apply   # apply corrections

Generated: 17 May 2026 GMT
"""

import sqlite3
import sys
import os
import shutil
from datetime import datetime

DB_PATH = "atollsphere.db"
DRY_RUN = "--apply" not in sys.argv


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: {DB_PATH} not found. Run from repo root.")
        sys.exit(1)

    # ── Backup before any changes ──
    if not DRY_RUN:
        backup_path = f"atollsphere_backup_pre_rollback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, backup_path)
        print(f"Backup created: {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("=" * 60)
    print("ED015 RESOLUTION ROLLBACK — PRED-01-C + PRED-01-D")
    print("=" * 60)

    # ── Show current state ──
    print("\n--- CURRENT STATE (BEFORE CORRECTION) ---")
    for pred in ("PRED-01-C", "PRED-01-D"):
        row = c.execute(
            "SELECT pred_ref, outcome, fi, oi, brier_contribution, notes "
            "FROM predictions_resolved WHERE pred_ref = ?", (pred,)
        ).fetchone()
        if row:
            print(f"  {row['pred_ref']}: {row['outcome']} "
                  f"fi={row['fi']:.4f} oi={row['oi']:.1f} "
                  f"BS={(row['fi'] - row['oi'])**2:.4f}")
            print(f"    Evidence: {row['notes'][:100]}...")
        else:
            print(f"  {pred}: NOT FOUND in predictions_resolved")

    c.execute("SELECT AVG(squared_error) as bs, COUNT(*) as n FROM brier_table")
    bs_row = c.fetchone()
    print(f"\n  Current Brier Score: {bs_row['bs']:.4f} (n={bs_row['n']})")

    # ── Define corrections ──
    corrections = [
        {
            "pred_ref": "PRED-01-D",
            "old_outcome": "CONTRADICTED",
            "new_outcome": "CONFIRMED",
            "old_oi": 0.0,
            "new_oi": 1.0,
            "evidence": (
                "CONFIRMED: Trump-Xi summit May 14-15 produced multiple public "
                "Iran-framework references. White House readout: agreed Hormuz "
                "'must remain open to support the free flow of energy.' Xi "
                "'made clear China's opposition to the militarisation of the "
                "strait and any effort to charge a toll.' Trump told Fox News "
                "Xi offered diplomatic help on Iran. Rubio confirmed Iran war "
                "discussed. Sources: Al Jazeera, CNBC, NBC News, CNN, PBS. "
                "Correction applied 17 May 2026 GMT — feed_analyzer missed "
                "summit evidence in RSS sweep."
            ),
        },
        {
            "pred_ref": "PRED-01-C",
            "old_outcome": "CONTRADICTED",
            "new_outcome": "CONFIRMED",
            "old_oi": 0.0,
            "new_oi": 1.0,
            "evidence": (
                "CONFIRMED: Lebanon ceasefire held and was extended by 45 days "
                "on May 15, 2026. State Department: 'highly productive' talks. "
                "Ceasefire in place since April 16; formally extended despite "
                "continued IDF strikes in southern Lebanon. The formal framework "
                "held — it was extended, not collapsed. Sources: CNBC, Al Jazeera, "
                "Times of Israel, PBS, The National. Correction applied 17 May "
                "2026 GMT — feed_analyzer misinterpreted IDF strike evidence as "
                "ceasefire collapse."
            ),
        },
    ]

    # ── Apply corrections ──
    print("\n--- CORRECTIONS ---")
    for corr in corrections:
        pred_ref = corr["pred_ref"]

        # Get current fi from DB (preserve it — fi is the forecast, not being changed)
        row = c.execute(
            "SELECT fi FROM predictions_resolved WHERE pred_ref = ?",
            (pred_ref,)
        ).fetchone()
        if not row:
            print(f"  ERROR: {pred_ref} not found in predictions_resolved. Skipping.")
            continue

        fi = row["fi"]
        new_oi = corr["new_oi"]
        new_sq_err = (fi - new_oi) ** 2

        print(f"\n  {pred_ref}:")
        print(f"    Outcome: {corr['old_outcome']} → {corr['new_outcome']}")
        print(f"    oi: {corr['old_oi']} → {new_oi}")
        print(f"    fi: {fi:.4f} (unchanged)")
        print(f"    BS contribution: {(fi - corr['old_oi'])**2:.4f} → {new_sq_err:.4f}")

        if not DRY_RUN:
            # Write 1: UPDATE predictions_resolved
            c.execute(
                "UPDATE predictions_resolved SET outcome = ?, oi = ?, "
                "brier_contribution = ?, notes = ? WHERE pred_ref = ?",
                (corr["new_outcome"], new_oi, new_sq_err, corr["evidence"], pred_ref)
            )
            assert c.rowcount == 1, f"predictions_resolved UPDATE failed for {pred_ref}"

            # Write 2: UPDATE predictions_open
            c.execute(
                "UPDATE predictions_open SET outcome = ?, oi = ?, "
                "brier_contribution = ? WHERE pred_ref = ?",
                (corr["new_outcome"], new_oi, new_sq_err, pred_ref)
            )
            assert c.rowcount == 1, f"predictions_open UPDATE failed for {pred_ref}"

            # Write 3: UPDATE brier_table
            c.execute(
                "UPDATE brier_table SET oi = ?, squared_error = ?, notes = ? "
                "WHERE pred_ref = ? AND edition = 15",
                (new_oi, new_sq_err, corr["evidence"], pred_ref)
            )
            assert c.rowcount == 1, f"brier_table UPDATE failed for {pred_ref}"

            print(f"    ✓ All 3 tables updated")

    # ── Verify final state ──
    if not DRY_RUN:
        conn.commit()

    print("\n--- CORRECTED STATE ---")
    for pred in ("PRED-01-C", "PRED-01-D"):
        if DRY_RUN:
            row = c.execute(
                "SELECT fi FROM predictions_resolved WHERE pred_ref = ?", (pred,)
            ).fetchone()
            fi = row["fi"] if row else 0.0
            new_sq = (fi - 1.0) ** 2
            print(f"  {pred}: CONFIRMED fi={fi:.4f} oi=1.0 BS={new_sq:.4f} (projected)")
        else:
            row = c.execute(
                "SELECT pred_ref, outcome, fi, oi, brier_contribution "
                "FROM predictions_resolved WHERE pred_ref = ?", (pred,)
            ).fetchone()
            print(f"  {row['pred_ref']}: {row['outcome']} "
                  f"fi={row['fi']:.4f} oi={row['oi']:.1f} "
                  f"BS={row['brier_contribution']:.4f}")

    # Calculate corrected Brier
    if DRY_RUN:
        # Project from current fi values
        rows = c.execute("SELECT fi FROM predictions_resolved").fetchall()
        total_sq = sum((r["fi"] - 1.0) ** 2 for r in rows)
        n = len(rows)
        new_bs = total_sq / n if n else 0
        print(f"\n  Projected Brier Score: {new_bs:.4f} (n={n})")
    else:
        c.execute("SELECT AVG(squared_error) as bs, COUNT(*) as n FROM brier_table")
        bs_row = c.fetchone()
        print(f"\n  Corrected Brier Score: {bs_row['bs']:.4f} (n={bs_row['n']})")

    status_label = "ELITE" if (new_bs if DRY_RUN else bs_row['bs']) <= 0.10 else "OPERATIONAL" if (new_bs if DRY_RUN else bs_row['bs']) <= 0.15 else "DEGRADED"
    print(f"  Status: {status_label}")

    if DRY_RUN:
        print("\n  *** DRY RUN — no changes written ***")
        print("  Run with --apply to commit corrections")
    else:
        print(f"\n  ✓ Corrections committed to {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
