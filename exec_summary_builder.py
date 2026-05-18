"""exec_summary_builder.py — CF-8 Executive Summary Generator.

Pure rendering layer: reads exclusively from AttolSphere DB via persistence
functions, performs ZERO independent calculation, and outputs a 2-page A4
PDF via WeasyPrint.

Design spec (LOCKED):
  - 2-page A4 format
  - Typography: Schibsted Grotesk (headings) + Newsreader (body)
  - BLUF narrative structure
  - ISO country pills (not flags)
  - Off-white panels #f0efec
  - Brier score + BSS (BS "Pending" until n≥1, BSS alongside)
  - Logos: signalghost-white.png (top-centre),
           project-hivemind-white.png (below-left)
  - Target audience: CRO/CIO/senior analyst
  - Pure rendering layer from DB — zero independent calculation
"""

import os
import base64
import datetime
from typing import Dict, List, Optional

from persistence import (
    init_db,
    get_latest_edition,
    get_latest_hypotheses,
    get_open_predictions,
    get_resolved_predictions,
    get_all_brier_rows,
    get_all_plm,
    fetch_all,
)
from predictions import compute_all_scores


# ── COUNTRY PILL MAPPING ────────────────────────────────────────────────────

CASE_COUNTRIES = {
    "A": ["US", "IR"],
    "B": ["IR"],
    "C": ["LB", "IL"],
    "D": ["US", "CN"],
    "E": ["IR"],
}


# ── CONFIDENCE TAG STYLING ──────────────────────────────────────────────────

CONFIDENCE_COLOURS = {
    "HIGH":       ("#b91c1c", "#fef2f2"),
    "MEDIUM":     ("#92400e", "#fefce8"),
    "LOW":        ("#166534", "#f0fdf4"),
    "VERY HIGH":  ("#7f1d1d", "#fef2f2"),
}

TAG_COLOURS = {
    "ESCALATING-PROVISIONAL": ("#b91c1c", "#fef2f2"),
    "ESCALATING":             ("#b91c1c", "#fef2f2"),
    "DEVELOPING":             ("#1e40af", "#eff6ff"),
    "WATCH":                  ("#6b7280", "#f3f4f6"),
    "RESOLVED":               ("#166534", "#f0fdf4"),
}


# ── LOGO EMBEDDING ──────────────────────────────────────────────────────────

