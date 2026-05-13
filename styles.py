"""styles.py — Signalghost colour constants and paragraph style factory.

Import in build scripts:
    from styles import make_styles, NAVY, TEAL, CHARCOAL, MID_GREY, LIGHT_BG,\
        ROW_ALT, WHITE, RED_TAG, AMBER, GREEN_TAG, PURPLE, DK_GREEN,\
        MARGIN, PAGE_W, PAGE_H
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT

# ── COLOUR CONSTANTS ─────────────────────────────────────────────────────────

NAVY        = colors.HexColor("#070922")
TEAL        = colors.HexColor("#6E78D8")
BLACK_PANEL = colors.HexColor("#000000")
CHARCOAL    = colors.HexColor("#3D3D3D")
MID_GREY  = colors.HexColor("#8A8A8A")
LIGHT_BG  = colors.HexColor("#F2F2F0")
ROW_ALT   = colors.HexColor("#F7F9FB")
WHITE     = colors.white
RED_TAG   = colors.HexColor("#B83232")
AMBER     = colors.HexColor("#C47D1A")
GREEN_TAG = colors.HexColor("#2C7A4B")
PURPLE    = colors.HexColor("#6B3FA0")
DK_GREEN  = colors.HexColor("#4A7C4E")
MARGIN    = 18 * mm
PAGE_W, PAGE_H = A4

# ── STYLES ───────────────────────────────────────────────────────────────────

def make_styles():
    """Return a dict of ParagraphStyle objects keyed by name."""
    s = {}
    s['cover_title'] = ParagraphStyle('cover_title',
        fontName='Helvetica-Bold', fontSize=18, textColor=NAVY,
        alignment=TA_CENTER, spaceAfter=6)
    s['cover_sub'] = ParagraphStyle('cover_sub',
        fontName='Helvetica', fontSize=10, textColor=CHARCOAL,
        alignment=TA_CENTER, spaceAfter=4)
    s['cover_meta'] = ParagraphStyle('cover_meta',
        fontName='Helvetica', fontSize=8.5, textColor=CHARCOAL,
        alignment=TA_CENTER, spaceAfter=3)
    s['cover_label'] = ParagraphStyle('cover_label',
        fontName='Helvetica-Bold', fontSize=7.5, textColor=MID_GREY,
        alignment=TA_CENTER)
    s['cover_value'] = ParagraphStyle('cover_value',
        fontName='Helvetica-Bold', fontSize=9, textColor=NAVY,
        alignment=TA_CENTER, spaceAfter=2)
    s['section_head'] = ParagraphStyle('section_head',
        fontName='Helvetica-Bold', fontSize=7.5, textColor=TEAL,
        spaceBefore=8, spaceAfter=3)
    s['body'] = ParagraphStyle('body',
        fontName='Helvetica', fontSize=8.5, textColor=CHARCOAL,
        alignment=TA_JUSTIFY, spaceAfter=4, leading=12)
    s['body_bold'] = ParagraphStyle('body_bold',
        fontName='Helvetica-Bold', fontSize=8.5, textColor=CHARCOAL,
        spaceAfter=3)
    s['small'] = ParagraphStyle('small',
        fontName='Helvetica', fontSize=7.5, textColor=MID_GREY, spaceAfter=2)
    s['small_bold'] = ParagraphStyle('small_bold',
        fontName='Helvetica-Bold', fontSize=7.5, spaceAfter=2)
    s['hyp_head'] = ParagraphStyle('hyp_head',
        fontName='Helvetica-Bold', fontSize=7.5, textColor=NAVY)
    s['pred_note'] = ParagraphStyle('pred_note',
        fontName='Helvetica-Oblique', fontSize=7.5,
        textColor=MID_GREY, leftIndent=8, spaceAfter=3)
    s['correction_note'] = ParagraphStyle('correction_note',
        fontName='Helvetica-Oblique', fontSize=7.5,
        textColor=RED_TAG, leftIndent=8, spaceAfter=3)
    s['afc_note'] = ParagraphStyle('afc_note',
        fontName='Helvetica-Oblique', fontSize=7.5,
        textColor=RED_TAG, leftIndent=8, spaceAfter=3)
    s['tql_head'] = ParagraphStyle('tql_head',
        fontName='Helvetica-Bold', fontSize=7.5,
        textColor=NAVY, spaceBefore=4, spaceAfter=2)
    s['flag_head'] = ParagraphStyle('flag_head',
        fontName='Helvetica-Bold', fontSize=8, textColor=TEAL, spaceAfter=2)
    s['footer'] = ParagraphStyle('footer',
        fontName='Helvetica', fontSize=6.5, textColor=MID_GREY,
        alignment=TA_CENTER)
    s['source_tier'] = ParagraphStyle('source_tier',
        fontName='Helvetica-Bold', fontSize=7, textColor=TEAL)
    s['infer'] = ParagraphStyle('infer',
        fontName='Helvetica-Bold', fontSize=8.5, textColor=CHARCOAL,
        spaceAfter=4, leading=12)
    s['heuristic_line'] = ParagraphStyle('heuristic_line',
        fontName='Helvetica-Oblique', fontSize=7, textColor=MID_GREY,
        spaceAfter=4)
    s['not_proven'] = ParagraphStyle('not_proven',
        fontName='Helvetica', fontSize=8, textColor=CHARCOAL,
        leftIndent=10, spaceAfter=3)
    # ── COVER-DARK VARIANTS (used only on the all-black cover page) ─────────
    s['cover_title_dark'] = ParagraphStyle('cover_title_dark',
        fontName='Helvetica-Bold', fontSize=18, textColor=WHITE,
        alignment=TA_CENTER, spaceAfter=6)
    s['cover_sub_dark'] = ParagraphStyle('cover_sub_dark',
        fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#C8CCE8"),
        alignment=TA_CENTER, spaceAfter=4)
    s['cover_meta_dark'] = ParagraphStyle('cover_meta_dark',
        fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor("#C8CCE8"),
        alignment=TA_CENTER, spaceAfter=3)
    s['cover_body_dark'] = ParagraphStyle('cover_body_dark',
        fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor("#E0E2F0"),
        alignment=TA_JUSTIFY, spaceAfter=4, leading=12)
    s['cover_section_dark'] = ParagraphStyle('cover_section_dark',
        fontName='Helvetica-Bold', fontSize=7.5, textColor=TEAL,
        spaceBefore=8, spaceAfter=3)
    return s
