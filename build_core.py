"""build_core.py — Signalghost reusable layout functions.

Provides all table/flowable builders and the page-callback factory.
Import in per-edition scripts:
    from build_core import (
        hr, thin_rule, tag_table, fact_table, hyp_table,
        disconf_table, flag_block, source_block, make_page_callbacks,
    )
"""

from reportlab.platypus import Paragraph, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER

from styles import (
    NAVY, TEAL, CHARCOAL, MID_GREY, LIGHT_BG, ROW_ALT,
    WHITE, RED_TAG, AMBER, GREEN_TAG, PURPLE, DK_GREEN,
    BLACK_PANEL,
    MARGIN, PAGE_W, PAGE_H,
)

# ── HELPERS ──────────────────────────────────────────────────────────────────

def hr(width='100%'):
    return HRFlowable(width=width, thickness=0.5, color=TEAL,
                      spaceAfter=5, spaceBefore=5)


def thin_rule():
    return HRFlowable(width='100%', thickness=0.3,
                      color=colors.HexColor('#D0D8E0'),
                      spaceAfter=2, spaceBefore=2)


def tag_table(case_letter, title, tag, confidence, escalation, styles):
    """Coloured header row for a case block.

    escalation: None, or a dict with:
      - type: 'gate_06_breach' | 'change_point' | None
      - detail: str (shown as tooltip/note)
    If escalation is active, the CASE cell background changes:
      gate_06_breach → RED_TAG (red)
      change_point   → AMBER  (orange)
    """
    tag_colors = {
        'ESCALATING':             (RED_TAG,   WHITE),
        'ESCALATING-PROVISIONAL': (AMBER,     WHITE),
        'DEVELOPING':             (AMBER,     WHITE),
        'NEW':                    (TEAL,      WHITE),
        'ELEVATED':               (NAVY,      WHITE),
        'STABLE':                 (GREEN_TAG, WHITE),
        'RESOLVED':               (MID_GREY,  WHITE),
        'DE-ESCALATING':          (DK_GREEN,  WHITE),
        'WATCH':                  (PURPLE,    WHITE),
    }
    conf_map = {
        'HIGH':       (GREEN_TAG, '70\u201390%'),
        'MEDIUM':     (AMBER,     '55\u201370%'),
        'LOW-MEDIUM': (AMBER,     '40\u201355%'),
        'LOW':        (RED_TAG,   '25\u201340%'),
    }
    tag_bg, tag_fg = tag_colors.get(tag, (MID_GREY, WHITE))
    conf_bg, conf_range = conf_map.get(confidence, (MID_GREY, ''))

    # FIX (Items 7+8): Visual escalation override
    esc_type = None
    esc_detail = ""
    if isinstance(escalation, dict):
        esc_type = escalation.get("type")
        esc_detail = escalation.get("detail", "")

    # Determine case cell background — escalation overrides default NAVY
    if esc_type == "gate_06_breach":
        case_bg = RED_TAG
        case_suffix = " \u26a0"  # warning triangle
    elif esc_type == "change_point":
        case_bg = AMBER
        case_suffix = " \u0394"  # delta symbol
    else:
        case_bg = NAVY
        case_suffix = ""

    case_cell = Paragraph(f'<b>CASE {case_letter}{case_suffix}</b>',
        ParagraphStyle('cc', fontName='Helvetica-Bold', fontSize=8,
                       textColor=WHITE))
    title_cell = Paragraph(f'<b>{title}</b>',
        ParagraphStyle('tc', fontName='Helvetica-Bold', fontSize=8,
                       textColor=NAVY))
    tag_cell = Paragraph(f'<b>{tag}</b>',
        ParagraphStyle('tgc', fontName='Helvetica-Bold', fontSize=7.5,
                       textColor=tag_fg, alignment=TA_CENTER))
    conf_cell = Paragraph(
        f'<b>{confidence}</b><br/><font size=6>{conf_range}</font>',
        ParagraphStyle('cfc', fontName='Helvetica-Bold', fontSize=7.5,
                       textColor=WHITE, alignment=TA_CENTER))

    tbl = Table([[case_cell, title_cell, tag_cell, conf_cell]],
                colWidths=[22*mm, 95*mm, 35*mm, 22*mm])

    # Bottom line colour escalates with the case cell
    bottom_line_color = RED_TAG if esc_type == "gate_06_breach" else TEAL

    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, 0), case_bg),
        ('BACKGROUND',    (1, 0), (1, 0), LIGHT_BG),
        ('BACKGROUND',    (2, 0), (2, 0), tag_bg),
        ('BACKGROUND',    (3, 0), (3, 0), conf_bg),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW',     (0, 0), (-1, -1), 1, bottom_line_color),
    ]))
    return tbl


