"""
pdf_builder.py — Shared PDF generation utilities for EquipmentIQ technical documents.
Uses reportlab Platypus (SKILL.md: use reportlab for PDF creation).
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.colors import HexColor
import datetime

# ─── BRAND COLORS ─────────────────────────────────────────────────────────────
C_NAVY    = HexColor('#1a2744')   # primary dark — headings, header bar
C_STEEL   = HexColor('#2e4a7a')   # secondary — subheadings
C_ACCENT  = HexColor('#e8703a')   # accent — warnings, highlights
C_LIGHT   = HexColor('#eef2f8')   # table row alt
C_BORDER  = HexColor('#c0cce0')   # table borders
C_MUTED   = HexColor('#6b7a99')   # captions, footers
C_WHITE   = colors.white
C_BLACK   = colors.black
C_RED     = HexColor('#c0392b')
C_ORANGE  = HexColor('#e67e22')
C_AMBER   = HexColor('#f39c12')
C_GREEN   = HexColor('#27ae60')
C_GRAY    = HexColor('#95a5a6')

SEV_COLORS = {
    'CRITICAL' : C_RED,
    'MAJOR'    : C_ORANGE,
    'SERIOUS'  : C_AMBER,
    'MODERATE' : HexColor('#d4ac0d'),
    'MINOR'    : HexColor('#2980b9'),
    'WARNING'  : HexColor('#1abc9c'),
    'NOTICE'   : C_GREEN,
    'ADVISORY' : C_GRAY,
}

PAGE_W, PAGE_H = A4   # 595.27 x 841.89 pts
MARGIN = 20 * mm

# ─── STYLES ───────────────────────────────────────────────────────────────────
def get_styles():
    base = getSampleStyleSheet()
    s = {}

    s['doc_title'] = ParagraphStyle('doc_title',
        fontSize=22, leading=28, textColor=C_WHITE,
        fontName='Helvetica-Bold', alignment=TA_LEFT)

    s['doc_subtitle'] = ParagraphStyle('doc_subtitle',
        fontSize=11, leading=16, textColor=HexColor('#c8d8f0'),
        fontName='Helvetica', alignment=TA_LEFT)

    s['doc_ref'] = ParagraphStyle('doc_ref',
        fontSize=9, leading=13, textColor=HexColor('#a0b4d0'),
        fontName='Helvetica', alignment=TA_RIGHT)

    s['h1'] = ParagraphStyle('h1',
        fontSize=15, leading=20, textColor=C_NAVY,
        fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6,
        borderPad=0, leftIndent=0)

    s['h2'] = ParagraphStyle('h2',
        fontSize=12, leading=16, textColor=C_STEEL,
        fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)

    s['h3'] = ParagraphStyle('h3',
        fontSize=10, leading=14, textColor=C_NAVY,
        fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=3)

    s['body'] = ParagraphStyle('body',
        fontSize=9.5, leading=14, textColor=C_BLACK,
        fontName='Helvetica', spaceAfter=5, alignment=TA_JUSTIFY)

    s['body_sm'] = ParagraphStyle('body_sm',
        fontSize=8.5, leading=12, textColor=C_BLACK,
        fontName='Helvetica', spaceAfter=3)

    s['caption'] = ParagraphStyle('caption',
        fontSize=8, leading=11, textColor=C_MUTED,
        fontName='Helvetica-Oblique', spaceAfter=6, alignment=TA_CENTER)

    s['note'] = ParagraphStyle('note',
        fontSize=8.5, leading=12, textColor=HexColor('#5d4037'),
        fontName='Helvetica', leftIndent=8, rightIndent=8,
        borderWidth=0, backColor=HexColor('#fff8e1'), spaceAfter=6)

    s['warning_box'] = ParagraphStyle('warning_box',
        fontSize=9, leading=13, textColor=HexColor('#7b1c00'),
        fontName='Helvetica-Bold', leftIndent=10, rightIndent=10,
        backColor=HexColor('#fde8e0'), spaceAfter=8)

    s['code'] = ParagraphStyle('code',
        fontSize=8, leading=11, textColor=HexColor('#1a2744'),
        fontName='Courier', leftIndent=10, backColor=HexColor('#f4f6fa'),
        spaceAfter=4)

    s['bullet'] = ParagraphStyle('bullet',
        fontSize=9.5, leading=14, textColor=C_BLACK,
        fontName='Helvetica', leftIndent=14, firstLineIndent=-10, spaceAfter=3)

    s['tbl_hdr'] = ParagraphStyle('tbl_hdr',
        fontSize=8.5, leading=11, textColor=C_WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER)

    s['tbl_cell'] = ParagraphStyle('tbl_cell',
        fontSize=8.5, leading=11, textColor=C_BLACK,
        fontName='Helvetica')

    s['tbl_cell_sm'] = ParagraphStyle('tbl_cell_sm',
        fontSize=7.5, leading=10, textColor=C_BLACK,
        fontName='Helvetica')

    s['toc_entry'] = ParagraphStyle('toc_entry',
        fontSize=10, leading=16, textColor=C_STEEL,
        fontName='Helvetica', leftIndent=0)

    s['toc_sub'] = ParagraphStyle('toc_sub',
        fontSize=9, leading=14, textColor=C_MUTED,
        fontName='Helvetica', leftIndent=12)

    return s


# ─── PAGE TEMPLATE WITH HEADER / FOOTER ────────────────────────────────────────
class DocPageTemplate:
    def __init__(self, doc_number, doc_title, revision, logo_text="EquipmentIQ"):
        self.doc_number = doc_number
        self.doc_title  = doc_title
        self.revision   = revision
        self.logo_text  = logo_text

    def first_page(self, canv, doc):
        self._draw_header_bar(canv, doc, is_first=True)
        self._draw_footer(canv, doc)

    def later_pages(self, canv, doc):
        self._draw_header_bar(canv, doc, is_first=False)
        self._draw_footer(canv, doc)

    def _draw_header_bar(self, canv, doc, is_first):
        canv.saveState()
        if is_first:
            # Full cover bar — tall
            bar_h = 52 * mm
            canv.setFillColor(C_NAVY)
            canv.rect(0, PAGE_H - bar_h, PAGE_W, bar_h, fill=1, stroke=0)
            canv.setFillColor(C_ACCENT)
            canv.rect(0, PAGE_H - bar_h - 3, PAGE_W, 3, fill=1, stroke=0)
        else:
            # Slim bar on subsequent pages
            bar_h = 14 * mm
            canv.setFillColor(C_NAVY)
            canv.rect(0, PAGE_H - bar_h, PAGE_W, bar_h, fill=1, stroke=0)
            canv.setFillColor(C_ACCENT)
            canv.rect(0, PAGE_H - bar_h - 2, PAGE_W, 2, fill=1, stroke=0)
            # Logo text
            canv.setFillColor(C_WHITE)
            canv.setFont('Helvetica-Bold', 9)
            canv.drawString(MARGIN, PAGE_H - 9*mm, self.logo_text)
            # Doc title abbreviated
            canv.setFont('Helvetica', 8)
            canv.setFillColor(HexColor('#a0b4d0'))
            canv.drawString(MARGIN + 65*mm, PAGE_H - 9*mm, self.doc_title[:60])
        canv.restoreState()

    def _draw_footer(self, canv, doc):
        canv.saveState()
        y = 12 * mm
        canv.setFillColor(C_BORDER)
        canv.rect(MARGIN, y, PAGE_W - 2*MARGIN, 0.5, fill=1, stroke=0)
        canv.setFont('Helvetica', 7.5)
        canv.setFillColor(C_MUTED)
        canv.drawString(MARGIN, y - 4*mm, f"{self.doc_number}  |  Rev {self.revision}  |  {datetime.date.today().strftime('%B %Y')}")
        canv.drawRightString(PAGE_W - MARGIN, y - 4*mm,
            f"CONFIDENTIAL — For authorised service personnel only  |  Page {doc.page}")
        canv.restoreState()


# ─── REUSABLE FLOWABLE HELPERS ─────────────────────────────────────────────────
def cover_block(story, styles, title, subtitle, doc_number, revision, classification, issued_by):
    """Full-page cover block (first page content below the header bar)."""
    story.append(Spacer(1, 58*mm))  # push below the cover bar
    story.append(Paragraph(title, styles['doc_title']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(subtitle, styles['doc_subtitle']))
    story.append(Spacer(1, 10*mm))
    # Meta table
    meta = [
        ['Document Number', doc_number,  'Classification', classification],
        ['Revision',        revision,     'Issued By',      issued_by],
        ['Issue Date',      datetime.date.today().strftime('%d %B %Y'),
         'Applies To',      'EquipmentIQ VMC-3000 Series'],
    ]
    tw = PAGE_W - 2*MARGIN
    t = Table(meta, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
    t.setStyle(TableStyle([
        ('FONTNAME',  (0,0),(-1,-1), 'Helvetica'),
        ('FONTNAME',  (0,0),(0,-1),  'Helvetica-Bold'),
        ('FONTNAME',  (2,0),(2,-1),  'Helvetica-Bold'),
        ('FONTSIZE',  (0,0),(-1,-1), 8.5),
        ('TEXTCOLOR', (0,0),(0,-1),  C_STEEL),
        ('TEXTCOLOR', (2,0),(2,-1),  C_STEEL),
        ('BACKGROUND',(0,0),(-1,-1), C_LIGHT),
        ('GRID',      (0,0),(-1,-1), 0.5, C_BORDER),
        ('TOPPADDING',(0,0),(-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('LEFTPADDING',  (0,0),(-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER))
    story.append(PageBreak())


def section_heading(story, styles, text, level=1):
    tag = f'h{level}'
    if level == 1:
        story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER))
        story.append(Spacer(1, 1*mm))
    story.append(Paragraph(text, styles[tag]))


def warning_box(story, styles, text, label="WARNING"):
    story.append(Paragraph(f"<b>{label}:</b> {text}", styles['warning_box']))
    story.append(Spacer(1, 2*mm))


def note_box(story, styles, text):
    story.append(Paragraph(f"<b>NOTE:</b> {text}", styles['note']))
    story.append(Spacer(1, 2*mm))


def bullet_list(story, styles, items):
    for item in items:
        story.append(Paragraph(f"&#8226; &nbsp; {item}", styles['bullet']))


def param_table(story, styles, params, caption=None):
    """Render a parameter specification table.
    Accepts either a list of dicts (with 'param_id' key) or
    a list of (param_id, param_dict) tuples from params.items().
    """
    hdr = ['Param ID', 'PID', 'Parameter Name', 'Unit', 'Normal Range', 'Critical Range']
    rows = [hdr]
    for p in params:
        if isinstance(p, tuple):
            pid_key, p = p
        else:
            pid_key = p.get('param_id', '—')
        rows.append([
            pid_key, str(p['pid']), p['name'], p['unit'],
            f"{p['normal_min']} \u2013 {p['normal_max']}",
            f"{p['critical_min']} \u2013 {p['critical_max']}",
        ])
    tw = PAGE_W - 2*MARGIN
    cw = [18*mm, 12*mm, 55*mm, 18*mm, 32*mm, 32*mm]
    t = Table(rows, colWidths=cw, repeatRows=1)
    ts = TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  C_NAVY),
        ('TEXTCOLOR',     (0,0), (-1,0),  C_WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 8),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('GRID',          (0,0), (-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ('ALIGN',         (1,0), (1,-1),  'CENTER'),
        ('ALIGN',         (3,0), (3,-1),  'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
    ])
    t.setStyle(ts)
    story.append(t)
    if caption:
        story.append(Paragraph(caption, styles['caption']))
    story.append(Spacer(1, 4*mm))


def error_code_table(story, styles, codes, caption=None):
    """Render an error code summary table with severity colour coding."""
    hdr = ['Error Code', 'Severity', 'Title', 'Primary Param', 'Action']
    rows = [hdr]
    row_styles = [
        ('BACKGROUND',    (0,0), (-1,0),  C_NAVY),
        ('TEXTCOLOR',     (0,0), (-1,0),  C_WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 7.5),
        ('GRID',          (0,0), (-1,-1), 0.4, C_BORDER),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('WORDWRAP',      (0,0), (-1,-1), 1),
    ]
    for i, c in enumerate(codes, 1):
        rows.append([
            c['error_code'], c['severity_level'],
            Paragraph(c['title'], ParagraphStyle('x', fontSize=7.5, leading=10, fontName='Helvetica')),
            c.get('primary_param','—'), c['required_action'][:55]+'…' if len(c['required_action'])>55 else c['required_action']
        ])
        sev_col = SEV_COLORS.get(c['severity_level'], C_GRAY)
        row_styles.append(('BACKGROUND', (1,i), (1,i), sev_col))
        row_styles.append(('TEXTCOLOR',  (1,i), (1,i), C_WHITE))
        row_styles.append(('FONTNAME',   (0,i), (-1,i), 'Helvetica'))
        if i % 2 == 0:
            row_styles.append(('BACKGROUND', (0,i),(0,i), C_LIGHT))
            row_styles.append(('BACKGROUND', (2,i),(-1,i), C_LIGHT))

    cw = [28*mm, 22*mm, 68*mm, 24*mm, 35*mm]
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle(row_styles))
    story.append(t)
    if caption:
        story.append(Paragraph(caption, styles['caption']))
    story.append(Spacer(1, 4*mm))


def parts_table(story, styles, parts, caption=None):
    """Render a spare parts / BOM table."""
    hdr = ['Part Number', 'Description', 'Qty', 'Unit', 'Lead Time', 'Safety Stock']
    rows = [hdr]
    for p in parts:
        rows.append([p['pn'], p['desc'], str(p['qty']), p['unit'], p['lead'], str(p['stock'])])
    cw = [32*mm, 78*mm, 12*mm, 14*mm, 22*mm, 19*mm]
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  C_STEEL),
        ('TEXTCOLOR',     (0,0), (-1,0),  C_WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 8),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('GRID',          (0,0), (-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ('ALIGN',         (2,0), (3,-1),  'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
    ]))
    t.setStyle(TableStyle([('FONTNAME',(0,1),(0,-1),'Courier'),('FONTSIZE',(0,1),(0,-1),8)]))
    story.append(t)
    if caption:
        story.append(Paragraph(caption, styles['caption']))
    story.append(Spacer(1, 4*mm))


def wiring_schematic_text(story, styles, title, connections):
    """Render a text-based wiring connection table (no image)."""
    section_heading(story, styles, title, level=2)
    hdr = ['Signal Name', 'From (Module:Pin)', 'To (Module:Pin)', 'Wire Gauge', 'Color Code', 'Notes']
    rows = [hdr]
    for c in connections:
        rows.append([c['signal'], c['from_pin'], c['to_pin'], c['gauge'], c['color'], c.get('notes','')])
    cw = [34*mm, 34*mm, 34*mm, 18*mm, 20*mm, 37*mm]
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  C_NAVY),
        ('TEXTCOLOR',     (0,0), (-1,0),  C_WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 7.5),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('FONTNAME',      (1,1), (2,-1),  'Courier'),
        ('GRID',          (0,0), (-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))


def build_doc(filepath, story, page_tmpl):
    """Build the PDF using SimpleDocTemplate with header/footer callbacks."""
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=22*mm, bottomMargin=22*mm,
        title=page_tmpl.doc_title,
        author='EquipmentIQ Technical Publications',
        subject=page_tmpl.doc_number,
    )
    doc.build(story,
              onFirstPage=page_tmpl.first_page,
              onLaterPages=page_tmpl.later_pages)
    print(f"  Built: {filepath}")
