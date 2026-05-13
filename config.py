"""config.py — Signalghost configuration constants.

Every named constant, version string, band boundary, feed tier, failure mode,
heuristic, deviation-audit item, and system-change-log entry from the
SESSION_STATE is encoded here. Nothing is summarised or compressed.
"""

from enum import Enum, auto
from typing import Dict, List, Tuple

# ── SYSTEM IDENTITY ──────────────────────────────────────────────────────────

PRODUCT_NAME = "Signalghost"
CODEBASE_NAME = "PROJECT HIVEMIND"
OPERATOR_TZ = "BST"  # UTC+1 (late March–late October)
ARCHITECTURE_VERSION = "v1.3.0"

# ── NARRATION / MODEL CONFIG (ADDED) ─────────────────────────────────────────

# Primary model for final analytical narration to PDF (also used for feed fallback).
MODEL_FINAL_NARRATION = "claude-sonnet-4-5"

# Token ceilings for narration sections (upper bounds; prompts also enforce word ceilings).
NARRATION_DEFAULT_MAX_TOKENS = 320
NARRATION_MAXTOK_EXECUTIVE_SUMMARY = 220
NARRATION_MAXTOK_SITUATION_OVERVIEW = 320
NARRATION_MAXTOK_PCP_STEP_1_5 = 220
NARRATION_MAXTOK_H1_SATURATION = 192
NARRATION_MAXTOK_CASE_PART1 = 384
NARRATION_MAXTOK_CASE_PART2 = 320
NARRATION_MAXTOK_CASE_PART3 = 288
NARRATION_MAXTOK_CASE_PART4 = 288
NARRATION_MAXTOK_CASE_PART5 = 192
NARRATION_MAXTOK_CASE_PART6 = 160
NARRATION_MAXTOK_CRITICAL_WINDOWS = 256
NARRATION_MAXTOK_DOMAIN_QUALITY = 128

# ── WAR DAY ORIGIN ───────────────────────────────────────────────────────────

WAR_START_YEAR = 2026
WAR_START_MONTH = 2
WAR_START_DAY = 28  # 28 February 2026 = Day 1

# ── BRIER SCORE TARGETS ─────────────────────────────────────────────────────

BS_TARGET_OPERATIONAL = 0.15
BS_TARGET_SUSTAINED = 0.12
BS_TARGET_ELITE = 0.10
BS_BASELINE = 0.25

# ── LOG SCORE / SPHERICAL SCORE TARGETS ──────────────────────────────────────

LS_TARGET = -0.20
LS_BASELINE = -0.693  # ln(0.5)
SS_TARGET = 0.90
SS_BASELINE = 0.500

# ── AI-007 CALIBRATION DOCTRINE — BAND GOVERNANCE ───────────────────────────

AI_007_HARD_CEILING = 0.85
AI_007_FORMAL_CONFIRMATION_FLOOR = 0.90

CONFIDENCE_BANDS: Dict[str, Tuple[float, float]] = {
    "BLACK_SWAN": (0.00, 0.24),
    "LOW": (0.25, 0.39),
    "LOW_MEDIUM": (0.40, 0.54),
    "MEDIUM": (0.55, 0.69),
    "HIGH": (0.70, 0.89),
    "FORMAL_ONLY": (0.90, 1.00),
}

CONFIDENCE_MEDIUM_CEILING_THRESHOLD = 0.60

# ── PER-BAND LOOKUP TABLE BANDS ─────────────────────────────────────────────

LOOKUP_BANDS: List[Tuple[float, float, str]] = [
    (0.00, 0.10, "0-10%"),
    (0.10, 0.20, "10-20%"),
    (0.20, 0.30, "20-30%"),
    (0.30, 0.40, "30-40%"),
    (0.40, 0.60, "40-60%"),
    (0.60, 0.70, "60-70%"),
    (0.70, 0.80, "70-80%"),
    (0.90, 1.00, "90-100%"),
]

LOOKUP_BAND_DEFAULT_LABEL = "40-60%"

# ── AI-012 PIPELINE PARAMETERS ───────────────────────────────────────────────

CAUSAL_EDGE_OLD_WEIGHT = 0.7
CAUSAL_EDGE_NEW_WEIGHT = 0.3
CAUSAL_EDGE_ESTABLISHED_THRESHOLD = 0.70