def fact_table(rows, styles):
    """Two-column fact/source table.

    rows = [(fact_text, source_attribution), ...]
    """
    header = [
        Paragraph('<b>FACT</b>',
            ParagraphStyle('fh', fontName='Helvetica-Bold',
                           fontSize=7, textColor=WHITE)),
        Paragraph('<b>SOURCE \u2014 TIER \u00b7 GATE 0</b>',
            ParagraphStyle('sh', fontName='Helvetica-Bold',
                           fontSize=7, textColor=WHITE)),
    ]
    table_rows = [header]
    for fact, source in rows:
        table_rows.append([
            Paragraph(fact,
                ParagraphStyle('fb', fontName='Helvetica',
                               fontSize=7.5, leading=10, textColor=CHARCOAL)),
            Paragraph(source,
                ParagraphStyle('sb', fontName='Helvetica-Oblique',
                               fontSize=7, leading=9.5, textColor=MID_GREY)),
        ])
    tbl = Table(table_rows, colWidths=[117*mm, 57*mm])
    style = [
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW',     (0, 1), (-1, -1), 0.3, colors.HexColor('#D0D8E0')),
    ]
    for i in range(1, len(table_rows)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(style))
    return tbl


def hyp_table(hypotheses, styles):
    """N-column hypothesis comparison table.

    hypotheses = [{'heading': str, 'body': str, 'probability_range': str}, ...]
    """
    n = len(hypotheses)
    col_w = 174 * mm / n
    headers, bodies = [], []
    for h in hypotheses:
        teal_hex = TEAL.hexval()[2:]  # strip '0x' prefix
        headers.append(
            Paragraph(
                f'<b>{h["heading"]}</b><br/>'
                f'<font size=6 color="#{teal_hex}">{h["probability_range"]}</font>',
                ParagraphStyle('hh', fontName='Helvetica-Bold', fontSize=7.5,
                               textColor=NAVY, leading=11)))
        bodies.append(
            Paragraph(h['body'],
                ParagraphStyle('hb', fontName='Helvetica', fontSize=7.5,
                               leading=10, textColor=CHARCOAL)))
    tbl = Table([headers, bodies], colWidths=[col_w] * n)
    line_cmds = [
        ('LINEAFTER', (i - 1, 0), (i - 1, -1), 0.5, TEAL)
        for i in range(1, n)
    ]
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), LIGHT_BG),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BOX',           (0, 0), (-1, -1), 0.5, TEAL),
    ] + line_cmds))
    return tbl


def disconf_table(rows, revision_trigger, styles):
    """Two-column confirms/contradicts disconfirmation table.

    rows = [(confirms_text, contradicts_text), ...]
    revision_trigger — string shown as a Gate 5 note (not rendered in the
    table itself; caller should append it as a pred_note paragraph).
    """
    header = [
        Paragraph('<b>CONFIRMS</b>',
            ParagraphStyle('ch', fontName='Helvetica-Bold',
                           fontSize=7.5, textColor=GREEN_TAG)),
        Paragraph('<b>CONTRADICTS</b>',
            ParagraphStyle('cth', fontName='Helvetica-Bold',
                           fontSize=7.5, textColor=RED_TAG)),
    ]
    table_rows = [header]
    for conf, contra in rows:
        table_rows.append([
            Paragraph(f'\u25a0 {conf}',
                ParagraphStyle('cr', fontName='Helvetica',
                               fontSize=7.5, leading=10, textColor=CHARCOAL)),
            Paragraph(f'\u25a0 {contra}',
                ParagraphStyle('ctr', fontName='Helvetica',
                               fontSize=7.5, leading=10, textColor=CHARCOAL)),
        ])
    tbl = Table(table_rows, colWidths=[87*mm, 87*mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEAFTER',     (0, 0), (0, -1),  0.5, TEAL),
        ('LINEBELOW',     (0, 1), (-1, -1), 0.3, colors.HexColor('#D0D8E0')),
    ]))
    return tbl


