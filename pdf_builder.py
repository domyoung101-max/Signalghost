"""pdf_builder.py — Signalghost PDF generation (v2.0.0).

MANDATORY PDF ARCHITECTURE — ALL 10 ITEMS REQUIRED EVERY EDITION:
  1. Brier Score / AI-009 section
  2. AI-007 Calibration Map
  3. No blank pages
  4. HPT block
  5. PLM section in PDF body
  6. PMM section in PDF body
  7. AI-009 point estimate table
  8. Domain quality assessment (body_bold closing every Part 2)
  9. Deviation audit block — 28-item checklist
  10. Prediction log RESOLVED (cumulative)

AI-005: ALL ANALYTICAL CONTENT MUST BE OUTPUT TO PDF ONLY.

Uses build_core.py and styles.py for branded layout matching Ed029 reference.
Falls back to comprehensive text report if ReportLab unavailable.
"""

import datetime
import os
import sys
from typing import Dict, List, Optional


class PDFBuilder:
    """Builds the edition PDF enforcing all 10 mandatory items."""

    def __init__(self, edition: int, sweep_str: str, date_str: str,
                 gmt_str: str, war_day: int):
        self.edition = edition
        self.sweep_str = sweep_str
        self.date_str = date_str
        self.gmt_str = gmt_str
        self.war_day = war_day
        self.output_path = f"Signalghost_Ed{edition:03d}_{sweep_str.replace(' ', '_')}.pdf"

        # Dynamic status bar — populated by session_executor before build.
        # Default fallback values shown only if executor doesn't override.
        self.status_bar_slot_1_label = "EDITION"
        self.status_bar_slot_1_value = f"{edition:03d}"
        self.status_bar_slot_2_label = "WAR DAY"
        self.status_bar_slot_2_value = str(war_day)
        self.status_bar_slot_3_label = "DOMINANT SIGNAL"
        self.status_bar_slot_3_value = "ASSESSING"
        self.status_bar_slot_4_label = "DEADLINE"
        self.status_bar_slot_4_value = "—"

        self._mandatory_items = {i: False for i in range(1, 11)}
        self._mandatory_items[3] = True  # No blank pages — verified at build

        # Ordered sections for rendering
        self.sections: List[Dict] = []
        self.bypasses: Dict[str, str] = {}

        # Case narratives (CDIT 6-part structure)
        self.case_narratives: Dict[str, Dict[str, str]] = {}

        # Non-case narrative sections
        self.situation_overview = ""
        self.pcp_step_1_5 = ""
        self.h1_saturation_check = ""
        self.critical_windows = ""
        self.executive_summary = ""

        # Source attribution
        self.source_attributions: List[Dict] = []

        # Active cases summary
        self.active_cases: List[Dict] = []

        # Carry-forward facts
        self.carry_forward_facts: List[Dict] = []

        # Prediction log open
        self.predictions_open: List[Dict] = []

        # Per-case structured hypothesis data for tables
        self.case_hypotheses: Dict[str, List[Dict]] = {}

        # Per-case disconfirmation data for tables
        self.case_disconf: Dict[str, List[tuple]] = {}

        # Per-case fact rows for fact_table
        self.case_facts: Dict[str, List[tuple]] = {}

        # FIX (Items 7+8): Per-case escalation overrides for tag_table
        # Dict: case_id -> {"type": "gate_06_breach"|"change_point", "detail": str}
        self.case_escalations: Dict[str, Dict] = {}

        # FIX (Item 14): Bypass declarations for PDF rendering
        # Dict: case_id -> [{"section": str, "justification": str, "risk": str}]
        self.bypass_declarations: Dict[str, List[Dict]] = {}

        # Cross-edition hypothesis time-series
        self._hypothesis_trend: Dict = {}

    # ── MANDATORY ITEM SETTERS ───────────────────────────────────────────

    def add_brier_score_section(self, scores, brier_rows, per_band_lookup):
        self.sections.append({
            "type": "brier_score", "scores": scores,
            "brier_rows": brier_rows, "per_band_lookup": per_band_lookup,
        })
        self._mandatory_items[1] = True

    def add_calibration_map(self, cal_map):
        self.sections.append({"type": "calibration_map", "entries": cal_map})
        self._mandatory_items[2] = True

    def add_hpt_block(self, hpt_entries):
        self.sections.append({"type": "hpt", "entries": hpt_entries})
        self._mandatory_items[4] = True

    def add_plm_section(self, plm_entries):
        self.sections.append({"type": "plm", "entries": plm_entries})
        self._mandatory_items[5] = True

    def add_pmm_section(self, pmm_entries):
        self.sections.append({"type": "pmm", "entries": pmm_entries})
        self._mandatory_items[6] = True

    def add_point_estimate_table(self, hypotheses):
        self.sections.append({"type": "point_estimates", "hypotheses": hypotheses})
        self._mandatory_items[7] = True

    def add_domain_quality_assessment(self, assessments):
        self.sections.append({"type": "domain_quality", "assessments": assessments})
        self._mandatory_items[8] = True

    def add_deviation_audit(self, audit_results):
        self.sections.append({"type": "deviation_audit", "results": audit_results})
        self._mandatory_items[9] = True

    def add_prediction_log_resolved(self, resolved):
        self.sections.append({"type": "prediction_log_resolved", "resolved": resolved})
        self._mandatory_items[10] = True

    # ── ADDITIONAL CONTENT SETTERS ───────────────────────────────────────

    def set_hypothesis_trend(self, trend_data: Dict):
        """Set cross-edition hypothesis time-series data.
        trend_data: dict from persistence.get_hypothesis_trend()
        """
        self._hypothesis_trend = trend_data

    def set_case_narrative(self, case_id: str, narrative: Dict[str, str]):
        self.case_narratives[case_id] = narrative

    def set_situation_overview(self, text: str):
        self.situation_overview = text

    def set_pcp_step(self, text: str):
        self.pcp_step_1_5 = text

    def set_h1_saturation(self, text: str):
        self.h1_saturation_check = text

    def set_critical_windows(self, text: str):
        self.critical_windows = text

    def set_executive_summary(self, text: str):
        self.executive_summary = text

    def set_source_attributions(self, sources: List[Dict]):
        self.source_attributions = sources

    def set_active_cases(self, cases: List[Dict]):
        self.active_cases = cases

    def set_status_bar(self, slot_3_label: str, slot_3_value: str,
                       slot_4_label: str, slot_4_value: str):
        """Set dynamic status bar slots 3 and 4 (slots 1/2 always Edition/War Day).

        Architecture-compliant: presentation only, does NOT enter Brier math.

        Common usages:
          ("DOMINANT SIGNAL", "PROJECT FREEDOM PAUSED", "DEADLINE", "BEIJING D-7")
          ("THRESHOLD BREACH", "100+ ROCKETS CONFIRMED", "GATE 0.6", "TRIGGERED")
          ("RECENTLY RESOLVED", "PRED-01-D CONFIRMED", "BRIER", "0.18")
        """
        self.status_bar_slot_3_label = slot_3_label
        self.status_bar_slot_3_value = slot_3_value
        self.status_bar_slot_4_label = slot_4_label
        self.status_bar_slot_4_value = slot_4_value

    def set_carry_forward_facts(self, facts: List[Dict]):
        self.carry_forward_facts = facts

    def set_predictions_open(self, preds: List[Dict]):
        self.predictions_open = preds

    def set_case_hypotheses(self, case_id: str, hyps: List[Dict]):
        """Set structured hypothesis data for a case (used by hyp_table)."""
        self.case_hypotheses[case_id] = hyps

    def set_case_disconf(self, case_id: str, rows: List[tuple]):
        """Set disconfirmation rows for a case: [(confirms, contradicts), ...]."""
        self.case_disconf[case_id] = rows

    def set_case_facts(self, case_id: str, rows: List[tuple]):
        """Set fact rows for a case: [(fact_text, source_attribution), ...]."""
        self.case_facts[case_id] = rows

    def set_case_escalation(self, case_id: str, escalation: Dict):
        """FIX (Items 7+8): Set visual escalation override for a case banner.

        escalation: {"type": "gate_06_breach"|"change_point", "detail": str}
        """
        self.case_escalations[case_id] = escalation

    def set_bypass_declarations(self, bypasses: Dict[str, List[Dict]]):
        """FIX (Item 14): Set bypass declarations for PDF rendering.

        bypasses: {case_id: [{"section": str, "justification": str, "risk": str}]}
        """
        self.bypass_declarations = bypasses

    def add_prediction_log_open(self, open_preds):
        self.predictions_open = open_preds

    def add_narrative_section(self, title, content):
        pass  # Handled by specific setters now

    def declare_bypass(self, case_id, item_number, reason):
        key = f"{case_id}_{item_number}"
        if key in self.bypasses:
            raise ValueError(f"Bypass already declared for {key}.")
        self.bypasses[key] = reason

    # ── VALIDATION ───────────────────────────────────────────────────────

    def validate_mandatory_items(self):
        missing = []
        bypassed = []
        for item_num, present in self._mandatory_items.items():
            if not present:
                bypass_key = None
                for k, v in self.bypasses.items():
                    if k.endswith(f"_{item_num}"):
                        bypass_key = k
                        break
                if bypass_key:
                    bypassed.append(f"Item {item_num}: BYPASSED — {self.bypasses[bypass_key]}")
                else:
                    missing.append(f"Item {item_num}")
        return {
            "valid": len(missing) == 0,
            "missing": missing,
            "bypassed": bypassed,
            "all_present": all(self._mandatory_items.values()),
        }

    # ── BUILD ────────────────────────────────────────────────────────────

    def build(self) -> str:
        validation = self.validate_mandatory_items()
        if not validation["valid"]:
            raise ValueError(
                f"Cannot build PDF — missing mandatory items: "
                f"{', '.join(validation['missing'])}. PLM entry mandatory."
            )

        try:
            return self._build_reportlab()
        except Exception as e:
            print(f"  ReportLab build failed ({str(e)[:80]}), falling back to text...")
            return self._build_text_fallback()

    def _build_reportlab(self):
        """Build branded PDF using ReportLab + build_core.py + styles.py."""
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.units import mm

        # Import styles and build_core from the project directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        from styles import make_styles, MARGIN, PAGE_W, PAGE_H, NAVY, TEAL, CHARCOAL, MID_GREY
        from build_core import (
            hr, thin_rule, tag_table, fact_table, hyp_table,
            disconf_table, flag_block, source_block,
            make_page_callbacks, simple_table, simple_table_dark,
        )
        from narration_client import _markdown_to_reportlab

        # Sanitise non-case narrative fields (case parts are already
        # processed via _post_process_narration in the executor).
        for _attr in ('executive_summary', 'situation_overview',
                      'pcp_step_1_5', 'h1_saturation_check',
                      'critical_windows'):
            _raw = getattr(self, _attr, '')
            if _raw:
                setattr(self, _attr, _markdown_to_reportlab(_raw))
        styles = make_styles()
        on_cover, on_page = make_page_callbacks(
            f"{self.edition:03d}", self.sweep_str, self.date_str)

        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=(PAGE_W, PAGE_H),
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=20*mm, bottomMargin=18*mm,
        )

        story = []

        # ── COVER PAGE (all-black background; on_cover paints it) ────────
        # Spacer below the on_cover-drawn header bar / top HIVEMIND mark.
        story.append(Spacer(1, 12*mm))

        # Medium PROJECT HIVEMIND "publisher mark" (centred).
        # Aspect 1774:887 ≈ 2:1, so width=60mm → height=30mm.
        from reportlab.platypus import Image as _RLImage
        _hivemind_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "projecthivemind.png")
        _signalghost_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "signalghost.png")
        if os.path.isfile(_hivemind_path):
            _hm_img = _RLImage(_hivemind_path, width=60*mm, height=30*mm)
            _hm_img.hAlign = 'CENTER'
            story.append(_hm_img)
            story.append(Spacer(1, 6*mm))

        # Large SIGNALGHOST "product hero" (centred, square).
        if os.path.isfile(_signalghost_path):
            _sg_img = _RLImage(_signalghost_path, width=60*mm, height=60*mm)
            _sg_img.hAlign = 'CENTER'
            story.append(_sg_img)
            story.append(Spacer(1, 6*mm))

        story.append(Paragraph(
            f"SIGNALGHOST STRATEGIC INTELLIGENCE BRIEF",
            styles['cover_title_dark']))
        story.append(Paragraph(
            f"EDITION {self.edition:03d} — {self.sweep_str}",
            styles['cover_sub_dark']))
        story.append(Paragraph(
            self.gmt_str,
            styles['cover_sub_dark']))
        story.append(Paragraph(
            f"War Day {self.war_day}",
            styles['cover_meta_dark']))
        story.append(Spacer(1, 6*mm))

        # Stats bar — DYNAMIC (Ed01 reset compliant)
        # Slot 1/2 always show Edition + War Day (chronology anchors).
        # Slot 3/4 are populated by session_executor based on:
        #   - Gate 0.6 threshold breach (highest priority)
        #   - Recently resolved case (CONFIRMED/CONTRADICTED)
        #   - Approaching window deadline (≤72h)
        #   - Otherwise dominant case status
        story.append(simple_table_dark(
            [self.status_bar_slot_1_label, self.status_bar_slot_2_label,
             self.status_bar_slot_3_label, self.status_bar_slot_4_label],
            [[self.status_bar_slot_1_value, self.status_bar_slot_2_value,
              self.status_bar_slot_3_value, self.status_bar_slot_4_value]],
            [40*mm, 30*mm, 50*mm, 40*mm], styles))
        story.append(Spacer(1, 4*mm))

        # Executive summary (light text on black cover).
        if self.executive_summary:
            story.append(Paragraph(self.executive_summary, styles['cover_body_dark']))
            story.append(Spacer(1, 3*mm))

        # Active cases summary table — dark variant for the cover.
        if self.active_cases:
            story.append(Paragraph("ACTIVE CASES — EDITION {0:03d}".format(self.edition),
                                   styles['cover_section_dark']))
            ac_rows = [[c.get("case_id",""), c.get("title","")[:60],
                        c.get("tag",""), c.get("confidence","")]
                       for c in self.active_cases]
            story.append(simple_table_dark(
                ["CASE", "TITLE", "TAG", "CONF"],
                ac_rows, [15*mm, 95*mm, 30*mm, 25*mm], styles))
            story.append(Spacer(1, 3*mm))

        story.append(PageBreak())

        # ── ACRONYM GLOSSARY (CF-7) ──────────────────────────────────────
        story.append(Paragraph("SIGNALGHOST — GLOSSARY OF TERMS",
                               styles['section_head']))
        story.append(hr())
        _glossary = [
            ("PCP",     "Priority Case Protocol"),
            ("TQL",     "Truth Quality Check"),
            ("HPT",     "Heuristic Performance Tracking"),
            ("PLM",     "Process Log Memo"),
            ("PMM",     "Post-Mortem Memo (Predictive Mistake Memo)"),
            ("CDIT",    "Case Detailed Intelligence Template"),
            ("fi",      "Forecast probability (assigned by system)"),
            ("oi",      "Outcome indicator (actual result: 0 or 1)"),
            ("BS",      "Brier Score"),
            ("LS",      "Log Score"),
            ("SS",      "Spherical Score"),
            ("LR",      "Likelihood Ratio"),
            ("EMA",     "Exponential Moving Average"),
            ("RL",      "Reinforcement Learning"),
            ("H1\u2013H7", "Heuristic labels (H1=Incentive Mismatch, H2=Timing, "
                        "H3=Beneficiary Asymmetry, H4=Narrative-Outcome Gap, "
                        "H5=Contradiction, H6=Suppressed Intersection, H7=Anchoring)"),
            ("S2\u2013S13", "Calibration pipeline stage numbers (13-stage)"),
            ("AI-005\u2013012", "Architecture rule reference numbers"),
            ("Gate 0.1\u20130.6", "Gate identifiers in the gate registry"),
            ("Gate 5",  "Prediction resolution gate"),
            ("Pt Est",  "Point Estimate"),
            ("pp",      "Percentage points"),
            ("Prop",    "Propagation (cross-case hypothesis adjustment)"),
            ("Ed0XX",   "Edition number (e.g., Ed011 = Edition 11)"),
            ("PRED-01-X", "Prediction reference (PRED-[batch]-[case])"),
            ("H-A1",    "Hypothesis ID (H-[case][number])"),
            ("GL U",    "General License U (OFAC oil waiver)"),
            ("Conf",    "Confidence level"),
        ]
        story.append(simple_table(
            ["Term", "Definition"],
            [[a, d] for a, d in _glossary],
            [28*mm, 142*mm], styles))
        story.append(PageBreak())

        # ── SITUATION OVERVIEW ───────────────────────────────────────────
        _page4_has_content = False
        if self.situation_overview:
            story.append(Paragraph("SITUATION OVERVIEW — {0}".format(self.gmt_str),
                                   styles['section_head']))
            story.append(hr())
            story.append(Paragraph(self.situation_overview, styles['body']))
            story.append(Spacer(1, 4*mm))
            _page4_has_content = True

        # ── PCP STEP 1.5 ────────────────────────────────────────────────
        if self.pcp_step_1_5:
            story.append(Paragraph("PCP STEP 1.5 — NEW SIGNAL CHECK",
                                   styles['section_head']))
            story.append(Paragraph(self.pcp_step_1_5, styles['body']))
            story.append(Spacer(1, 4*mm))
            _page4_has_content = True

        # ── H1 SATURATION CHECK ──────────────────────────────────────────
        if self.h1_saturation_check:
            story.append(Paragraph("H1 SATURATION CHECK — STANDING RULE",
                                   styles['section_head']))
            story.append(Paragraph(self.h1_saturation_check, styles['body']))
            story.append(Spacer(1, 4*mm))
            _page4_has_content = True

        # ── CALIBRATION MAP (Mandatory Item 2) ──────────────────────────
        for section in self.sections:
            if section["type"] == "calibration_map":
                story.append(Paragraph(
                    "AI-007 CALIBRATION MAP — EDITION {0:03d} CORRECTIONS".format(self.edition),
                    styles['section_head']))
                story.append(hr())
                story.append(Paragraph(
                    "Raw vs calibrated probabilities. Band governance check applied. "
                    "Any hypothesis above 85% requires named explicit formal evidence.",
                    styles['body']))
                cal_rows = [[e.get("hyp_id",""), e.get("prior_range",""),
                             e.get("new_range",""), f"{e.get('point_estimate',0):.2f}",
                             e.get("pipeline_stages","")[:80],
                             e.get("correction_basis","")[:500]]
                            for e in section["entries"]]
                story.append(simple_table(
                    ["Hypothesis", "Prior", "New", "Pt Est", "Pipeline", "Basis"],
                    cal_rows, [18*mm, 22*mm, 22*mm, 16*mm, 36*mm, 56*mm], styles))
                story.append(Spacer(1, 6*mm))
                _page4_has_content = True
                break

        # CF-6: Only break page if content was added — prevents blank page
        if _page4_has_content:
            story.append(PageBreak())

        # ── PER-CASE SECTIONS (FULL CDIT) ────────────────────────────────
        for case in self.active_cases:
            cid = case.get("case_id", "")
            narrative = self.case_narratives.get(cid, {})

            # Tag table header (build_core branded)
            # FIX (Items 7+8): Pass escalation override if this case has one
            case_esc = self.case_escalations.get(cid)
            story.append(tag_table(
                cid, case.get("title", "")[:60],
                case.get("tag", "DEVELOPING"),
                case.get("confidence", "MEDIUM"),
                case_esc, styles))
            story.append(Spacer(1, 3*mm))

            # Part 1 — Fact Table (build_core fact_table + prose)
            if narrative.get("part1_facts") or cid in self.case_facts:
                story.append(Paragraph("PART 1 \u2014 FACT TABLE", styles['section_head']))
                # Structured fact table if available
                if cid in self.case_facts and self.case_facts[cid]:
                    story.append(fact_table(self.case_facts[cid], styles))
                    story.append(Spacer(1, 2*mm))
                # Prose narration
                if narrative.get("part1_facts"):
                    story.append(Paragraph(narrative["part1_facts"], styles['body']))
                story.append(Spacer(1, 3*mm))

            # Part 2 — Incongruity Analysis (prose)
            if narrative.get("part2_incongruity"):
                story.append(Paragraph("PART 2 \u2014 INCONGRUITY ANALYSIS", styles['section_head']))
                story.append(Paragraph(narrative["part2_incongruity"], styles['body']))
                story.append(Spacer(1, 2*mm))

            # Domain quality assessment (Mandatory Item 8 — body_bold closing Part 2)
            dq = self._get_domain_quality(cid)
            if dq:
                story.append(Paragraph(dq, styles['body_bold']))
                story.append(Spacer(1, 3*mm))

            # Part 3 — Hypothesis Set (build_core hyp_table + prose)
            story.append(Paragraph("PART 3 \u2014 HYPOTHESIS SET", styles['section_head']))
            if cid in self.case_hypotheses and self.case_hypotheses[cid]:
                hyps_for_table = self.case_hypotheses[cid]
                story.append(hyp_table(hyps_for_table, styles))
                story.append(Spacer(1, 2*mm))
            if narrative.get("part3_hypotheses"):
                story.append(Paragraph(narrative["part3_hypotheses"], styles['body']))
            story.append(Spacer(1, 3*mm))

            # Part 4 — TQL (prose — structured by AI)
            if narrative.get("part4_tql"):
                story.append(Paragraph(
                    "PART 4 \u2014 TRUTH QUALITY CHECK (TQL) \u2014 AI-006 MANDATORY",
                    styles['section_head']))
                story.append(Paragraph(narrative["part4_tql"], styles['body']))
                story.append(Spacer(1, 3*mm))

            # Part 5 — Disconfirmation (build_core disconf_table + prose)
            story.append(Paragraph("PART 5 \u2014 DISCONFIRMATION", styles['section_head']))
            if cid in self.case_disconf and self.case_disconf[cid]:
                story.append(disconf_table(
                    self.case_disconf[cid],
                    f"Gate 5 \u2014 Case {cid}", styles))
                story.append(Spacer(1, 2*mm))
            if narrative.get("part5_disconfirmation"):
                story.append(Paragraph(narrative["part5_disconfirmation"], styles['body']))
            story.append(Spacer(1, 3*mm))

            # Part 6 — Forward Flag (build_core flag_block + prose)
            story.append(Paragraph("PART 6 \u2014 FORWARD FLAG", styles['section_head']))
            # Find relevant open predictions for this case
            case_preds = [p for p in self.predictions_open
                          if cid.lower() in p.get("pred_ref", "").lower()
                          or cid.lower() in p.get("flag", "").lower()]
            for pred in case_preds[:2]:
                story.extend(flag_block(
                    pred.get("pred_ref", ""),
                    f"{self.edition:03d}",
                    pred.get("flag", "")[:200],
                    f"Window: {pred.get('window', '')} | Status: {pred.get('status', '')}",
                    styles))
                story.append(Spacer(1, 2*mm))
            if narrative.get("part6_forward_flag"):
                story.append(Paragraph(narrative["part6_forward_flag"], styles['body']))
            story.append(Spacer(1, 4*mm))

            # FIX (Item 14): Bypass declarations for this case
            case_bypasses = self.bypass_declarations.get(cid, [])
            if case_bypasses:
                story.append(Paragraph(
                    f"DECLARED BYPASSES — CASE {cid}",
                    styles['section_head']))
                bp_rows = [[
                    b.get("section", ""),
                    b.get("justification", "")[:80],
                    b.get("risk", "")[:40],
                ] for b in case_bypasses]
                story.append(simple_table(
                    ["Section", "Justification", "Risk"],
                    bp_rows, [30*mm, 100*mm, 40*mm], styles))
                story.append(Spacer(1, 3*mm))

            story.append(PageBreak())

        # ── CARRY-FORWARD FACTS ──────────────────────────────────────────
        if self.carry_forward_facts:
            story.append(Paragraph(
                "CARRY-FORWARD FACTS — STATUS AT {0}".format(self.gmt_str),
                styles['section_head']))
            story.append(hr())
            cf_rows = [[f.get("fact","")[:500], f.get("last_verified","")[:80],
                        f.get("ed_action","")[:200]]
                       for f in self.carry_forward_facts[:20]]
            story.append(simple_table(
                ["FACT", "LAST VERIFIED", "NEXT ACTION"],
                cf_rows, [80*mm, 40*mm, 50*mm], styles))
            story.append(Spacer(1, 6*mm))

        # ── CRITICAL WINDOWS ─────────────────────────────────────────────
        if self.critical_windows:
            story.append(Paragraph(
                "CRITICAL WINDOWS — ED{0:03d} PRIORITIES".format(self.edition + 1),
                styles['section_head']))
            story.append(hr())
            story.append(Paragraph(self.critical_windows, styles['body']))
            story.append(Spacer(1, 6*mm))

        # ── PREDICTION LOG — OPEN ────────────────────────────────────────
        if self.predictions_open:
            story.append(Paragraph("PREDICTION LOG — OPEN", styles['section_head']))
            story.append(hr())
            pred_rows = [[p.get("pred_ref",""), p.get("flag","")[:50],
                          p.get("window",""), p.get("status","")[:30]]
                         for p in self.predictions_open]
            story.append(simple_table(
                ["Ref", "Flag", "Window", "Status"],
                pred_rows, [28*mm, 70*mm, 30*mm, 42*mm], styles))
            story.append(Spacer(1, 6*mm))

        story.append(PageBreak())

        # ── BRIER SCORE (Mandatory Item 1) ───────────────────────────────
        for section in self.sections:
            if section["type"] == "brier_score":
                story.append(Paragraph(
                    "BRIER SCORE FRAMEWORK — AI-009 + AI-012 INTEGRATED",
                    styles['section_head']))
                story.append(hr())
                scores = section["scores"]
                story.append(Paragraph(
                    f"Current: BS = {scores.get('brier_score', 'N/A')} "
                    f"(n={scores.get('brier_n', 0)}, {scores.get('brier_status', 'N/A')})",
                    styles['body_bold']))
                story.append(Spacer(1, 3*mm))

                # Point estimate table (Mandatory Item 7)
                for s2 in self.sections:
                    if s2["type"] == "point_estimates":
                        story.append(Paragraph("POINT ESTIMATE TABLE", styles['section_head']))
                        pe_rows = [[h.get("hyp_id",""), h.get("range",""),
                                    f"{h.get('point_estimate',0):.2f}"]
                                   for h in s2["hypotheses"]]
                        story.append(simple_table(
                            ["Hyp", "Range", "Pt Est"],
                            pe_rows, [25*mm, 60*mm, 25*mm], styles))
                        story.append(Spacer(1, 4*mm))
                        break

                # Running Brier table
                story.append(Paragraph("RUNNING BRIER SCORE TABLE", styles['section_head']))
                br_rows = [[r.get("pred_ref",""), f"{r.get('fi',0):.2f}",
                            f"{r.get('oi',0):.1f}", f"{r.get('squared_error',0):.4f}",
                            str(r.get("edition","")), r.get("notes","")[:35]]
                           for r in section["brier_rows"]]
                story.append(simple_table(
                    ["Pred Ref", "fi", "oi", "(fi-oi)^2", "Ed", "Notes"],
                    br_rows, [28*mm, 14*mm, 12*mm, 18*mm, 14*mm, 84*mm], styles))
                story.append(Spacer(1, 4*mm))

                # Per-band lookup table
                if section.get("per_band_lookup"):
                    story.append(Paragraph("PER-BAND CALIBRATION LOOKUP TABLE",
                                           styles['section_head']))
                    pbl_rows = [[r.get("band",""), str(r.get("pred_freq","")),
                                 str(r.get("obs_freq","")),
                                 f"{r.get('ema_error',0):.3f}" if r.get("ema_error") else "",
                                 f"{r.get('adjustment',0):.0%}" if r.get("adjustment") else "0%",
                                 r.get("min_n_status","")]
                                for r in section["per_band_lookup"]]
                    story.append(simple_table(
                        ["Band", "Pred Freq", "Obs Freq", "EMA Error", "Adj", "Status"],
                        pbl_rows, [22*mm, 20*mm, 18*mm, 22*mm, 18*mm, 30*mm], styles))
                story.append(Spacer(1, 6*mm))
                break

        # ── HPT (Mandatory Item 4) ───────────────────────────────────────
        for section in self.sections:
            if section["type"] == "hpt":
                story.append(Paragraph(
                    "HEURISTIC PERFORMANCE TRACKING (HPT)", styles['section_head']))
                story.append(hr())
                hpt_rows = [[e.get("edition",""), e.get("case_a","")[:20],
                             e.get("case_b","")[:20], e.get("case_c","")[:20],
                             e.get("case_d","")[:20], e.get("case_e","")[:20]]
                            for e in section["entries"]]
                story.append(simple_table(
                    ["Edition", "Case A", "Case B", "Case C", "Case D", "Case E"],
                    hpt_rows, [26*mm]*6, styles))
                story.append(Spacer(1, 6*mm))
                break

        # ── HYPOTHESIS TREND (Cross-edition time-series) ─────────────────
        if self._hypothesis_trend:
            story.append(Paragraph(
                "HYPOTHESIS TREND — CROSS-EDITION POINT ESTIMATES",
                styles['section_head']))
            story.append(hr())
            # Build columns: Hyp | Ed001 | Ed002 | ... | EdNNN
            all_editions = sorted(set(
                e["edition"]
                for entries in self._hypothesis_trend.values()
                for e in entries
            ))
            # Show last 6 editions max to fit table width
            display_eds = all_editions[-6:]
            header = ["Hyp"] + [f"Ed{e:03d}" for e in display_eds] + ["Δ"]
            trend_rows = []
            for hid in sorted(self._hypothesis_trend.keys()):
                entries = self._hypothesis_trend[hid]
                ed_map = {e["edition"]: e["point_estimate"] for e in entries}
                row = [hid]
                pts_in_range = []
                for ed in display_eds:
                    pt = ed_map.get(ed)
                    if pt is not None:
                        row.append(f"{pt:.2f}")
                        pts_in_range.append(pt)
                    else:
                        row.append("—")
                # Delta: change from first to last displayed edition
                if len(pts_in_range) >= 2:
                    delta = pts_in_range[-1] - pts_in_range[0]
                    sign = "+" if delta >= 0 else ""
                    row.append(f"{sign}{delta:.2f}")
                else:
                    row.append("—")
                trend_rows.append(row)
            col_count = len(header)
            col_w = [20*mm] + [22*mm] * (col_count - 2) + [18*mm]
            story.append(simple_table(header, trend_rows, col_w, styles))
            story.append(Spacer(1, 6*mm))

        # ── PLM (Mandatory Item 5) ───────────────────────────────────────
        for section in self.sections:
            if section["type"] == "plm":
                story.append(Paragraph("PROCESS LOG MEMO (PLM)", styles['section_head']))
                story.append(hr())
                plm_rows = [[e.get("entry_id",""), e.get("edition",""),
                             e.get("issue","")[:70]]
                            for e in section["entries"]]
                story.append(simple_table(
                    ["Entry", "Edition", "Issue"],
                    plm_rows, [20*mm, 28*mm, 122*mm], styles))
                story.append(Spacer(1, 6*mm))
                break

        # ── PMM (Mandatory Item 6) ───────────────────────────────────────
        for section in self.sections:
            if section["type"] == "pmm":
                story.append(Paragraph("ANALYTICAL PMM LOG", styles['section_head']))
                story.append(hr())
                pmm_rows = [[e.get("entry_id",""), e.get("pred_ref",""),
                             e.get("outcome",""), e.get("what_failed","")[:50]]
                            for e in section["entries"]]
                story.append(simple_table(
                    ["Entry", "Pred Ref", "Outcome", "What Failed"],
                    pmm_rows, [18*mm, 30*mm, 22*mm, 100*mm], styles))
                story.append(Spacer(1, 6*mm))
                break

        # ── PREDICTION LOG RESOLVED (Mandatory Item 10) ──────────────────
        for section in self.sections:
            if section["type"] == "prediction_log_resolved":
                story.append(Paragraph(
                    "PREDICTION LOG — RESOLVED (CUMULATIVE)", styles['section_head']))
                story.append(hr())
                res_rows = [[r.get("pred_ref",""), r.get("outcome",""),
                             r.get("notes","")[:55]]
                            for r in section["resolved"]]
                story.append(simple_table(
                    ["Ref", "Outcome", "Notes"],
                    res_rows, [28*mm, 22*mm, 120*mm], styles))
                story.append(Spacer(1, 6*mm))
                break

        # ── DEVIATION AUDIT (Mandatory Item 9) ───────────────────────────
        for section in self.sections:
            if section["type"] == "deviation_audit":
                story.append(Paragraph(
                    "DEVIATION AUDIT — 28 ITEMS", styles['section_head']))
                story.append(hr())
                da_rows = [[str(r.get("item_number","")),
                            r.get("description","")[:65],
                            "PASS" if r.get("passed") else "FAIL"]
                           for r in section["results"]]
                story.append(simple_table(
                    ["#", "Item", "Status"],
                    da_rows, [10*mm, 130*mm, 20*mm], styles))
                story.append(Spacer(1, 6*mm))
                break

        # ── SOURCE ATTRIBUTION ───────────────────────────────────────────
        if self.source_attributions:
            story.append(Paragraph(
                "SOURCES — EDITION {0:03d} {1}".format(self.edition, self.sweep_str),
                styles['section_head']))
            story.append(hr())
            story.extend(source_block(self.source_attributions, styles))
            story.append(Spacer(1, 6*mm))

        # ── FOOTER LINE ──────────────────────────────────────────────────
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(
            f"Signalghost - Edition {self.edition:03d} - {self.sweep_str} - "
            f"{self.date_str} - {self.gmt_str} - v1.3.0 - War Day {self.war_day} - "
            f"AI-007 CALIBRATION DOCTRINE IN FORCE",
            styles['footer']))

        # Build PDF
        doc.build(story, onFirstPage=on_cover, onLaterPages=on_page)
        return self.output_path

    def _get_domain_quality(self, case_id: str) -> str:
        """Get domain quality assessment for a case."""
        for section in self.sections:
            if section["type"] == "domain_quality":
                assessments = section.get("assessments", {})
                return assessments.get(case_id, "")
        return ""

    def _build_text_fallback(self) -> str:
        """Comprehensive text report when ReportLab unavailable."""
        lines = []
        sep = "=" * 72
        lines.append(sep)
        lines.append(f"SIGNALGHOST STRATEGIC INTELLIGENCE BRIEF")
        lines.append(f"EDITION {self.edition:03d} — {self.sweep_str}")
        lines.append(f"{self.date_str} — {self.gmt_str} — War Day {self.war_day}")
        lines.append(sep)
        lines.append("")

        if self.executive_summary:
            lines.append(self.executive_summary)
            lines.append("")

        # Active Cases
        if self.active_cases:
            lines.append("--- ACTIVE CASES ---")
            for c in self.active_cases:
                lines.append(f"  Case {c.get('case_id','')}: {c.get('title','')} [{c.get('tag','')}] {c.get('confidence','')}")
            lines.append("")

        if self.situation_overview:
            lines.append("--- SITUATION OVERVIEW ---")
            lines.append(self.situation_overview)
            lines.append("")

        if self.pcp_step_1_5:
            lines.append("--- PCP STEP 1.5 — NEW SIGNAL CHECK ---")
            lines.append(self.pcp_step_1_5)
            lines.append("")

        if self.h1_saturation_check:
            lines.append("--- H1 SATURATION CHECK ---")
            lines.append(self.h1_saturation_check)
            lines.append("")

        # Calibration Map
        for section in self.sections:
            if section["type"] == "calibration_map":
                lines.append("--- AI-007 CALIBRATION MAP ---")
                for e in section["entries"]:
                    lines.append(f"  {e.get('hyp_id','')}: {e.get('prior_range','')} -> {e.get('new_range','')} pt={e.get('point_estimate',0):.2f} | {e.get('pipeline_stages','')} | {e.get('correction_basis','')}")
                lines.append("")

        # Per-case CDIT
        for case in self.active_cases:
            cid = case.get("case_id", "")
            narrative = self.case_narratives.get(cid, {})
            lines.append(f"{'='*60}")
            lines.append(f"CASE {cid} — {case.get('title','')} [{case.get('tag','')}] [{case.get('confidence','')}]")
            lines.append(f"{'='*60}")

            for part_key, part_title in [
                ("part1_facts", "PART 1 — FACT TABLE"),
                ("part2_incongruity", "PART 2 — INCONGRUITY ANALYSIS"),
                ("part3_hypotheses", "PART 3 — HYPOTHESIS SET"),
                ("part4_tql", "PART 4 — TRUTH QUALITY CHECK (TQL)"),
                ("part5_disconfirmation", "PART 5 — DISCONFIRMATION"),
                ("part6_forward_flag", "PART 6 — FORWARD FLAG"),
            ]:
                if narrative.get(part_key):
                    lines.append(f"\n{part_title}")
                    lines.append(narrative[part_key])

            dq = self._get_domain_quality(cid)
            if dq:
                lines.append(f"\nDOMAIN QUALITY: {dq}")
            lines.append("")

        # Carry-forward facts
        if self.carry_forward_facts:
            lines.append("--- CARRY-FORWARD FACTS ---")
            for f in self.carry_forward_facts[:20]:
                lines.append(f"  {f.get('fact','')[:60]} | {f.get('last_verified','')} | {f.get('ed_action','')}")
            lines.append("")

        # Critical windows
        if self.critical_windows:
            lines.append("--- CRITICAL WINDOWS ---")
            lines.append(self.critical_windows)
            lines.append("")

        # Prediction log open
        if self.predictions_open:
            lines.append("--- PREDICTION LOG — OPEN ---")
            for p in self.predictions_open:
                lines.append(f"  {p.get('pred_ref','')}: {p.get('flag','')[:50]} | {p.get('window','')} | {p.get('status','')}")
            lines.append("")

        # Mandatory items from sections
        for section in self.sections:
            stype = section["type"]
            if stype == "brier_score":
                lines.append("--- BRIER SCORE ---")
                s = section["scores"]
                lines.append(f"Brier Score: {s.get('brier_score','N/A')} (n={s.get('brier_n',0)}, {s.get('brier_status','')})")
                for r in section["brier_rows"]:
                    lines.append(f"  {r.get('pred_ref','')}: fi={r.get('fi',0):.2f} oi={r.get('oi',0):.1f} err={r.get('squared_error',0):.4f}")
                lines.append("")
            elif stype == "point_estimates":
                lines.append("--- POINT ESTIMATES ---")
                for h in section["hypotheses"]:
                    lines.append(f"  {h.get('hyp_id','')}: {h.get('range','')} pt={h.get('point_estimate',0):.2f}")
                lines.append("")
            elif stype == "hpt":
                lines.append("--- HPT ---")
                for e in section["entries"]:
                    lines.append(f"  {e.get('edition','')}: A={e.get('case_a','')} B={e.get('case_b','')} C={e.get('case_c','')} D={e.get('case_d','')} E={e.get('case_e','')}")
                lines.append("")
            elif stype == "plm":
                lines.append("--- PLM ---")
                for e in section["entries"]:
                    lines.append(f"  {e.get('entry_id','')}: {e.get('issue','')}")
                lines.append("")
            elif stype == "pmm":
                lines.append("--- PMM ---")
                for e in section["entries"]:
                    lines.append(f"  {e.get('entry_id','')}: {e.get('pred_ref','')} — {e.get('outcome','')} — {e.get('what_failed','')}")
                lines.append("")
            elif stype == "deviation_audit":
                lines.append("--- DEVIATION AUDIT — 28 ITEMS ---")
                for r in section["results"]:
                    status = "PASS" if r.get("passed") else "FAIL"
                    lines.append(f"  [{status}] {r.get('item_number','')}: {r.get('description','')[:65]}")
                lines.append("")
            elif stype == "prediction_log_resolved":
                lines.append("--- PREDICTION LOG — RESOLVED (CUMULATIVE) ---")
                for r in section["resolved"]:
                    lines.append(f"  {r.get('pred_ref','')}: {r.get('outcome','')} — {r.get('notes','')}")
                lines.append("")

        # Source attribution
        if self.source_attributions:
            lines.append("--- SOURCES ---")
            for i, s in enumerate(self.source_attributions, 1):
                lines.append(f"  SOURCE {i} — {s.get('name','')}")
                lines.append(f"    TIER {s.get('tier','')} — {s.get('category','')}")
                lines.append(f"    {s.get('body','')[:100]}")
                if s.get('incentive'):
                    lines.append(f"    Incentive: {s.get('incentive','')}")
            lines.append("")

        # Footer
        lines.append(f"\nSignalghost - Edition {self.edition:03d} - {self.sweep_str} - {self.date_str} - {self.gmt_str} - v1.3.0 - War Day {self.war_day}")

        txt_path = self.output_path.replace(".pdf", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return txt_path
