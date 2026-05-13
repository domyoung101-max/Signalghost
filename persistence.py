"""persistence.py — Signalghost SQLite persistence layer.

Creates and manages all tables required by the SESSION_STATE for carry-forward
state across editions.  Every value the SESSION_STATE says must carry forward
is loaded at run start and saved back at run end.
"""

import sqlite3
import json
import os
from typing import List, Optional, Dict, Any

DB_PATH = os.environ.get("SIGNALGHOST_DB", os.environ.get("ATOLLSPHERE_DB", "atollsphere.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables.  Safe to call multiple times (IF NOT EXISTS)."""
    conn = get_connection()
    c = conn.cursor()

    # ── EDITIONS ─────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS editions (
        edition_number   INTEGER PRIMARY KEY,
        sweep_descriptor TEXT NOT NULL,
        gmt_timestamp    TEXT NOT NULL,
        bst_timestamp    TEXT NOT NULL,
        war_day          INTEGER NOT NULL,
        brier_score      REAL,
        n_predictions    INTEGER DEFAULT 0,
        architecture_version TEXT DEFAULT 'v1.3.0',
        created_at       TEXT DEFAULT (datetime('now'))
    )""")

    # ── HYPOTHESES ───────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS hypotheses (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        hyp_id           TEXT NOT NULL,
        case_id          TEXT NOT NULL,
        edition          INTEGER NOT NULL,
        range_lower      REAL NOT NULL,
        range_upper      REAL NOT NULL,
        point_estimate   REAL NOT NULL,
        status           TEXT DEFAULT '',
        pipeline_stages  TEXT DEFAULT '',
        correction_basis TEXT DEFAULT '',
        h4_gap_active    INTEGER DEFAULT 0,
        tier1_denial_active INTEGER DEFAULT 0,
        no_observable_prep_action INTEGER DEFAULT 0,
        independent_chains INTEGER DEFAULT 2,
        single_cluster_h5 INTEGER DEFAULT 0,
        UNIQUE(hyp_id, edition)
    )""")

    # ── PREDICTIONS (OPEN) ───────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS predictions_open (
        pred_ref          TEXT PRIMARY KEY,
        flag              TEXT NOT NULL,
        window            TEXT NOT NULL,
        status            TEXT NOT NULL,
        disconfirmation   TEXT NOT NULL,
        fi                REAL,
        outcome           TEXT,
        oi                REAL,
        brier_contribution REAL,
        resolution_edition INTEGER,
        notes             TEXT DEFAULT '',
        resolution_yes    TEXT DEFAULT '',
        resolution_no     TEXT DEFAULT '',
        resolution_source TEXT DEFAULT '',
        tracked_hyp       TEXT DEFAULT ''
    )""")

    # ── PREDICTIONS (RESOLVED) ───────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS predictions_resolved (
        pred_ref   TEXT PRIMARY KEY,
        outcome    TEXT NOT NULL,
        notes      TEXT DEFAULT '',
        fi         REAL,
        oi         REAL,
        brier_contribution REAL,
        resolution_edition INTEGER
    )""")

    # ── BRIER TABLE ──────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS brier_table (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        pred_ref    TEXT NOT NULL,
        fi          REAL NOT NULL,
        oi          REAL NOT NULL,
        squared_error REAL NOT NULL,
        edition     INTEGER NOT NULL,
        notes       TEXT DEFAULT ''
    )""")

    # ── CAUSAL EDGE REGISTER (AI-012-1) ──────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS causal_edges (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        cause           TEXT NOT NULL,
        effect          TEXT NOT NULL,
        prior_strength  REAL NOT NULL,
        observed_signal REAL NOT NULL,
        new_strength    REAL NOT NULL,
        edition         INTEGER NOT NULL
    )""")

    # ── DELTA BUFFER (AI-012-2) ──────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS delta_buffer (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        hyp_id   TEXT NOT NULL,
        edition  INTEGER NOT NULL,
        delta_p  REAL NOT NULL,
        UNIQUE(hyp_id, edition)
    )""")

    # ── CHANGE POINT FLAGS (AI-012-3) ────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS change_point_flags (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        hyp_id      TEXT NOT NULL,
        edition     INTEGER NOT NULL,
        delta_p     REAL NOT NULL,
        mean_delta  REAL NOT NULL,
        std_delta   REAL NOT NULL,
        z_score     REAL NOT NULL,
        flag_raised INTEGER NOT NULL,
        resolution  TEXT DEFAULT '',
        active      INTEGER DEFAULT 1,
        UNIQUE(hyp_id, edition)
    )""")

    # ── CORRELATION MATRIX (AI-012-4) ────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS correlation_matrix (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        hyp_a                 TEXT NOT NULL,
        hyp_b                 TEXT NOT NULL,
        raw_correlation       REAL NOT NULL,
        shrinkage_factor      REAL NOT NULL,
        effective_correlation REAL NOT NULL,
        n                     INTEGER NOT NULL,
        edition               INTEGER NOT NULL,
        UNIQUE(hyp_a, hyp_b, edition)
    )""")

    # ── PROPAGATION REGISTER (AI-012-5) ──────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS propagation_register (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        trigger_hyp    TEXT NOT NULL,
        direction      TEXT NOT NULL,
        downstream_hyp TEXT NOT NULL,
        adjustment     REAL NOT NULL,
        condition_text TEXT NOT NULL,
        active         INTEGER DEFAULT 0,
        applied_edition INTEGER
    )""")

    # ── EMA BAND ERRORS (AI-012-7) ───────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS ema_band_errors (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        band            TEXT NOT NULL,
        ema_error_prior REAL NOT NULL,
        current_error   REAL NOT NULL,
        ema_error_updated REAL NOT NULL,
        edition         INTEGER NOT NULL,
        UNIQUE(band, edition)
    )""")

    # ── PER-BAND LOOKUP TABLE (AI-012-9) ─────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS per_band_lookup (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        band         TEXT NOT NULL,
        pred_freq    INTEGER NOT NULL,
        obs_freq     INTEGER NOT NULL,
        obs_rate     REAL,
        ema_error    REAL NOT NULL,
        adjustment   REAL NOT NULL,
        min_n_status TEXT NOT NULL,
        edition      INTEGER NOT NULL,
        UNIQUE(band, edition)
    )""")

    # ── RL BANDIT Q-TABLE (AI-012-6) ─────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS rl_q_table (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        band           TEXT NOT NULL,
        current_factor REAL NOT NULL,
        q_value        REAL NOT NULL,
        status         TEXT NOT NULL,
        edition        INTEGER NOT NULL,
        UNIQUE(band, edition)
    )""")

    # ── PLM ENTRIES ──────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS plm_entries (
        entry_id TEXT PRIMARY KEY,
        edition  TEXT NOT NULL,
        issue    TEXT NOT NULL
    )""")

    # ── PMM ENTRIES ──────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS pmm_entries (
        entry_id      TEXT PRIMARY KEY,
        pred_ref      TEXT NOT NULL,
        outcome       TEXT NOT NULL,
        what_failed   TEXT NOT NULL,
        why           TEXT NOT NULL,
        system_change TEXT NOT NULL,
        heuristic     TEXT NOT NULL
    )""")

    # ── FEED SWEEP RESULTS ───────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS feed_sweep_results (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_name TEXT NOT NULL,
        tier      INTEGER NOT NULL,
        checked   INTEGER NOT NULL,
        findings  TEXT DEFAULT '',
        edition   INTEGER NOT NULL,
        timestamp TEXT DEFAULT ''
    )""")

    # ── GATE RECORDS ─────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS gate_records (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        gate_id   TEXT NOT NULL,
        gate_name TEXT NOT NULL,
        edition   INTEGER NOT NULL,
        passed    INTEGER NOT NULL,
        details   TEXT DEFAULT '',
        hyp_id    TEXT
    )""")

    # ── CARRY-FORWARD FACTS ──────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS carry_forward_facts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        fact            TEXT NOT NULL,
        last_verified   TEXT NOT NULL,
        ed_action       TEXT NOT NULL,
        staleness_days  INTEGER,
        staleness_editions INTEGER DEFAULT 0,
        edition         INTEGER NOT NULL
    )""")

    # ── CASES ────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        case_id    TEXT NOT NULL,
        title      TEXT NOT NULL,
        tag        TEXT NOT NULL,
        confidence TEXT NOT NULL,
        notes      TEXT DEFAULT '',
        edition    INTEGER NOT NULL,
        PRIMARY KEY(case_id, edition)
    )""")

    # ── CALIBRATION MAP (AI-007) ─────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS calibration_map (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        hyp_id          TEXT NOT NULL,
        prior_range     TEXT NOT NULL,
        new_range       TEXT NOT NULL,
        point_estimate  REAL NOT NULL,
        pipeline_stages TEXT NOT NULL,
        correction_basis TEXT NOT NULL,
        edition         INTEGER NOT NULL,
        UNIQUE(hyp_id, edition)
    )""")

    # ── HPT ENTRIES ──────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS hpt_entries (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        edition             TEXT NOT NULL,
        case_a              TEXT NOT NULL,
        case_b              TEXT NOT NULL,
        case_c              TEXT NOT NULL,
        case_d              TEXT NOT NULL,
        case_e              TEXT NOT NULL,
        outcome_correlation TEXT NOT NULL,
        UNIQUE(edition)
    )""")

    # ── DEVIATION AUDIT RESULTS ──────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS deviation_audit (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        item_number INTEGER NOT NULL,
        description TEXT NOT NULL,
        passed      INTEGER NOT NULL,
        notes       TEXT DEFAULT '',
        edition     INTEGER NOT NULL,
        UNIQUE(item_number, edition)
    )""")

    # ── DISCONFIRMATION THRESHOLDS ───────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS disconfirmation_thresholds (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id   TEXT NOT NULL,
        threshold TEXT NOT NULL,
        effect    TEXT NOT NULL
    )""")

    # ── SYSTEM CHANGE LOG ────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS system_change_log (
        entry_id TEXT PRIMARY KEY,
        summary  TEXT NOT NULL,
        in_force TEXT NOT NULL
    )""")

    conn.commit()

    # ── MIGRATIONS — add columns to existing tables if missing ──────────
    # Resolution Protocol fields (Criterion 6) — added post-Ed010.
    for col in ["resolution_yes", "resolution_no", "resolution_source"]:
        try:
            c.execute(f"ALTER TABLE predictions_open ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            pass  # column already exists

    # CF-1: tracked_hyp — links prediction fi to a specific hypothesis
    for col in ["tracked_hyp"]:
        try:
            c.execute(f"ALTER TABLE predictions_open ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            pass  # column already exists

    # CF-3: staleness_editions — integer counter for carry-forward fact age
    try:
        c.execute("ALTER TABLE carry_forward_facts ADD COLUMN staleness_editions INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass  # column already exists

    conn.close()


# ── GENERIC CRUD HELPERS ─────────────────────────────────────────────────────

def insert_row(table: str, data: Dict[str, Any]):
    conn = get_connection()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    conn.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})",
                 list(data.values()))
    conn.commit()
    conn.close()