DELTA_BUFFER_SIZE = 5
DELTA_MIN_ENTRIES_FOR_CHANGE_POINT = 3

CHANGE_POINT_Z_THRESHOLD = 2.0

CORRELATION_SHRINKAGE_N_MAX = 20
CORRELATION_MIN_N = 5

PROPAGATION_DELTA_THRESHOLD = 0.05

RL_ALPHA = 0.1
RL_EPSILON = 0.1
RL_GOVERNING_N = 30
RL_OPERATIONAL_N = 10
RL_INDICATIVE_BAND_N = 5

EMA_OLD_WEIGHT = 0.9
EMA_NEW_WEIGHT = 0.1
EMA_MIN_N_FULL_RANGE = 10
EMA_MIN_N_CAP = 5
EMA_CAP_VALUE = 0.03

PUB_LOCK_H4_GAP_CAP = 0.50
PUB_LOCK_CHAIN_CAP = 0.60

AI_010_DISCOUNT_MIN_PP = 0.10

# ── EVIDENCE WEIGHT LADDER — PER-TIER LR RANGES (Rule 3 + Gate 0.4) ────────
# Tier 1: Government primary — widest range, load-bearing
# Tier 2: Named journalist — moderate range
# Tier 3: State-affiliated — narrow range, corroboration required
# Tier 4: Aggregator (Wikipedia/ACLED) — directional only, tightest range
# Gate 0.4 extension: Tier 1 with HIGH incentive and no competing primary
#   must be downgraded to Tier 2 range.
TIER_LR_RANGES: Dict[int, Tuple[float, float]] = {
    1: (0.33, 3.00),
    2: (0.50, 2.00),
    3: (0.67, 1.50),
    4: (0.83, 1.20),
}
TIER_LR_DEFAULT = (0.67, 1.50)  # fallback if tier unknown — conservative

# HIGH-incentive Tier 1 sources (state media posing as primary).
# If a Tier 1 feed has HIGH incentive AND no independent competing Tier 1
# source corroborates the same claim, clamp to Tier 2 range.
TIER1_HIGH_INCENTIVE_FEEDS: List[str] = [
    "irna", "tasnim", "mehr", "press tv", "fars",
    "wana", "al arabiya", "house of saud",
]

GATE_0_2_TIER3_PP_TRIGGER = 0.05
GATE_0_3_THRESHOLD = 0.60
GATE_0_4_THRESHOLD = 0.70
GATE_0_4_CORRELATION_THRESHOLD = 0.30
GATE_0_4_PARTNER_FLOOR = 0.35
GATE_0_6_ROCKET_THRESHOLD = 100

PMM_004_ADJUSTMENT_PP = -0.10

# ── SWEEP DESCRIPTORS ────────────────────────────────────────────────────────

SWEEP_MORNING = "MORNING SWEEP"
SWEEP_AFTERNOON = "AFTERNOON SWEEP"
SWEEP_EVENING = "EVENING SWEEP"
SWEEP_LATE_NIGHT = "LATE NIGHT SWEEP"

SWEEP_HOUR_RANGES = [
    (5, 12, SWEEP_MORNING),
    (12, 17, SWEEP_AFTERNOON),
    (17, 21, SWEEP_EVENING),
    (21, 24, SWEEP_LATE_NIGHT),
]

# ── FAILURE MODES ────────────────────────────────────────────────────────────

class FailureMode(Enum):
    THEATRE_OF_RIGOR = auto()
    CLAIM_TYPE_CONFLATION = auto()
    SOURCE_AMPLIFICATION = auto()
    ESCAPE_HATCH_ASSIGNMENT = auto()
    EFFICIENCY_DRIFT = auto()


FAILURE_MODE_DESCRIPTIONS: Dict[FailureMode, str] = {
    FailureMode.THEATRE_OF_RIGOR:
        "Skeleton appearance prioritised over consistent execution.",
    FailureMode.CLAIM_TYPE_CONFLATION:
        "Facts, inferences, and predictions presented in undifferentiated prose, creating false certainty.",
    FailureMode.SOURCE_AMPLIFICATION:
        "Treating multiple downstream echoes of a single upstream source as independent corroboration.",
    FailureMode.ESCAPE_HATCH_ASSIGNMENT:
        "Using WATCH, PARTIAL, AMBIGUOUS, or DIRECTIONAL labels to preserve preferred narrative when disconfirmation evidence is present.",
    FailureMode.EFFICIENCY_DRIFT:
        "System is pressured toward simplification, document compression, or architectural shortcuts that sacrifice precision, robustness, and governance. Named instance Ed031.",
}

