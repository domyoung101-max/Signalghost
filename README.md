# Signalghost — Deterministic Forecasting Execution System

## What This System Is

Signalghost (codebase: Project HiveMind) is a highly disciplined forecasting engine, rulebook, and live geopolitical probability tracker. This Python implementation converts the Signalghost SESSION\_STATE (Edition 033) into a deterministic execution system. Every probability published passes through a 13-stage calibration pipeline. Every prediction is falsifiable, tracked, and scored. Every failure is logged and generates a system change.**Primary objective:** Brier score reduction toward elite forecasting performance (BS < 0.10).

**Architecture:** v1.3.0 · GMT primary · SQLite persistence

## File Tree

```
signalghost/
├── main.py                  # Entry point — runs one complete edition
├── session\\\_executor.py      # Orchestrates full session in chronological order
├── config.py                # All constants, failure modes, heuristics, bands, feeds, gates
├── models.py                # Dataclasses for all named structures
├── persistence.py           # SQLite schema and CRUD for all carry-forward tables
├── timestamping.py          # Mandatory GMT timestamp capture (first action every session)
├── chronology.py            # War day verification, edition chronology, staleness
├── feeds.py                 # 18 named feeds by tier, sweep execution (adapters TODO)
├── gates.py                 # All 7 named gates as explicit functions
├── calibration\\\_pipeline.py  # 13-stage pipeline — all named stages as functions
├── calibration\\\_state.py     # Ed033 seed data for all carry-forward registers
├── predictions.py           # Brier/Log/Spherical scoring, prediction resolution, PMM-004
├── pdf\\\_builder.py           # PDF generation enforcing 10 mandatory architecture items
├── handover.py              # SESSION\\\_STATE handover generator for next edition
├── narration\\\_client.py      # Claude API for optional prose (never for mechanics)
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## How It Maps to the SESSION\_STATE

|SESSION\_STATE Section|Implementation|
|-|-|
|WHAT THIS SYSTEM IS|config.py constants, README|
|LIVE GMT TIMESTAMP|timestamping.py — mandatory first action|
|PLATFORM|config.py (SYSTEM\_NAME, ARCHITECTURE\_VERSION, targets)|
|CRITICAL PROCESS RULES|config.py (AI\_005\_RULE, OPERATOR\_GOVERNANCE\_RULES)|
|MANDATORY PDF ARCHITECTURE|pdf\_builder.py — validates all 10 items before build|
|CHRONOLOGY VERIFICATION|chronology.py — arithmetic + online verification|
|OPERATOR GOVERNANCE RULES|config.py (named failure modes as FailureMode enum)|
|SOURCING FRAMEWORK|feeds.py — 18 named feeds, adapters per feed|
|AI-010 RULE|calibration\_pipeline.py: ai\_010\_single\_cluster\_h5\_discount()|
|CALIBRATION DOCTRINE AI-007|config.py bands, calibration\_pipeline.py: ai\_007\_hard\_ceiling\_check()|
|GATE REGISTRY|gates.py — all 7 gates as named functions|
|CALIBRATION PIPELINE|calibration\_pipeline.py — 13 stages in order|
|AI-012 Enhancements|calibration\_pipeline.py (9 enhancements as named functions)|
|CALIBRATION MAP|calibration\_state.py (Ed033 seed), persistence.py schema|
|Brier Score Framework|predictions.py — BS, LS, SS computation|
|PLM / PMM|config.py (seed entries), persistence.py schema|
|Prediction Log|persistence.py schema, predictions.py resolution|
|Carry-Forward Facts|persistence.py schema, calibration\_state.py seed|
|Deviation Audit (28 items)|config.py (DEVIATION\_AUDIT\_ITEMS), session\_executor.py|
|Session Handoff|handover.py — full SESSION\_STATE markdown generation|
|Narration (optional)|narration\_client.py — Claude API for prose only|

## First Run Commands (Windows PowerShell)

```powershell
# Create virtual environment
python -m venv .venv
.\\\\.venv\\\\Scripts\\\\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Set API key (optional — system runs without it)
$env:ANTHROPIC\\\_API\\\_KEY = "sk-ant-..."

# Initialize database with Ed033 seed data
python main.py --init-only

# Run one full edition (Ed034)
python main.py
```

## First Run Commands (Linux/macOS)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Set API key (optional — system runs without it)
export ANTHROPIC\\\_API\\\_KEY="sk-ant-..."

# Initialize database with Ed033 seed data
python main.py --init-only

# Run one full edition (Ed034)
python main.py
```

## Key Design Decisions

1. **SQLite for persistence** — all carry-forward state survives across editions
2. **Claude API only for prose** — narration\_client.py is isolated; all mechanics are deterministic Python
3. **Feed adapters are TODO** — each of 18 feeds has a named placeholder function ready for real RSS/API integration
4. **PDF uses ReportLab** — falls back to text report if unavailable
5. **Every named item from SESSION\_STATE has a code/schema/validation slot** — see COVERAGE MATRIX below

## Architecture Notes

* **13-stage pipeline** executes in strict order per SESSION\_STATE v1.3.0
* **7 named gates** execute in the documented sequence (0.1→0.2→0.5→0.3→0.4→0.6→5)
* **5 named failure modes** encoded as FailureMode enum
* **7 heuristics (H1-H7)** encoded in config
* **28-item deviation audit** checked before every PDF build
* **AI-007 hard ceilings cannot be overridden by AI-012** — enforced in code
* **AI-012-10 Publication Integrity Lock** is the final numerical constraint — Stage 13
* **PMM-004** is a mandatory governing rule with explicit code enforcement

