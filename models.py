"""models.py — Signalghost data models.

Dataclasses for every named structure in the SESSION_STATE: hypotheses,
predictions, causal edges, delta buffers, correlation matrix entries,
propagation rules, EMA band errors, Q-table entries, PLM/PMM entries,
feed sweep results, gate records, carry-forward facts, cases, calibration
map entries, HPT entries, and deviation audit results.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from config import PredictionOutcome


# ── HYPOTHESIS ───────────────────────────────────────────────────────────────

@dataclass
class Hypothesis:
    """A named hypothesis within a case."""
    hyp_id: str           # e.g. "H-A1"
    case_id: str          # e.g. "A"
    range_lower: float    # e.g. 0.50
    range_upper: float    # e.g. 0.62
    point_estimate: float # e.g. 0.56
    status: str = ""      # e.g. "PROVISIONAL", "CONFIRMED", "CONTRADICTED", ""
    pipeline_stages_applied: str = ""  # e.g. "S2(Bayes) S3(smooth)"
    correction_basis: str = ""
    edition: int = 0
    h4_gap_active: bool = False
    tier1_denial_active: bool = False
    no_observable_prep_action: bool = False
    independent_chains: int = 2  # default assumes sufficient chains
    single_cluster_h5: bool = False  # AI-010 trigger


# ── PREDICTION ───────────────────────────────────────────────────────────────

@dataclass
class Prediction:
    """A named prediction entry (open or resolved)."""
    pred_ref: str                    # e.g. "PRED-034-A"
    flag: str                        # descriptive flag text
    window: str                      # e.g. "Before 30 Apr"
    status: str                      # e.g. "OPENED Ed033"
    disconfirmation_statement: str   # how to falsify
    outcome: Optional[PredictionOutcome] = None
    fi: Optional[float] = None       # forecast probability at resolution
    oi: Optional[float] = None       # outcome (1.0/0.0/0.5)
    brier_contribution: Optional[float] = None  # (fi - oi)^2
    resolution_edition: Optional[int] = None
    notes: str = ""


# ── BRIER TABLE ROW ─────────────────────────────────────────────────────────

@dataclass
class BrierRow:
    """One row of the running Brier score table."""
    pred_ref: str
    fi: float
    oi: float
    squared_error: float
    edition: int
    notes: str = ""


# ── CAUSAL EDGE ──────────────────────────────────────────────────────────────

@dataclass
class CausalEdge:
    """AI-012-1: Causal Edge Tracking register entry."""
    cause: str
    effect: str
    prior_strength: float
    observed_signal: float  # 1.0 confirmed / 0.0 contradicted / 0.5 ambiguous
    new_strength: float
    edition: int


# ── DELTA BUFFER ENTRY ───────────────────────────────────────────────────────

@dataclass
class DeltaEntry:
    """AI-012-2: One delta value in the rolling buffer."""
    hyp_id: str
    edition: int
    delta_p: float


# ── CHANGE POINT FLAG ────────────────────────────────────────────────────────

@dataclass
class ChangePointFlag:
    """AI-012-3: Change point detection record."""
    hyp_id: str
    edition: int
    delta_p: float
    mean_delta: float
    std_delta: float
    z_score: float
    flag_raised: bool
    resolution: str = ""
    active: bool = True


# ── CORRELATION MATRIX ENTRY ─────────────────────────────────────────────────

@dataclass
class CorrelationEntry:
    """AI-012-4: One cell in the correlation matrix."""
    hyp_a: str
    hyp_b: str
    raw_correlation: float
    shrinkage_factor: float  # n / 20
    effective_correlation: float
    n: int
    edition: int


# ── PROPAGATION RULE ─────────────────────────────────────────────────────────

@dataclass
class PropagationRule:
    """AI-012-5: Cross-case propagation register entry."""
    trigger_hyp: str
    direction: str       # "UP" or "DOWN"
    downstream_hyp: str
    adjustment: float
    condition: str       # e.g. "H-B2 rises > 0.05"
    active: bool = False
    applied_edition: Optional[int] = None


# ── EMA BAND ERROR ───────────────────────────────────────────────────────────

@dataclass
class EMABandError:
    """AI-012-7: Brier/EMA calibration per band."""
    band: str
    ema_error_prior: float
    current_error: float
    ema_error_updated: float
    edition: int


# ── PER-BAND LOOKUP ENTRY ───────────────────────────────────────────────────

@dataclass
class PerBandLookup:
    """AI-012-9: Per-band calibration lookup table entry."""
    band: str
    pred_freq: int
    obs_freq: int
    obs_rate: Optional[float]
    ema_error: float
    adjustment: float
    min_n_status: str  # "INDICATIVE", "OPERATIONAL", "NO DATA"
    edition: int


# ── RL BANDIT Q-TABLE ENTRY ──────────────────────────────────────────────────

@dataclass
class QTableEntry:
    """AI-012-6: RL Bandit Q-table entry."""
    band: str
    current_factor: float
    q_value: float
    status: str  # "INDICATIVE", "OPERATIONAL", "GOVERNING"
    edition: int


# ── FEED SWEEP RESULT ────────────────────────────────────────────────────────

@dataclass
class FeedSweepResult:
    """Result from checking one of the 18 named feeds."""
    feed_name: str
    tier: int
    checked: bool
    findings: str = ""
    edition: int = 0
    timestamp: str = ""


# ── GATE RECORD ──────────────────────────────────────────────────────────────

@dataclass
class GateRecord:
    """Pass/fail record for a named gate check."""
    gate_id: str        # e.g. "Gate 0.1"
    gate_name: str
    edition: int
    passed: bool
    details: str = ""
    hyp_id: Optional[str] = None


# ── CARRY-FORWARD FACT ───────────────────────────────────────────────────────

@dataclass
class CarryForwardFact:
    """A carry-forward fact with staleness tracking."""
    fact: str
    last_verified: str
    ed034_action: str
    staleness_days: Optional[int] = None
    edition: int = 0


# ── CASE ─────────────────────────────────────────────────────────────────────

@dataclass
class Case:
    """An active case with its tag and confidence."""
    case_id: str       # e.g. "A"
    title: str
    tag: str           # e.g. "ESCALATING"
    confidence: str    # e.g. "MEDIUM"
    notes: str = ""


# ── CALIBRATION MAP ENTRY ────────────────────────────────────────────────────

@dataclass
class CalibrationMapEntry:
    """One row of the AI-007 calibration map."""
    hyp_id: str
    prior_range: str
    new_range: str
    point_estimate: float
    pipeline_stages: str
    correction_basis: str
    edition: int


# ── HPT ENTRY ────────────────────────────────────────────────────────────────

@dataclass
class HPTEntry:
    """Heuristic Performance Tracking row."""
    edition: str
    case_a: str
    case_b: str
    case_c: str
    case_d: str
    case_e: str
    outcome_correlation: str


# ── DEVIATION AUDIT RESULT ───────────────────────────────────────────────────

@dataclass
class DeviationAuditResult:
    """Result of one deviation audit item."""
    item_number: int
    description: str
    passed: bool
    notes: str = ""


# ── DISCONFIRMATION THRESHOLD ────────────────────────────────────────────────

@dataclass
class DisconfirmationThreshold:
    """Standing disconfirmation threshold entry."""
    case_id: str
    threshold: str
    effect: str


# ── PLM ENTRY ────────────────────────────────────────────────────────────────

@dataclass
class PLMEntry:
    """Process Log Memo entry."""
    entry_id: str
    edition: str
    issue: str


# ── PMM ENTRY ────────────────────────────────────────────────────────────────

@dataclass
class PMMEntry:
    """Analytical PMM Log entry."""
    entry_id: str
    pred_ref: str
    outcome: str
    what_failed: str
    why: str
    system_change: str
    heuristic: str


# ── EDITION RECORD ───────────────────────────────────────────────────────────

@dataclass
class EditionRecord:
    """Record of a completed edition."""
    edition_number: int
    sweep_descriptor: str
    gmt_timestamp: str
    bst_timestamp: str
    war_day: int
    brier_score: Optional[float] = None
    n_predictions: int = 0
    architecture_version: str = "v1.3.0"