# ── HYPOTHESIS STATUS ENUM ───────────────────────────────────────────────────

class HypothesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    CONFIRMED = "CONFIRMED"
    CONTRADICTED = "CONTRADICTED"
    NEAR_CONFIRMED_PROVISIONAL = "NEAR-CONFIRMED PROVISIONAL"

# ── PREDICTION OUTCOME ENUM ──────────────────────────────────────────────────

class PredictionOutcome(Enum):
    CONFIRMED = "CONFIRMED"
    CONTRADICTED = "CONTRADICTED"
    PARTIAL = "PARTIAL"
    AMBIGUOUS = "AMBIGUOUS"
    DIRECTIONAL = "DIRECTIONAL"
    PENDING = "PENDING"
    WATCH = "WATCH"
    OPENED = "OPENED"
    AT_RISK = "AT RISK"
    NEAR_CONTRADICTED = "NEAR-CONTRADICTED"
    PARTIALLY_PROGRESSING = "PARTIALLY PROGRESSING"


OUTCOME_VALUES = {
    PredictionOutcome.CONFIRMED: 1.0,
    PredictionOutcome.CONTRADICTED: 0.0,
    PredictionOutcome.PARTIAL: 0.5,
}

# ── HEURISTICS (H1–H7) ──────────────────────────────────────────────────────

HEURISTICS: Dict[str, str] = {
    "H1": "INCENTIVE MISMATCH — Who benefits from this narrative being believed?",
    "H2": "TIMING CONVERGENCE — Why now? What concurrent events explain this timing?",
    "H3": "BENEFICIARY ASYMMETRY — Who gains disproportionately vs who appears to be acting?",
    "H4": "NARRATIVE VS OUTCOME GAP — Do both parties' accounts agree?",
    "H5": "STRUCTURAL CONTRADICTION — Do stated positions contain claims that cannot simultaneously be true?",
    "H6": "SUPPRESSED INTERSECTION — Are two developments sharing a common actor, motive, or dependency not being named?",
    "H7": "ANCHORING RISK — If this were the first edition, what probability would I assign?",
}

# ── FEED TIERS ───────────────────────────────────────────────────────────────

FEED_TIERS: Dict[str, List[str]] = {
    "TIER_1": [
        "Trump Truth Social / White House official statements",
        "CENTCOM public affairs",
        "IDF official statements",
        "Iran SNSC / IRNA (named attribution)",
        "Named government spokesperson statements",
    ],
    "TIER_2": [
        "Reuters", "AP", "Bloomberg", "Al Jazeera",
        "NBC News live updates", "CBS News live updates", "NPR",
    ],
    "TIER_3": [
        "Tasnim News Agency (IRGC-linked)", "Mehr News Agency",
        "WANA News Agency", "House of Saud / Conflict Pulse",
    ],
    "TIER_4": [
        "Wikipedia", "ACLED conflict monitor",
    ],
}

TOTAL_NAMED_FEEDS = 18

# ── MANDATORY PDF ITEMS ─────────────────────────────────────────────────────-

MANDATORY_PDF_ITEMS: List[str] = [
    "1. Brier Score / AI-009 section",
    "2. AI-007 Calibration Map",
    "3. No blank pages",
    "4. HPT block",
    "5. PLM section in PDF body",
    "6. PMM section in PDF body",
    "7. AI-009 point estimate table",
    "8. Domain quality assessment",
    "9. Deviation audit block — 28-item checklist",
    "10. Prediction log RESOLVED (cumulative)",
]

# ── DEVIATION AUDIT ITEMS (28) ───────────────────────────────────────────────