def flag_block(ref, number, body_text, gate_note, styles):
    """Forward-flag prediction block. Returns a list of flowables."""
    return [
        Paragraph(f'<b>FLAG {number} \u00b7 {ref}</b>', styles['flag_head']),
        Paragraph(body_text, styles['body']),
        Paragraph(f'<i>Gate note: {gate_note}</i>', styles['pred_note']),
    ]


def source_block(sources, styles):
    """Formatted source list. Returns a list of flowables.

    Each source dict: name, tier, category, body, and optionally
    incentive (str) and url (str).
    """
    flowables = []
    for i, s in enumerate(sources, 1):
        flowables.append(Paragraph(
            f'SOURCE {i} \u2014 {s["name"]}',
            ParagraphStyle('sn', fontName='Helvetica-Bold', fontSize=7.5,
                           textColor=NAVY, spaceBefore=4)))
        flowables.append(Paragraph(
            f'TIER {s["tier"]} \u2014 {s["category"]}',
            styles['source_tier']))
        flowables.append(Paragraph(s['body'], styles['small']))
        if s.get('incentive'):
            flowables.append(Paragraph(
                f'Incentive: {s["incentive"]}',
                ParagraphStyle('inc', fontName='Helvetica-Oblique',
                               fontSize=7, textColor=AMBER)))
        if s.get('url'):
            flowables.append(Paragraph(s['url'], styles['small']))
        flowables.append(thin_rule())
    return flowables


# ── PAGE-CALLBACK FACTORY ────────────────────────────────────────────────────

# Resolve logo paths relative to this module's location, so the build works
# regardless of the cwd from which the edition script is invoked.
import os as _os
from reportlab.lib.utils import ImageReader as _ImageReader

_THIS_DIR = _os.path.dirname(_os.path.abspath(__file__))
_HIVEMIND_LOGO_PATH = _os.path.join(_THIS_DIR, "projecthivemind.png")
_SIGNALGHOST_LOGO_PATH = _os.path.join(_THIS_DIR, "signalghost.png")


def _logo_reader(path):
    """Return an ImageReader for the given logo path, or None if missing.

    Returning None lets the page callbacks degrade gracefully if a logo
    file is absent (e.g. during partial deployments) rather than crashing
    the whole PDF build.
    """
    try:
        if _os.path.isfile(path):
            return _ImageReader(path)
    except Exception:
        pass
    return None


def make_page_callbacks(edition, sweep_str, date_str):
    """Return (on_cover, on_page) callables for SimpleDocTemplate.build().

    Parameters
    ----------
    edition   : str  e.g. '013'
    sweep_str : str  e.g. 'MORNING SWEEP'
    date_str  : str  e.g. '09 APRIL 2026'
    """

    hivemind_reader = _logo_reader(_HIVEMIND_LOGO_PATH)
    # Header mark size: ~6mm tall, HIVEMIND aspect 1774:887 ≈ 2:1 → ~12mm wide.
    HEADER_LOGO_H_MM = 6.0
    HEADER_LOGO_W_MM = 12.0

    def on_cover(canvas, doc):
        canvas.saveState()
        # Full-page black background.
        canvas.setFillColor(BLACK_PANEL)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # Small HIVEMIND header mark, top-left.
        if hivemind_reader is not None:
            canvas.drawImage(
                hivemind_reader,
                MARGIN, PAGE_H - 13*mm,
                width=HEADER_LOGO_W_MM*mm, height=HEADER_LOGO_H_MM*mm,
                mask='auto', preserveAspectRatio=True)
        # Confidentiality footer (centered, light text on black).
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(colors.HexColor("#A0A4BC"))
        canvas.drawCentredString(
            PAGE_W / 2, 6*mm,
            'CONFIDENTIAL \u2014 For Editorial Review Only \u00b7 Signalghost \u00b7 PROJECT HIVEMIND')
        canvas.restoreState()

    def on_page(canvas, doc):
        canvas.saveState()
        # Pure black header bar (matches HIVEMIND logo background — seamless seat).
        canvas.setFillColor(BLACK_PANEL)
        canvas.rect(0, PAGE_H - 13*mm, PAGE_W, 13*mm, fill=1, stroke=0)
        # Small HIVEMIND logo, top-left inside the header bar.
        if hivemind_reader is not None:
            canvas.drawImage(
                hivemind_reader,
                MARGIN, PAGE_H - 11.5*mm,
                width=HEADER_LOGO_W_MM*mm, height=HEADER_LOGO_H_MM*mm,
                mask='auto', preserveAspectRatio=True)
        # Edition info, top-right.
        canvas.setFillColor(WHITE)
        canvas.setFont('Helvetica', 6.5)
        canvas.drawRightString(
            PAGE_W - MARGIN, PAGE_H - 8*mm,
            f'SIGNALGHOST BRIEF \u00b7 EDITION {edition} \u00b7 {sweep_str} \u00b7 {date_str}')
        # Light footer (white-on-light not great; keep the existing band).
        canvas.setFillColor(LIGHT_BG)
        canvas.rect(0, 0, PAGE_W, 9*mm, fill=1, stroke=0)
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(MID_GREY)
        canvas.drawCentredString(
            PAGE_W / 2, 3*mm,
            f'CONFIDENTIAL \u2014 For Editorial Review Only \u00b7 Signalghost \u00b7 PROJECT HIVEMIND'
            f' \u00b7 smarter ai prediction systems \u00b7 Page {doc.page}')
        canvas.restoreState()

    return on_cover, on_page