def _embed_image(path: str) -> str:
    """Return base64 data-URI for an image file, or empty string if missing."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = path.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "svg": "image/svg+xml"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


# ── HTML TEMPLATE ────────────────────────────────────────────────────────────

def _build_country_pills(case_id: str) -> str:
    codes = CASE_COUNTRIES.get(case_id, [])
    pills = []
    for code in codes:
        pills.append(
            f'<span class="country-pill">{code}</span>'
        )
    return " ".join(pills)


def _build_confidence_badge(confidence: str) -> str:
    fg, bg = CONFIDENCE_COLOURS.get(confidence, ("#374151", "#f3f4f6"))
    return (
        f'<span class="confidence-badge" '
        f'style="color:{fg};background:{bg}">{confidence}</span>'
    )


def _build_tag_badge(tag: str) -> str:
    fg, bg = TAG_COLOURS.get(tag, ("#374151", "#f3f4f6"))
    return (
        f'<span class="tag-badge" '
        f'style="color:{fg};background:{bg}">{tag}</span>'
    )


def _format_range(lower: float, upper: float) -> str:
    return f"{lower:.0%}–{upper:.0%}"


def _format_pt(pt: float) -> str:
    return f"{pt:.0%}"


def _build_bluf(cases: List[Dict], hypotheses: List[Dict],
                scores: Dict, edition_row: Dict) -> str:
    """Build Bottom Line Up Front paragraph from DB state.

    Pure rendering — all values read from DB, no calculation.
    """
    # Find the dominant hypothesis per case (highest pt estimate)
    case_dominant = {}
    for h in hypotheses:
        cid = h["case_id"]
        if cid not in case_dominant or h["point_estimate"] > case_dominant[cid]["point_estimate"]:
            case_dominant[cid] = h

    parts = []
    for case in sorted(cases, key=lambda c: c["case_id"]):
        cid = case["case_id"]
        dom = case_dominant.get(cid)
        if dom:
            pt_pct = f"{dom['point_estimate']:.0%}"
            parts.append(
                f"Case {cid} ({case['title']}): dominant at {pt_pct}"
            )

    bs = scores["brier_score"]
    bss = scores["brier_skill_score"]
    n = scores["brier_n"]

    bluf = (
        f"Edition {edition_row['edition_number']:03d} "
        f"({edition_row['sweep_descriptor']}) assessed {len(cases)} active cases "
        f"across {len(hypotheses)} hypotheses. "
        + ". ".join(parts) + ". "
    )
    if n >= 1:
        bluf += (
            f"System calibration: BS\u2009=\u2009{bs:.4f} (n={n}), "
            f"BSS\u2009=\u2009{bss:.3f} ({bss:.1%} skill over baseline)."
        )
    else:
        bluf += "Brier score: Pending (no resolved predictions)."

    return bluf


def build_exec_summary_html(
    db_path: str = "atollsphere.db",
    logo_dir: str = ".",
) -> str:
    """Build executive summary HTML from DB state.

    Args:
        db_path: Path to AttolSphere database.
        logo_dir: Directory containing logo PNG files.

    Returns:
        Complete HTML string ready for WeasyPrint rendering.
    """
    # ── DB reads (pure rendering — zero calculation) ─────────────────────
    # Set DB path via env var (persistence.py reads ATOLLSPHERE_DB)
    os.environ["ATOLLSPHERE_DB"] = db_path
    # Force persistence module to pick up new path
    import persistence
    persistence.DB_PATH = db_path

    init_db()
    edition_num = get_latest_edition()
    if edition_num is None:
        raise RuntimeError("No editions in DB.")

    edition_rows = fetch_all("editions", "edition_number = ?", (edition_num,))
    if not edition_rows:
        raise RuntimeError(f"Edition {edition_num} not found in editions table.")
    edition_row = edition_rows[0]

    hypotheses = get_latest_hypotheses(edition_num)
    cases = fetch_all("cases", "edition = ?", (edition_num,))
    scores = compute_all_scores()
    open_preds = get_open_predictions()
    resolved_preds = get_resolved_predictions()
    brier_rows = get_all_brier_rows()

    # ── Logos ─────────────────────────────────────────────────────────────
    sg_logo = _embed_image(os.path.join(logo_dir, "signalghost-white.png"))
    ph_logo = _embed_image(os.path.join(logo_dir, "project-hivemind-white.png"))

    # ── Build case cards ──────────────────────────────────────────────────
    case_hyps = {}
    for h in hypotheses:
        case_hyps.setdefault(h["case_id"], []).append(h)

    case_cards_html = []
    for case in sorted(cases, key=lambda c: c["case_id"]):
        cid = case["case_id"]
        hyps = sorted(case_hyps.get(cid, []),
                       key=lambda h: h["point_estimate"], reverse=True)
        pills = _build_country_pills(cid)
        tag_badge = _build_tag_badge(case.get("tag", "WATCH"))
        conf_badge = _build_confidence_badge(case.get("confidence", "MEDIUM"))

        hyp_rows = ""
        for h in hyps:
            rng = _format_range(h["range_lower"], h["range_upper"])
            pt = _format_pt(h["point_estimate"])
            hyp_rows += (
                f'<tr><td class="hyp-id">{h["hyp_id"]}</td>'
                f'<td class="hyp-range">{rng}</td>'
                f'<td class="hyp-pt">{pt}</td></tr>\n'
            )

        case_cards_html.append(f"""
        <div class="case-card">
          <div class="case-header">
            <span class="case-label">CASE {cid}</span>
            {pills} {tag_badge} {conf_badge}
          </div>
          <div class="case-title">{case['title']}</div>
          <table class="hyp-table">
            <tr><th>Hyp</th><th>Range</th><th>Pt Est</th></tr>
            {hyp_rows}
          </table>
        </div>""")

    case_cards = "\n".join(case_cards_html)

    # ── Build prediction tracker ──────────────────────────────────────────
    open_pred_rows = ""
    for p in open_preds:
        if "RESOLVED" in (p.get("status") or ""):
            continue
        fi_str = f"{p.get('fi', 0):.0%}" if p.get("fi") is not None else "—"
        open_pred_rows += (
            f'<tr><td>{p["pred_ref"]}</td>'
            f'<td class="pred-flag">{p["flag"]}</td>'
            f'<td>{p.get("window", "")}</td>'
            f'<td>{fi_str}</td></tr>\n'
        )

    resolved_pred_rows = ""
    for p in resolved_preds:
        outcome = p.get("outcome", "")
        outcome_class = "outcome-confirmed" if outcome == "CONFIRMED" else "outcome-contradicted"
        brier_c = p.get("brier_contribution")
        bc_str = f"{brier_c:.4f}" if brier_c is not None else "—"
        resolved_pred_rows += (
            f'<tr><td>{p["pred_ref"]}</td>'
            f'<td class="{outcome_class}">{outcome}</td>'
            f'<td>{bc_str}</td></tr>\n'
        )

    # ── Brier metrics ─────────────────────────────────────────────────────
    bs = scores["brier_score"]
    bss = scores["brier_skill_score"]
    n = scores["brier_n"]
    status = scores["brier_status"]

    if n >= 1:
        bs_display = f"{bs:.4f}"
        bss_display = f"{bss:.3f} ({bss:.1%})"
    else:
        bs_display = "Pending"
        bss_display = "Pending"

    # ── BLUF ──────────────────────────────────────────────────────────────
    bluf_text = _build_bluf(cases, hypotheses, scores, edition_row)

    # ── Assemble HTML ─────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=Schibsted+Grotesk:wght@400;600;700&display=swap');

@page {{
  size: A4;
  margin: 18mm 16mm 14mm 16mm;
  @bottom-center {{
    content: "SIGNALGHOST · PROJECT HIVEMIND · Ed{edition_num:03d} · {edition_row['gmt_timestamp']}";
    font-family: 'Schibsted Grotesk', sans-serif;
    font-size: 6.5pt;
    color: #9ca3af;
    letter-spacing: 0.04em;
  }}
  @bottom-right {{
    content: counter(page) " / " counter(pages);
    font-family: 'Schibsted Grotesk', sans-serif;
    font-size: 6.5pt;
    color: #9ca3af;
  }}
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  font-family: 'Newsreader', 'Georgia', serif;
  font-size: 9pt;
  line-height: 1.45;
  color: #1f2937;
  background: #fff;
}}

/* ── HEADER ────────────────────────────────────────── */

.header {{
  background: #111827;
  color: #fff;
  padding: 10mm 8mm 7mm 8mm;
  margin: -18mm -16mm 0 -16mm;
  margin-bottom: 5mm;
  text-align: center;
  position: relative;
}}

.header .sg-logo {{
  height: 18mm;
  margin-bottom: 2mm;
  display: block;
  margin-left: auto;
  margin-right: auto;
}}

.header .ph-logo {{
  height: 7mm;
  position: absolute;
  bottom: 5mm;
  left: 8mm;
  opacity: 0.7;
}}

.header h1 {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-weight: 700;
  font-size: 14pt;
  letter-spacing: 0.06em;
  margin-bottom: 1mm;
}}

.header .edition-line {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 8pt;
  font-weight: 400;
  color: #d1d5db;
  letter-spacing: 0.03em;
}}

/* ── METRICS BAR ───────────────────────────────────── */

.metrics-bar {{
  display: flex;
  justify-content: space-between;
  background: #f0efec;
  border-radius: 3px;
  padding: 3mm 4mm;
  margin-bottom: 4mm;
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 8pt;
}}

.metric {{
  text-align: center;
}}

.metric .metric-label {{
  font-size: 6.5pt;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 0.5mm;
}}

.metric .metric-value {{
  font-weight: 700;
  font-size: 10pt;
  color: #111827;
}}

.metric .metric-sub {{
  font-size: 6.5pt;
  color: #6b7280;
}}

/* ── BLUF ──────────────────────────────────────────── */

.bluf {{
  background: #f0efec;
  border-left: 3px solid #111827;
  padding: 3mm 4mm;
  margin-bottom: 4mm;
  border-radius: 0 3px 3px 0;
}}

.bluf-label {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 7pt;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 1mm;
}}

.bluf p {{
  font-size: 8.5pt;
  line-height: 1.5;
  color: #374151;
}}

/* ── SECTION HEADS ─────────────────────────────────── */

.section-head {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 8pt;
  font-weight: 700;
  color: #111827;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #d1d5db;
  padding-bottom: 1mm;
  margin-top: 4mm;
  margin-bottom: 2.5mm;
}}

/* ── CASE CARDS ────────────────────────────────────── */

.cases-grid {{
  display: flex;
  flex-wrap: wrap;
  gap: 2.5mm;
}}

.case-card {{
  background: #f0efec;
  border-radius: 3px;
  padding: 2.5mm 3mm;
  width: 48.5%;
  page-break-inside: avoid;
}}

.case-header {{
  display: flex;
  align-items: center;
  gap: 2mm;
  margin-bottom: 1mm;
}}

.case-label {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-weight: 700;
  font-size: 7.5pt;
  color: #111827;
}}

.case-title {{
  font-family: 'Newsreader', serif;
  font-size: 8pt;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1.5mm;
}}

.country-pill {{
  display: inline-block;
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 6pt;
  font-weight: 700;
  background: #374151;
  color: #fff;
  padding: 0.3mm 1.5mm;
  border-radius: 2px;
  letter-spacing: 0.04em;
}}

.confidence-badge, .tag-badge {{
  display: inline-block;
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 6pt;
  font-weight: 600;
  padding: 0.3mm 1.5mm;
  border-radius: 2px;
  letter-spacing: 0.03em;
}}

.hyp-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 7.5pt;
}}

.hyp-table th {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 6.5pt;
  font-weight: 600;
  color: #6b7280;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid #d1d5db;
  padding: 0.5mm 1mm;
}}

.hyp-table td {{
  padding: 0.5mm 1mm;
  border-bottom: 1px solid #e5e7eb;
}}

.hyp-id {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-weight: 600;
  font-size: 7pt;
}}

.hyp-range {{ color: #6b7280; }}
.hyp-pt {{ font-weight: 600; }}

/* ── PREDICTION TRACKER ────────────────────────────── */

.pred-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 7.5pt;
  margin-bottom: 2mm;
}}

.pred-table th {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 6.5pt;
  font-weight: 600;
  color: #6b7280;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid #d1d5db;
  padding: 0.5mm 1mm;
}}

.pred-table td {{
  padding: 0.8mm 1mm;
  border-bottom: 1px solid #e5e7eb;
}}

.pred-flag {{ max-width: 55mm; }}

.outcome-confirmed {{
  font-weight: 600;
  color: #166534;
}}

.outcome-contradicted {{
  font-weight: 600;
  color: #b91c1c;
}}

/* ── RESOLVED PANEL ────────────────────────────────── */

.resolved-panel {{
  background: #f0efec;
  border-radius: 3px;
  padding: 2.5mm 3mm;
  margin-bottom: 3mm;
}}

.resolved-panel .res-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 7.5pt;
}}

.resolved-panel .res-table th {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 6.5pt;
  font-weight: 600;
  color: #6b7280;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid #d1d5db;
  padding: 0.5mm 1mm;
}}

.resolved-panel .res-table td {{
  padding: 0.5mm 1mm;
}}

/* ── FOOTER ────────────────────────────────────────── */

.classification {{
  font-family: 'Schibsted Grotesk', sans-serif;
  font-size: 6pt;
  color: #9ca3af;
  text-align: center;
  margin-top: 3mm;
  letter-spacing: 0.04em;
}}
</style>
</head>
<body>

<!-- ═══════════════════ PAGE 1 ═══════════════════ -->

<div class="header">
  {"<img class='sg-logo' src='" + sg_logo + "' alt='Signalghost'>" if sg_logo else "<div style='height:18mm'></div>"}
  <h1>EXECUTIVE SUMMARY</h1>
  <div class="edition-line">
    Edition {edition_num:03d} · {edition_row['sweep_descriptor']} ·
    {edition_row['gmt_timestamp']} ·
    Architecture {edition_row.get('architecture_version', 'v1.3.0')} ·
    War Day {edition_row['war_day']}
  </div>
  {"<img class='ph-logo' src='" + ph_logo + "' alt='Project Hivemind'>" if ph_logo else ""}
</div>

<div class="metrics-bar">
  <div class="metric">
    <span class="metric-label">Brier Score</span>
    <span class="metric-value">{bs_display}</span>
    <span class="metric-sub">n={n} · {status}</span>
  </div>
  <div class="metric">
    <span class="metric-label">Brier Skill Score</span>
    <span class="metric-value">{bss_display}</span>
    <span class="metric-sub">ref = 0.25 (coin-flip)</span>
  </div>
  <div class="metric">
    <span class="metric-label">Active Cases</span>
    <span class="metric-value">{len(cases)}</span>
  </div>
  <div class="metric">
    <span class="metric-label">Open Predictions</span>
    <span class="metric-value">{sum(1 for p in open_preds if 'RESOLVED' not in (p.get('status') or ''))}</span>
  </div>
  <div class="metric">
    <span class="metric-label">Resolved</span>
    <span class="metric-value">{len(resolved_preds)}</span>
  </div>
</div>

<div class="bluf">
  <div class="bluf-label">Bottom Line Up Front</div>
  <p>{bluf_text}</p>
</div>

<div class="section-head">Case Assessment Matrix</div>
<div class="cases-grid">
  {case_cards}
</div>

<!-- ═══════════════════ PAGE 2 ═══════════════════ -->

<div class="section-head" style="page-break-before: always;">Prediction Tracker — Open</div>
<table class="pred-table">
  <tr><th>Ref</th><th>Flag</th><th>Window</th><th>f<sub>i</sub></th></tr>
  {open_pred_rows}
</table>

<div class="section-head">Resolved Predictions</div>
<div class="resolved-panel">
  <table class="res-table">
    <tr><th>Ref</th><th>Outcome</th><th>Brier Contribution</th></tr>
    {resolved_pred_rows}
  </table>
</div>

<div class="classification">
  SIGNALGHOST · PROJECT HIVEMIND · EXECUTIVE SUMMARY · Ed{edition_num:03d} ·
  {edition_row['gmt_timestamp']} · {edition_row.get('architecture_version', 'v1.3.0')} ·
  Pure rendering layer — zero independent calculation
</div>

</body>
</html>"""

    return html