DEVIATION_AUDIT_ITEMS: List[str] = [
    "1. GMT timestamp captured from bash tool before any feed",
    "2. War day verified arithmetically",
    "3. War day verified online",
    "4. Sweep descriptor programmatically derived",
    "5. All 18 named feeds checked before analytical content written",
    "6. AI-005: all analytical content to PDF only",
    "7. AI-007 hard ceilings checked (85% cap)",
    "8. H7 anchoring risk checked for all material hypotheses",
    "9. AI-010 single-cluster H5 discount where triggered",
    "10. AI-012 12-stage pipeline executed in order",
    "11. Causal edge register updated (AI-012-1)",
    "12. Delta buffer appended (AI-012-2)",
    "13. Change point z-scores computed (AI-012-3)",
    "14. Correlation matrix updated (AI-012-4)",
    "15. Propagation register checked (AI-012-5)",
    "16. EMA errors updated (AI-012-7)",
    "17. Per-band lookup table checked (AI-012-9)",
    "18. Band adjustments applied (AI-012-8)",
    "19. RL Bandit Q-table noted (AI-012-6 — ADVISORY)",
    "20. All 10 mandatory PDF items present (AI-011)",
    "21. No blank pages",
    "22. HPT block present",
    "23. PLM section present in PDF body",
    "24. PMM section present in PDF body",
    "25. Bypass audit: no bypasses, no silent omissions",
    "26. Gate 0.2 Source Corroboration Applied Where Triggered",
    "27. Gate 0.3 Incentive Analysis Completion Verified",
    "28. Gate 0.4 Cross-Case Consistency Resolved",
]

# ── OPERATOR GOVERNANCE RULES ────────────────────────────────────────────────

OPERATOR_GOVERNANCE_RULES: List[str] = [
    "1. DO NOT drift semantically.",
    "2. DO NOT perform any action other than what the operator has strictly asked for.",
    "3. DO NOT hallucinate.",
    "4. DO NOT be sycophantic.",
    "5. DO NOT resolve sweep content in chat. AI-005 absolute.",
    "6. The defined CDIT architecture is governing.",
    "7. Chronology is never assumed. Verify online.",
    "8. All 10 mandatory PDF items must be present in every build.",
    "9. Response must be complete.",
    "10. This list is non-exhaustive.",
]

# ── SYSTEM CHANGE LOG ENTRIES ────────────────────────────────────────────────

SYSTEM_CHANGE_LOG_ENTRIES: List[Dict[str, str]] = [
    {"entry": "001", "summary": "Named-party predictions require incentive analysis before C3.", "in_force": "Ed014"},
    {"entry": "AI-001", "summary": "Case B standing.", "in_force": "Ed018"},
    {"entry": "AI-002", "summary": "Wikipedia Tier 4 only.", "in_force": "Ed019"},
    {"entry": "AI-003", "summary": "Gate 0.5, H1 saturation check, PCP Step 1.5.", "in_force": "Ed019"},
    {"entry": "AI-004", "summary": "All rule changes logged before in force.", "in_force": "Ed019"},
    {"entry": "AI-005", "summary": "PDF brief mandatory. Analysis to PDF ONLY.", "in_force": "Ed022"},
    {"entry": "AI-006", "summary": "Part 4 TQL mandatory every case every edition.", "in_force": "Ed023"},
    {"entry": "AI-007", "summary": "Calibration doctrine. Band governance. 85% cap.", "in_force": "Ed027"},
    {"entry": "AI-008", "summary": "Architecture alignment. Full CDIT, 18 named feeds.", "in_force": "Ed029"},
    {"entry": "AI-009", "summary": "Brier score optimisation. Old shrinkage RETIRED Ed031.", "in_force": "Ed029"},
    {"entry": "AI-010", "summary": "Single-cluster H5 discount. Minimum 10pp.", "in_force": "Ed030"},
    {"entry": "AI-011", "summary": "Mandatory PDF architecture — 10 items. Deviation audit 28 items.", "in_force": "Ed031"},
    {"entry": "AI-012", "summary": "NINE CALIBRATION ENHANCEMENTS. 12-stage pipeline. v1.3.0.", "in_force": "Ed031"},
    {"entry": "PMM-004", "summary": "GOVERNING RULE: H4 gap + no prep action → −10pp.", "in_force": "Ed034"},
    {"entry": "Gate 0.2", "summary": "Source Corroboration Requirement.", "in_force": "Ed034"},
    {"entry": "Gate 0.3", "summary": "Incentive Analysis Completion.", "in_force": "Ed034"},
    {"entry": "Gate 0.4", "summary": "Cross-Case Consistency Check.", "in_force": "Ed034"},
    {"entry": "AI-012-10", "summary": "PUBLICATION INTEGRITY LOCK.", "in_force": "Ed035"},
]