def simple_table(headers, rows, col_widths, styles, alt=True):
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from styles import NAVY, CHARCOAL, WHITE, ROW_ALT
    hdr_cells = [Paragraph(f'<b>{h}</b>',
        ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=7,
                       textColor=WHITE)) for h in headers]
    table_rows = [hdr_cells]
    for row in rows:
        table_rows.append([Paragraph(str(c),
            ParagraphStyle('td', fontName='Helvetica', fontSize=7.5,
                           leading=10, textColor=CHARCOAL))
            for c in row])
    tbl = Table(table_rows, colWidths=col_widths)
    style = [
        ('BACKGROUND', (0,0),(-1,0), NAVY),
        ('VALIGN', (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0),(-1,-1), 4),
        ('RIGHTPADDING', (0,0),(-1,-1), 4),
        ('TOPPADDING', (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LINEBELOW', (0,1),(-1,-1), 0.3, colors.HexColor('#D0D8E0')),
    ]
    if alt:
        for i in range(1, len(table_rows)):
            if i % 2 == 0:
                style.append(('BACKGROUND', (0,i),(-1,i), ROW_ALT))
    tbl.setStyle(TableStyle(style))
    return tbl


def simple_table_dark(headers, rows, col_widths, styles, alt=True):
    """Dark-themed simple_table for use on the all-black cover page.

    Light text on dark fills, with a faint teal-tinted alt row to keep
    rows visually separable against the surrounding black.
    """
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from styles import TEAL, WHITE
    hdr_cells = [Paragraph(f'<b>{h}</b>',
        ParagraphStyle('th_dk', fontName='Helvetica-Bold', fontSize=7,
                       textColor=WHITE)) for h in headers]
    table_rows = [hdr_cells]
    body_color = colors.HexColor('#E0E2F0')
    for row in rows:
        table_rows.append([Paragraph(str(c),
            ParagraphStyle('td_dk', fontName='Helvetica', fontSize=7.5,
                           leading=10, textColor=body_color))
            for c in row])
    tbl = Table(table_rows, colWidths=col_widths)
    header_bg = colors.HexColor('#161A30')
    alt_bg = colors.HexColor('#0E1126')
    style = [
        ('BACKGROUND', (0,0),(-1,0), header_bg),
        ('VALIGN', (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0),(-1,-1), 4),
        ('RIGHTPADDING', (0,0),(-1,-1), 4),
        ('TOPPADDING', (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LINEBELOW', (0,1),(-1,-1), 0.3, TEAL),
        ('BOX', (0,0),(-1,-1), 0.4, colors.HexColor('#2A2E48')),
    ]
    if alt:
        for i in range(1, len(table_rows)):
            if i % 2 == 0:
                style.append(('BACKGROUND', (0,i),(-1,i), alt_bg))
    tbl.setStyle(TableStyle(style))
    return tbl