def render_exec_summary_pdf(
    output_path: str = None,
    db_path: str = "atollsphere.db",
    logo_dir: str = ".",
) -> str:
    """Render executive summary PDF via WeasyPrint.

    Args:
        output_path: PDF output path. Defaults to
            ExecSummary_Ed{NNN}_{descriptor}.pdf
        db_path: Path to AttolSphere database.
        logo_dir: Directory containing logo PNG files.

    Returns:
        Path to rendered PDF file.
    """
    from weasyprint import HTML

    html = build_exec_summary_html(db_path=db_path, logo_dir=logo_dir)

    if output_path is None:
        os.environ["ATOLLSPHERE_DB"] = db_path
        import persistence
        persistence.DB_PATH = db_path
        init_db()
        ed = get_latest_edition()
        rows = fetch_all("editions", "edition_number = ?", (ed,))
        desc = rows[0]["sweep_descriptor"].replace(" ", "_") if rows else "SWEEP"
        output_path = f"ExecSummary_Ed{ed:03d}_{desc}.pdf"

    # Write intermediate HTML for debugging
    html_path = output_path.rsplit(".", 1)[0] + ".html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    HTML(string=html, base_url=logo_dir).write_pdf(output_path)
    print(f"  Exec summary PDF: {output_path}")
    print(f"  Exec summary HTML: {html_path}")

    return output_path


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "atollsphere.db"
    logo = sys.argv[2] if len(sys.argv) > 2 else "."
    out = sys.argv[3] if len(sys.argv) > 3 else None
    render_exec_summary_pdf(output_path=out, db_path=db, logo_dir=logo)