# ── PLM ENTRIES (PROCESS LESSONS MEMO) ───────────────────────────────────────

PLM_ENTRIES: List[Dict[str, str]] = [
    {"entry": "PLM-001", "edition": "Ed025 Morning", "issue": "Build script pre-existed. Session resumed mid-build."},
    {"entry": "PLM-002", "edition": "Ed025 Evening", "issue": "Session state truncated in chat. PDF built correctly."},
    {"entry": "PLM-003", "edition": "Ed026 Morning", "issue": "flag_block() missing styles argument."},
    {"entry": "PLM-004", "edition": "Ed028 Pre-Sweep", "issue": "SESSION_STATE.md regenerated at operator request."},
    {"entry": "PLM-005", "edition": "Ed028 Late Afternoon", "issue": "story.extend() required for flag_block()/source_block()."},
    {"entry": "PLM-006", "edition": "Ed029 Evening", "issue": "SESSION_STATE.md corrupted by operator tool."},
    {"entry": "PLM-007", "edition": "Ed030 Morning", "issue": "AI-005 violation: analytical content in chat."},
    {"entry": "PLM-008", "edition": "Ed030 Initial", "issue": "War Day shown as 57 — corrected to 56."},
    {"entry": "PLM-009", "edition": "Ed030/031", "issue": "10 missing items from Ed029 PDF. AI-011 introduced."},
    {"entry": "PLM-010", "edition": "Ed031", "issue": "Nine calibration enhancements added. v1.3.0."},
    {"entry": "PLM-011", "edition": "Ed032 Morning", "issue": "styles.py and build_core.py recreated from context."},
    {"entry": "PLM-012", "edition": "Ed033 Evening", "issue": "Ed032 PDF never completed. Ed033 from Ed031 baseline."},
    {"entry": "PLM-013", "edition": "26 April 2026", "issue": "Gates 0.2/0.3/0.4 absent across 33 editions. Identified by Dominic Young."},
]

# ── PMM ENTRIES (PREDICTION MISTAKE MEMO) ────────────────────────────────────

PMM_ENTRIES: List[Dict[str, str]] = [
    {
        "entry": "PMM-001",
        "pred_ref": "PRED-012-B",
        "outcome": "CONTRADICTED",
        "what_failed": "Named-source prediction without incentive analysis.",
        "why": "H1 not applied before C3.",
        "system_change": "Named-party predictions require incentive analysis before C3.",
        "heuristic": "H1 — misapplication",
    },
    {
        "entry": "PMM-002",
        "pred_ref": "PRED-026-E",
        "outcome": "CONTRADICTED",
        "what_failed": "First Yanbu strike carried PENDING through Ed026.",
        "why": "Gate 0.1 temporal currency check failed.",
        "system_change": "Gate 0.1 mandatory for all absence claims.",
        "heuristic": "H4 — narrative vs outcome gap",
    },
    {
        "entry": "PMM-003",
        "pred_ref": "PRED-022-A through PRED-029-A (x6)",
        "outcome": "CONTRADICTED",
        "what_failed": "H-A1 at 72-82% on Iranian-source cluster.",
        "why": "Gate 0.5 cluster risk underweighted.",
        "system_change": "AI-010: single-cluster H5 discount minimum 10pp.",
        "heuristic": "H4 — narrative vs outcome gap",
    },
    {
        "entry": "PMM-004",
        "pred_ref": "PRED-031-A",
        "outcome": "CONTRADICTED",
        "what_failed": "H-A1 at 72-82% with active Tier 1 Iranian denial.",
        "why": "H4 gap was governing signal. Gate 0.3 absent.",
        "system_change": "MANDATORY GOVERNING RULE from Ed034. Gate 0.3 + Gate 0.2 now in force.",
        "heuristic": "H4/H6",
    },
]

# ── GATE EXECUTION ORDER ─────────────────────────────────────────────────────

