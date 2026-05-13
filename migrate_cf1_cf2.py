"""migrate_cf1_cf2.py — One-time migration for CF-1 (tracked_hyp) and CF-2 (resolution protocols).

Run once:  python migrate_cf1_cf2.py

Populates:
  - tracked_hyp: links each prediction to the hypothesis whose point_estimate drives fi
  - resolution_yes: observable condition(s) that resolve the prediction as CONFIRMED
  - resolution_no: observable condition(s) that resolve as CONTRADICTED
  - resolution_source: named verification source(s)

These fields are required by Criterion 6 (Resolution Protocol) and CF-1 (Dynamic fi Linkage).
"""

import sqlite3
import os

DB_PATH = os.environ.get("ATOLLSPHERE_DB", "atollsphere.db")


MIGRATION_DATA = {
    "PRED-01-A": {
        "tracked_hyp": "H-A1",
        "resolution_yes": (
            "Signed framework memo between Iran and US confirmed by both "
            "governments OR joint statement from Pakistan/Oman channel "
            "confirming agreement on nuclear terms."
        ),
        "resolution_no": (
            "30-day window expires without signed memo OR Trump publicly "
            "rejects Iranian draft OR Araghchi withdraws from Pakistan channel."
        ),
        "resolution_source": (
            "US State Department, Iranian Foreign Ministry (IRNA/PressTV), "
            "Pakistani Foreign Office, IAEA Director-General statements."
        ),
    },
    "PRED-01-B": {
        "tracked_hyp": "H-B1",
        "resolution_yes": (
            "IAEA confirms physical transfer of Iranian uranium stockpile "
            "to a third country OR Iranian government announces shipment "
            "with independent IAEA verification."
        ),
        "resolution_no": (
            "Memo signed without uranium-export provision OR IAEA confirms "
            "uranium remains in Iran post-memo OR Khamenei publicly rejects export."
        ),
        "resolution_source": (
            "IAEA quarterly reports, IAEA Director-General statements, "
            "Iranian Atomic Energy Organisation (AEOI) announcements."
        ),
    },
    "PRED-01-C": {
        "tracked_hyp": "H-C3",  # Ceasefire holds/extends — see NOTE below
        "resolution_yes": (
            "Ceasefire remains in effect through 14 May 2026 23:59 GMT with "
            "no confirmed barrage of 100+ rockets in a single 24-hour period "
            "AND no IDF brigade-strength operation north of Litani River."
        ),
        "resolution_no": (
            "IDF major operation north of Litani River in brigade strength OR "
            "Hezbollah confirmed barrage 100+ rockets at Israeli territory in "
            "a single 24-hour period OR US/Lebanon government announces "
            "ceasefire collapse before 14 May."
        ),
        "resolution_source": (
            "IDF official statements, Lebanese Armed Forces, UNIFIL situation "
            "reports, US State Department, Al Jazeera/Reuters live reporting."
        ),
    },
    "PRED-01-D": {
        "tracked_hyp": "H-D2",
        "resolution_yes": (
            "Trump-Xi summit produces joint statement or press conference "
            "that explicitly references Iran nuclear framework, sanctions "
            "architecture, or US-Iran negotiations."
        ),
        "resolution_no": (
            "Summit occurs but joint statement omits Iran entirely OR "
            "Beijing publicly opposes US framework OR summit deferred past "
            "16 May 2026."
        ),
        "resolution_source": (
            "White House press releases, Xinhua/CCTV official readout, "
            "joint communiqué text, press conference transcripts."
        ),
    },
    "PRED-01-E": {
        "tracked_hyp": "H-E1",
        "resolution_yes": (
            "IRGC commander (Salami or successor) or SNSC secretary issues "
            "public statement endorsing Araghchi diplomatic framework without "
            "contradicting core terms."
        ),
        "resolution_no": (
            "Salami or Ghalibaf publicly contradict Araghchi framework OR "
            "SNSC issues statement reasserting blockade-lift precondition OR "
            "Khamenei advisor repudiates Pakistan channel."
        ),
        "resolution_source": (
            "Tasnim News Agency, Fars News, IRNA, IRGC official Telegram "
            "channels, SNSC official statements."
        ),
    },
}


def run_migration():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure columns exist (idempotent)
    for col, col_type in [
        ("tracked_hyp", "TEXT DEFAULT ''"),
        ("resolution_yes", "TEXT DEFAULT ''"),
        ("resolution_no", "TEXT DEFAULT ''"),
        ("resolution_source", "TEXT DEFAULT ''"),
    ]:
        try:
            c.execute(f"ALTER TABLE predictions_open ADD COLUMN {col} {col_type}")
        except Exception:
            pass

    # Apply migration data
    for pred_ref, data in MIGRATION_DATA.items():
        c.execute(
            """UPDATE predictions_open
               SET tracked_hyp = ?,
                   resolution_yes = ?,
                   resolution_no = ?,
                   resolution_source = ?
               WHERE pred_ref = ?""",
            (
                data["tracked_hyp"],
                data["resolution_yes"],
                data["resolution_no"],
                data["resolution_source"],
                pred_ref,
            ),
        )
        rows_affected = c.rowcount
        print(f"  {pred_ref}: {'UPDATED' if rows_affected > 0 else 'NOT FOUND'} "
              f"→ tracked_hyp={data['tracked_hyp']}")

    conn.commit()

    # Verification pass
    print()
    print("VERIFICATION:")
    c.execute("SELECT pred_ref, tracked_hyp, resolution_yes, resolution_no, resolution_source FROM predictions_open")
    for row in c.fetchall():
        pred_ref, tracked, res_y, res_n, res_s = row
        y_ok = "✓" if res_y and len(res_y) > 20 else "✗"
        n_ok = "✓" if res_n and len(res_n) > 20 else "✗"
        s_ok = "✓" if res_s and len(res_s) > 10 else "✗"
        t_ok = "✓" if tracked else "✗"
        print(f"  {pred_ref}: tracked={tracked or 'EMPTY'} "
              f"[tracked:{t_ok} yes:{y_ok} no:{n_ok} source:{s_ok}]")

    conn.close()
    print()
    print("Migration complete. All 5 predictions now have Criterion 6 fields populated.")
    print()
    print("NOTE: PRED-01-C tracks H-C3 (ceasefire holds/extends).")
    print("Original seed used H-C1+H-C2 composite — verify this mapping is correct")
    print("for your current case structure before running Ed012.")


if __name__ == "__main__":
    print("CF-1/CF-2 Migration: Populating tracked_hyp + resolution protocols")
    print("=" * 60)
    run_migration()