def fetch_all(table: str, where: str = "", params: tuple = ()) -> List[Dict]:
    conn = get_connection()
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_one(table: str, where: str, params: tuple = ()) -> Optional[Dict]:
    conn = get_connection()
    sql = f"SELECT * FROM {table} WHERE {where}"
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return dict(row) if row else None


def get_latest_edition() -> Optional[int]:
    conn = get_connection()
    row = conn.execute("SELECT MAX(edition_number) as mx FROM editions").fetchone()
    conn.close()
    return row["mx"] if row and row["mx"] is not None else None


def get_latest_hypotheses(edition: int) -> List[Dict]:
    return fetch_all("hypotheses", "edition = ?", (edition,))


def get_latest_causal_edges(edition: int) -> List[Dict]:
    return fetch_all("causal_edges", "edition = ?", (edition,))


def get_delta_buffer(hyp_id: str, limit: int = 5) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM delta_buffer WHERE hyp_id = ? ORDER BY edition DESC LIMIT ?",
        (hyp_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_correlation_matrix(edition: int) -> List[Dict]:
    return fetch_all("correlation_matrix", "edition = ?", (edition,))


def get_latest_ema_errors(edition: int) -> List[Dict]:
    return fetch_all("ema_band_errors", "edition = ?", (edition,))


def get_latest_q_table(edition: int) -> List[Dict]:
    return fetch_all("rl_q_table", "edition = ?", (edition,))


def get_latest_per_band_lookup(edition: int) -> List[Dict]:
    return fetch_all("per_band_lookup", "edition = ?", (edition,))


def get_active_change_point_flags() -> List[Dict]:
    return fetch_all("change_point_flags", "active = 1")


def get_all_brier_rows() -> List[Dict]:
    return fetch_all("brier_table", "", ())


def get_all_plm() -> List[Dict]:
    return fetch_all("plm_entries")


def get_all_pmm() -> List[Dict]:
    return fetch_all("pmm_entries")


def get_open_predictions() -> List[Dict]:
    return fetch_all("predictions_open")


def get_resolved_predictions() -> List[Dict]:
    return fetch_all("predictions_resolved")


def get_propagation_register() -> List[Dict]:
    return fetch_all("propagation_register")


# ── SEED HELPERS ─────────────────────────────────────────────────────────────

def seed_from_session_state(session_data: Dict):
    """Seed database from parsed SESSION_STATE data.  Called on first run."""
    conn = get_connection()
    # Check if already seeded
    row = conn.execute("SELECT COUNT(*) as c FROM editions").fetchone()
    if row["c"] > 0:
        conn.close()
        return  # already seeded

    # Import here to avoid circular dependency
    from calibration_state import SEED_DATA
    SEED_DATA(conn)

    conn.commit()
    conn.close()


# ── HYPOTHESIS TREND (Cross-edition time-series) ────────────────────────────

def get_hypothesis_trend(hyp_ids: List[str] = None) -> Dict[str, List[Dict]]:
    """Return per-edition point estimates for each hypothesis.

    Returns dict: hyp_id -> [{"edition": N, "point_estimate": X, "range_lower": L, "range_upper": U}, ...]
    sorted by edition ascending.
    """
    conn = get_connection()
    if hyp_ids:
        placeholders = ",".join(["?"] * len(hyp_ids))
        rows = conn.execute(
            f"SELECT hyp_id, edition, point_estimate, range_lower, range_upper "
            f"FROM hypotheses WHERE hyp_id IN ({placeholders}) ORDER BY hyp_id, edition",
            hyp_ids
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT hyp_id, edition, point_estimate, range_lower, range_upper "
            "FROM hypotheses ORDER BY hyp_id, edition"
        ).fetchall()
    conn.close()

    trend = {}
    for r in rows:
        hid = r["hyp_id"]
        if hid not in trend:
            trend[hid] = []
        trend[hid].append({
            "edition": r["edition"],
            "point_estimate": r["point_estimate"],
            "range_lower": r["range_lower"],
            "range_upper": r["range_upper"],
        })
    return trend