GATE_EXECUTION_ORDER = [
    {"sequence": 1, "gate": "Gate 0.1", "name": "Temporal Currency Check", "stage": "Pre-analysis"},
    {"sequence": 2, "gate": "Gate 0.2", "name": "Source Corroboration Requirement", "stage": "Pre-analysis"},
    {"sequence": 3, "gate": "Gate 0.5", "name": "Cluster Risk Check", "stage": "Pre-analysis"},
    {"sequence": 4, "gate": "Gate 0.3", "name": "Incentive Analysis Completion", "stage": "Pre-publication (>60%)"},
    {"sequence": 5, "gate": "Gate 0.4", "name": "Cross-Case Consistency Check", "stage": "Pre-publication (>70%)"},
    {"sequence": 6, "gate": "Gate 0.6", "name": "Absence / Threshold Gate", "stage": "Per-edition verification"},
    {"sequence": 7, "gate": "Gate 5", "name": "Resolution Gate", "stage": "Prediction resolution only"},
]

# ── PIPELINE STAGES ──────────────────────────────────────────────────────────

PIPELINE_STAGES = [
    {"stage": 1, "code": "AI-010", "name": "Single-cluster H5 discount"},
    {"stage": 2, "code": "AI-009", "name": "Bayesian update"},
    {"stage": 3, "code": "AI-012-1", "name": "Causal edge smoothing"},
    {"stage": 4, "code": "AI-012-2", "name": "Delta statistics update"},
    {"stage": 5, "code": "AI-012-3", "name": "Change point detection"},
    {"stage": 6, "code": "AI-012-4", "name": "Correlation matrix update"},
    {"stage": 7, "code": "AI-012-5", "name": "Cross-case propagation"},
    {"stage": 8, "code": "AI-012-7", "name": "Brier/EMA calibration"},
    {"stage": 9, "code": "AI-012-9", "name": "Per-band lookup table adjustment"},
    {"stage": 10, "code": "AI-012-8", "name": "Band adjustment"},
    {"stage": 11, "code": "AI-007", "name": "Hard ceiling check"},
    {"stage": 12, "code": "AI-012-6", "name": "RL Bandit advisory note"},
    {"stage": 13, "code": "AI-012-10", "name": "Publication Integrity Lock"},
]

# ── META / GOVERNANCE TEXT ───────────────────────────────────────────────────

AI_SELF_EXAMINATION_LIMITATION = (
    "The Signalghost AI component has a documented structural limitation in "
    "prospective self-examination. Reference: PLM-013. Attribution: Dominic Young, 26 April 2026."
)

AI_005_RULE = "ALL ANALYTICAL CONTENT MUST BE OUTPUT TO PDF ONLY. NEVER RESOLVED IN CHAT."

EDITION_WORKFLOW_RULES: List[str] = [
    "1. SESSION_STATE governs the PDF of the same edition number.",
    "2. build_core.py and styles.py are static infrastructure.",
    "3. The companion .py increments with each edition.",
    "4. No sweep may begin before the GMT timestamp is locked.",
    "5. No PDF may be generated before the sweep is complete.",
    "6. No SESSION_STATE update may be written before the PDF is complete.",
    "7. The loop does not terminate.",
]

SESSION_HANDOFF_ITEMS: List[str] = [
    "1. LIVE GMT TIMESTAMP", "2. Full AI-012 pipeline executed",
    "3. Causal edge register updated", "4. Delta buffer updated",
    "5. Change point z-scores computed", "6. Correlation matrix updated",
    "7. Propagation register checked", "8. RL Bandit Q-table updated",
    "9. EMA errors updated", "10. Per-band lookup table recomputed",
    "11. Band adjustments applied", "12. Calibration map documented",
    "13. Prediction log entries updated", "14. Carry-forward facts flagged",
    "15. New rules added to SYSTEM CHANGE LOG", "16. Next edition sweep actions",
    "17. Deviation audit failures as PLM", "18. Prediction failures as PMM",
    "19. All 10 mandatory PDF items verified", "20. War day verified online",
    "21. Resolved prediction log updated", "22. Gate 0.2/0.3/0.4 verified",
]

BUILD_NOTES = {
    "flag_block": "Five positional args. PLM-003.",
    "story_extend": "story.extend() not story.append(). PLM-005.",
    "source_block": "story.extend(source_block([...], styles)). PLM-007.",
}
