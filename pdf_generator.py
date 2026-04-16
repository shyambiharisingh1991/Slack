from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Wedge
from reportlab.graphics import renderPDF
from datetime import datetime, date
import os
import math
from engineer_tenures import get_team, get_geo, get_onboarding_plan, get_current_tenure, get_all_tenures
from trailhead import fetch_trailhead_profile

# ── Enterprise color palette ──────────────────────────────────────────
NAVY = colors.HexColor('#1a365d')
SLATE = colors.HexColor('#2d3748')
ACCENT = colors.HexColor('#3182ce')
GREEN = colors.HexColor('#38a169')
ORANGE = colors.HexColor('#dd6b20')
RED = colors.HexColor('#e53e3e')
LIGHT_BG = colors.HexColor('#f7fafc')
LIGHT_BLUE = colors.HexColor('#ebf8ff')
LIGHT_GREEN = colors.HexColor('#f0fff4')
LIGHT_RED = colors.HexColor('#fff5f5')
BORDER = colors.HexColor('#e2e8f0')
MUTED = colors.HexColor('#a0aec0')
WHITE = colors.white

# ── Display-name mappings ─────────────────────────────────────────────
TEAM_MAP = {
    'sales_core': 'Sales – Core', 'sales_industries': 'Sales – Industries',
    'sales_signature': 'Sales – Signature', 'service_signature': 'Service – Signature',
    'service_premier': 'Service Premier', 'prom': 'ProM', 'guides': 'Guides',
    'success_architect': 'Success Architect', 'unassigned': 'Not Assigned', 'fde': 'FDE',
    'support': 'Support', 'success_architects': 'Success Architects',
}
GEO_MAP = {
    'apac': 'APAC', 'ist': 'IST', 'emea': 'EMEA',
    'amer_est': 'AMER EST', 'amer_pst': 'AMER PST', 'americas': 'Americas',
    'unassigned': 'Not Assigned',
}
PLAN_MAP = {
    'sales_core': 'Sales – Core', 'sales_industries': 'Sales – Industries',
    'sales_signature': 'Sales – Signature', 'service_signature': 'Service – Signature',
    'service_premier': 'Service Premier', 'prom': 'ProM', 'guides': 'Guides',
    'success_architect': 'Success Architect', 'custom': 'Custom', 'standard': 'Standard',
}


def _make_styles():
    """Create reusable paragraph styles."""
    base = getSampleStyleSheet()
    return {
        'base': base,
        'title': ParagraphStyle('RTitle', parent=base['Heading1'], fontSize=22,
                                textColor=NAVY, spaceAfter=4, fontName='Helvetica-Bold'),
        'subtitle': ParagraphStyle('RSub', parent=base['Normal'], fontSize=10,
                                   textColor=SLATE, spaceAfter=20),
        'section': ParagraphStyle('RSec', parent=base['Normal'], fontSize=9,
                                  textColor=SLATE, spaceAfter=8, fontName='Helvetica-Bold'),
        'body': ParagraphStyle('RBody', parent=base['Normal'], fontSize=10, textColor=SLATE),
        'small': ParagraphStyle('RSmall', parent=base['Normal'], fontSize=8, textColor=MUTED),
        'footer': ParagraphStyle('RFoot', parent=base['Normal'], fontSize=8,
                                 textColor=MUTED, alignment=TA_CENTER),
        'narrative': ParagraphStyle('RNarr', parent=base['Normal'], fontSize=10,
                                    textColor=SLATE, leading=16, spaceAfter=12),
    }


def _navy_header_table(data, col_widths, header_color=NAVY):
    """Build a table with a colored header row and alternating row stripes."""
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ]))
    return t


def _progress_ring(percent, size=80):
    """Draw a donut-style progress ring."""
    d = Drawing(size, size)
    cx, cy, r = size / 2, size / 2, size / 2 - 4
    # Background circle
    d.add(Circle(cx, cy, r, fillColor=LIGHT_BG, strokeColor=BORDER, strokeWidth=1))
    # Progress arc (drawn as wedge)
    color = GREEN if percent >= 75 else ACCENT if percent >= 25 else ORANGE
    if percent >= 100:
        # Full circle — just fill the ring
        d.add(Circle(cx, cy, r, fillColor=color, strokeColor=None, strokeWidth=0))
    elif percent > 0:
        angle = 360 * percent / 100
        d.add(Wedge(cx, cy, r, 90, 90 - angle, fillColor=color, strokeColor=None, strokeWidth=0))
    # Inner white circle to create donut effect
    d.add(Circle(cx, cy, r * 0.62, fillColor=WHITE, strokeColor=None, strokeWidth=0))
    # Center text
    d.add(String(cx, cy - 5, f"{percent:.0f}%", fontSize=14, fontName='Helvetica-Bold',
                 fillColor=NAVY, textAnchor='middle'))
    return d


def _status_label(status):
    """Human-readable status label."""
    return (status or 'unknown').replace('_', ' ').title()


def _days_remaining(due_date_str):
    """Calculate days until due date. Negative = overdue."""
    if not due_date_str:
        return None
    try:
        due = datetime.strptime(due_date_str[:10], '%Y-%m-%d').date()
        return (due - date.today()).days
    except (ValueError, TypeError):
        return None


# ═════════════════════════════════════════════════════════════════════════
#  ENGINEER REPORT
# ═════════════════════════════════════════════════════════════════════════

def generate_engineer_report(engineer_data, assignments_data, app_data, filename="engineer_report.pdf"):
    """Generate a comprehensive, executive-style PDF report for an engineer."""
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    elements = []
    S = _make_styles()

    engineer_name = engineer_data.get('name', 'Unknown Engineer')
    engineer_email = (engineer_data.get('email') or '').strip() or 'Not on file'

    # ── Header ──────────────────────────────────────────────────────────
    elements.append(Paragraph("Training & Readiness Report", S['title']))
    elements.append(Paragraph(
        f"Confidential  ·  {engineer_name}  ·  Generated {datetime.now().strftime('%B %d, %Y')}",
        S['subtitle']))
    elements.append(Spacer(1, 0.1 * inch))

    # ── Participant info ────────────────────────────────────────────────
    elements.append(Paragraph("PARTICIPANT INFORMATION", S['section']))
    trailhead_user = engineer_data.get('trailhead_username', '')
    if trailhead_user and trailhead_user.startswith("http"):
        trailhead_profile = trailhead_user.strip().rstrip("/")
    elif trailhead_user:
        trailhead_profile = f"https://www.salesforce.com/trailblazer/{trailhead_user}"
    else:
        trailhead_profile = ""

    info_rows = [
        ["Name", engineer_name],
        ["Email", engineer_email],
        ["Role", (engineer_data.get('role') or 'Engineer').title()],
    ]
    if trailhead_user:
        link = Paragraph(
            f'<a href="{trailhead_profile}" color="#3182ce">{trailhead_user}</a>',
            S['base']['Normal'])
        info_rows.append(["Trailhead", link])
    info_tbl = Table(info_rows, colWidths=[1.6 * inch, 4.4 * inch])
    info_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), SLATE),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    elements.append(info_tbl)
    elements.append(Spacer(1, 0.2 * inch))

    # ── Team history ────────────────────────────────────────────────────
    all_tenures = get_all_tenures(engineer_data)
    if all_tenures:
        elements.append(Paragraph("TEAM HISTORY", S['section']))
        tenure_rows = [["Team", "Region", "Onboarding Plan", "Start", "End"]]
        for t in all_tenures:
            team = TEAM_MAP.get(t.get("team", ""), t.get("team", "").replace("_", " ").title())
            geo = GEO_MAP.get(t.get("geo", ""), t.get("geo", "").upper())
            plan = PLAN_MAP.get(t.get("onboarding_plan", ""), t.get("onboarding_plan", "").replace("_", " ").title())
            start = (t.get("start_date") or "")[:10] or "—"
            end = (t.get("end_date") or "")[:10] if t.get("end_date") else "Ongoing"
            tenure_rows.append([team, geo, plan, start, end])
        elements.append(_navy_header_table(tenure_rows, [1.3*inch, 1.0*inch, 1.4*inch, 1.0*inch, 1.0*inch]))
    elements.append(Spacer(1, 0.25 * inch))

    # ── Trailhead profile ──────────────────────────────────────────────
    th_data = fetch_trailhead_profile(trailhead_user) if trailhead_user else None
    if th_data:
        elements.append(Paragraph("TRAILHEAD READINESS", S['section']))
        certs = th_data.get("certifications", [])
        active_certs = [c for c in certs if not c.get("expired")]

        th_stats = [
            ["Rank", th_data["rank"]],
            ["Badges", str(th_data["badges"])],
            ["Points", f"{th_data['points']:,}"],
            ["Trails Completed", str(th_data["trails"])],
            ["Superbadges", str(th_data["superbadges"])],
            ["Certifications", f"{len(active_certs)} active"],
        ]
        th_tbl = Table(th_stats, colWidths=[1.6 * inch, 4.4 * inch])
        th_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, -1), SLATE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ]))
        elements.append(th_tbl)

        if active_certs:
            elements.append(Spacer(1, 0.15 * inch))
            cert_rows = [["Certification", "Status", "Earned"]]
            for c in active_certs:
                cert_rows.append([c["title"], c["status"], c.get("date", "—")])
            elements.append(_navy_header_table(
                cert_rows, [3.4 * inch, 1.2 * inch, 1.0 * inch], header_color=ACCENT))

        if trailhead_profile:
            elements.append(Spacer(1, 0.05 * inch))
            elements.append(Paragraph(
                f'<a href="{trailhead_profile}" color="#3182ce">View full Trailhead profile</a>',
                S['small']))
        elements.append(Spacer(1, 0.25 * inch))

    # ── Executive summary ───────────────────────────────────────────────
    total = len(assignments_data)
    completed = [a for a in assignments_data if a.get('status') == 'completed']
    in_progress = [a for a in assignments_data if a.get('status') == 'in_progress']
    not_started = [a for a in assignments_data if a.get('status') in ('assigned', 'locked')]
    pct = (len(completed) / total * 100) if total > 0 else 0

    overdue_count = sum(1 for a in assignments_data
                        if a.get('status') != 'completed' and _days_remaining(a.get('due_date')) is not None
                        and _days_remaining(a.get('due_date')) < 0)

    elements.append(Paragraph("EXECUTIVE SUMMARY", S['section']))

    # Narrative paragraph
    overdue_note = (f'<font color="#e53e3e"><b>{overdue_count} module(s) are overdue.</b></font> '
                    if overdue_count else '')
    if pct == 100:
        narrative = f"{engineer_name} has <b>completed all {total} assigned modules</b>. No further action is required."
    elif pct == 0:
        narrative = (f"{engineer_name} has <b>{total} modules assigned</b> but has not completed any yet. "
                     f"{overdue_note}Immediate follow-up is recommended.")
    else:
        narrative = (f"{engineer_name} has completed <b>{len(completed)} of {total}</b> modules ({pct:.0f}%). "
                     f"<b>{len(in_progress)}</b> module(s) are in progress and <b>{len(not_started)}</b> are pending. "
                     f"{overdue_note}")
    elements.append(Paragraph(narrative, S['narrative']))

    # Progress ring + stats side by side
    ring = _progress_ring(pct)
    stats_rows = [
        ["Completed", str(len(completed)), f"{pct:.0f}%"],
        ["In Progress", str(len(in_progress)), ""],
        ["Not Started", str(len(not_started)), ""],
        ["Overdue", str(overdue_count), ""],
        ["Total", str(total), ""],
    ]
    stats_tbl = Table(stats_rows, colWidths=[1.6*inch, 0.8*inch, 0.8*inch])
    stats_tbl.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), SLATE),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER),
        # Highlight overdue in red
        ('TEXTCOLOR', (1, 3), (2, 3), RED if overdue_count else SLATE),
    ]))
    summary_layout = Table([[ring, stats_tbl]], colWidths=[1.2*inch, 3.5*inch])
    summary_layout.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (1, 0), (1, 0), 20),
    ]))
    elements.append(summary_layout)
    elements.append(Spacer(1, 0.3 * inch))

    # ── Velocity / timeline ─────────────────────────────────────────────
    completed_with_dates = [a for a in completed if a.get('completed_at')]
    if completed_with_dates:
        completed_with_dates.sort(key=lambda a: a['completed_at'])
        first_done = completed_with_dates[0]['completed_at'][:10]
        last_done = completed_with_dates[-1]['completed_at'][:10]
        elements.append(Paragraph("COMPLETION TIMELINE", S['section']))
        timeline_rows = [["Module", "Completed On"]]
        for a in completed_with_dates:
            mid = str(a.get('module_id', ''))
            mod_name = app_data.get("modules", {}).get(mid, {}).get("name") or a.get("module_name") or f"Module {mid}"
            done_date = a['completed_at'][:10]
            timeline_rows.append([mod_name, done_date])
        elements.append(_navy_header_table(timeline_rows, [4.0*inch, 2.0*inch], header_color=GREEN))
        elements.append(Spacer(1, 0.05 * inch))
        elements.append(Paragraph(
            f"First completion: {first_done}  ·  Latest: {last_done}  ·  "
            f"Avg pace: {len(completed_with_dates)} module(s) over "
            f"{max(1, (datetime.strptime(last_done, '%Y-%m-%d') - datetime.strptime(first_done, '%Y-%m-%d')).days)} days",
            S['small']))
        elements.append(Spacer(1, 0.25 * inch))

    # ── In-progress & upcoming detail ───────────────────────────────────
    active = in_progress + not_started
    if active:
        elements.append(Paragraph("ACTIVE & UPCOMING MODULES", S['section']))
        detail_rows = [["#", "Module", "Status", "Due Date", "Days Left"]]
        active.sort(key=lambda a: (a.get('sequence_order') or 0, a.get('id', 0)))
        for i, a in enumerate(active, 1):
            mid = str(a.get('module_id', ''))
            mod_name = app_data.get("modules", {}).get(mid, {}).get("name") or a.get("module_name") or f"Module {mid}"
            status = _status_label(a.get('status'))
            due = (a.get('due_date') or '—')[:10]
            days = _days_remaining(a.get('due_date'))
            if days is None:
                days_text = "—"
            elif days < 0:
                days_text = f"{abs(days)}d OVERDUE"
            elif days == 0:
                days_text = "Due today"
            else:
                days_text = f"{days}d"
            detail_rows.append([str(i), mod_name, status, due, days_text])

        detail_tbl = _navy_header_table(detail_rows, [0.4*inch, 2.6*inch, 1.2*inch, 1.0*inch, 1.0*inch])
        # Color-code overdue cells
        for row_idx in range(1, len(detail_rows)):
            cell_text = detail_rows[row_idx][4]
            if "OVERDUE" in str(cell_text):
                detail_tbl.setStyle(TableStyle([
                    ('TEXTCOLOR', (4, row_idx), (4, row_idx), RED),
                    ('FONTNAME', (4, row_idx), (4, row_idx), 'Helvetica-Bold'),
                ]))
        elements.append(detail_tbl)
        elements.append(Spacer(1, 0.25 * inch))

    # ── All assignments summary table ───────────────────────────────────
    if assignments_data:
        elements.append(Paragraph("FULL ASSIGNMENT LOG", S['section']))
        all_rows = [["Module", "Type", "Status", "Due", "Completed"]]
        sorted_all = sorted(assignments_data, key=lambda a: (a.get('sequence_order') or 0, a.get('id', 0)))
        for a in sorted_all:
            mid = str(a.get('module_id', ''))
            atype = (a.get('type') or 'module').title()
            if atype == 'Assessment':
                mod_name = app_data.get("assessments", {}).get(mid, {}).get("name") or a.get("module_name") or f"Assessment {mid}"
            else:
                mod_name = app_data.get("modules", {}).get(mid, {}).get("name") or a.get("module_name") or f"Module {mid}"
            status = _status_label(a.get('status'))
            due = (a.get('due_date') or '—')[:10]
            done = a.get('completed_at', '')[:10] if a.get('completed_at') else '—'
            all_rows.append([mod_name, atype, status, due, done])

        all_tbl = _navy_header_table(all_rows, [2.4*inch, 0.8*inch, 1.0*inch, 1.0*inch, 1.0*inch])
        # Highlight completed rows green, overdue red
        for row_idx in range(1, len(all_rows)):
            if all_rows[row_idx][2] == 'Completed':
                all_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, row_idx), (-1, row_idx), LIGHT_GREEN),
                ]))
            orig_assign = sorted_all[row_idx - 1]
            days = _days_remaining(orig_assign.get('due_date'))
            if days is not None and days < 0 and orig_assign.get('status') != 'completed':
                all_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, row_idx), (-1, row_idx), LIGHT_RED),
                ]))
        elements.append(all_tbl)
    else:
        elements.append(Paragraph("No assignments recorded for this participant.", S['body']))

    # ── Footer ──────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  ·  "
        f"CloudSuccess LevelUp  ·  Training & Readiness",
        S['footer']))

    doc.build(elements)
    return filename


# ═════════════════════════════════════════════════════════════════════════
#  MODULE REPORT (unchanged API, refreshed styling)
# ═════════════════════════════════════════════════════════════════════════

def generate_module_report(module_id, module_name, app_data, status_filter=None, filename="module_report.pdf"):
    """Generate a PDF report for a specific module showing all assigned engineers."""
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=54, leftMargin=54,
                            topMargin=54, bottomMargin=54)
    elements = []
    S = _make_styles()

    elements.append(Paragraph(f"Module Report – {module_name}", S['title']))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y')}  ·  "
        f"{'Filter: ' + status_filter.replace('_',' ').title() if status_filter and status_filter != 'all' else 'All statuses'}",
        S['subtitle']))

    # Gather assignments
    module_assignments = []
    for assign_id, assign_data in app_data["assignments"].items():
        if str(assign_data.get("module_id")) == module_id or assign_data.get("module_id") == module_id:
            if status_filter and status_filter != "all":
                if assign_data.get("status") == status_filter:
                    module_assignments.append(assign_data)
            else:
                module_assignments.append(assign_data)

    total = len(module_assignments)
    comp = len([a for a in module_assignments if a.get('status') == 'completed'])
    pct = (comp / total * 100) if total > 0 else 0

    # Summary
    elements.append(Paragraph("SUMMARY", S['section']))
    ring = _progress_ring(pct)
    stats_rows = [
        ["Total Assigned", str(total)],
        ["Completed", f"{comp} ({pct:.0f}%)"],
        ["In Progress", str(len([a for a in module_assignments if a.get('status') == 'in_progress']))],
        ["Not Started", str(len([a for a in module_assignments if a.get('status') in ('assigned', 'locked')]))],
    ]
    stats_tbl = Table(stats_rows, colWidths=[2.0*inch, 1.5*inch])
    stats_tbl.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), SLATE),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    layout = Table([[ring, stats_tbl]], colWidths=[1.2*inch, 4.0*inch])
    layout.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (1, 0), (1, 0), 20)]))
    elements.append(layout)
    elements.append(Spacer(1, 0.25 * inch))

    # Engineer detail
    if module_assignments:
        elements.append(Paragraph("ASSIGNED ENGINEERS", S['section']))
        rows = [['Engineer', 'Team', 'Status', 'Due Date', 'Days Left']]
        for a in module_assignments:
            eng = app_data["engineers"].get(str(a.get('engineer_id', '')), {})
            eng_name = eng.get('name', 'Unknown')
            team = TEAM_MAP.get(get_team(eng), get_team(eng).replace('_', ' ').title())
            status = _status_label(a.get('status'))
            due = (a.get('due_date') or '—')[:10]
            days = _days_remaining(a.get('due_date'))
            days_text = "—" if days is None else (f"{abs(days)}d overdue" if days < 0 else f"{days}d")
            rows.append([eng_name, team, status, due, days_text])
        tbl = _navy_header_table(rows, [1.8*inch, 1.4*inch, 1.0*inch, 1.0*inch, 1.0*inch])
        for row_idx in range(1, len(rows)):
            if "overdue" in str(rows[row_idx][4]):
                tbl.setStyle(TableStyle([('TEXTCOLOR', (4, row_idx), (4, row_idx), RED)]))
        elements.append(tbl)
    else:
        elements.append(Paragraph("No engineers assigned to this module.", S['body']))

    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  ·  CloudSuccess LevelUp",
        S['footer']))
    doc.build(elements)
    return filename


# ═════════════════════════════════════════════════════════════════════════
#  ASSESSMENT REPORT
# ═════════════════════════════════════════════════════════════════════════

def generate_assessment_report(assessment_id, assessment_name, app_data, status_filter=None, filename="assessment_report.pdf"):
    """Generate a PDF report for a specific assessment showing all assigned engineers."""
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=54, leftMargin=54,
                            topMargin=54, bottomMargin=54)
    elements = []
    S = _make_styles()

    elements.append(Paragraph(f"Assessment Report – {assessment_name}", S['title']))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y')}  ·  "
        f"{'Filter: ' + status_filter.replace('_',' ').title() if status_filter and status_filter != 'all' else 'All statuses'}",
        S['subtitle']))

    assessment_assignments = []
    for assign_id, assign_data in app_data["assignments"].items():
        if assign_data.get("type") == "assessment" and str(assign_data.get("module_id")) == assessment_id:
            if status_filter and status_filter != "all":
                if assign_data.get("status") == status_filter:
                    assessment_assignments.append(assign_data)
            else:
                assessment_assignments.append(assign_data)

    total = len(assessment_assignments)
    comp = len([a for a in assessment_assignments if a.get('status') == 'completed'])
    pct = (comp / total * 100) if total > 0 else 0

    elements.append(Paragraph("SUMMARY", S['section']))
    ring = _progress_ring(pct)
    stats_rows = [
        ["Total Assigned", str(total)],
        ["Completed", f"{comp} ({pct:.0f}%)"],
        ["In Progress", str(len([a for a in assessment_assignments if a.get('status') == 'in_progress']))],
        ["Not Started", str(len([a for a in assessment_assignments if a.get('status') in ('assigned', 'locked')]))],
    ]
    stats_tbl = Table(stats_rows, colWidths=[2.0*inch, 1.5*inch])
    stats_tbl.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), SLATE),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    layout = Table([[ring, stats_tbl]], colWidths=[1.2*inch, 4.0*inch])
    layout.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (1, 0), (1, 0), 20)]))
    elements.append(layout)
    elements.append(Spacer(1, 0.25 * inch))

    if assessment_assignments:
        elements.append(Paragraph("ASSIGNED ENGINEERS", S['section']))
        rows = [['Engineer', 'Status', 'Due Date', 'Assigned']]
        for a in assessment_assignments:
            eng = app_data["engineers"].get(str(a.get('engineer_id', '')), {})
            eng_name = eng.get('name', 'Unknown')
            status = _status_label(a.get('status'))
            due = (a.get('due_date') or '—')[:10]
            assigned_dt = a.get('assigned_at', '')[:10] if a.get('assigned_at') else '—'
            rows.append([eng_name, status, due, assigned_dt])
        elements.append(_navy_header_table(rows, [2.2*inch, 1.4*inch, 1.3*inch, 1.4*inch], header_color=ACCENT))
    else:
        elements.append(Paragraph("No engineers assigned to this assessment.", S['body']))

    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  ·  CloudSuccess LevelUp",
        S['footer']))
    doc.build(elements)
    return filename


# ═════════════════════════════════════════════════════════════════════════
#  DUE / OVERDUE REPORT
# ═════════════════════════════════════════════════════════════════════════

def generate_due_report(app_data, filename="due_report.pdf"):
    """Generate a PDF report showing engineers who are behind schedule."""
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=54, leftMargin=54,
                            topMargin=54, bottomMargin=54)
    elements = []
    S = _make_styles()

    today = date.today()

    elements.append(Paragraph("Overdue Assignments Report", S['title']))
    elements.append(Paragraph(f"Generated {today.strftime('%B %d, %Y')}  ·  Behind-schedule items only", S['subtitle']))

    # Collect overdue
    overdue = []
    for assign_id, a in app_data["assignments"].items():
        if a.get('status') == 'completed':
            continue
        days = _days_remaining(a.get('due_date'))
        if days is not None and days < 0:
            a['_days_overdue'] = abs(days)
            overdue.append(a)
    overdue.sort(key=lambda x: x['_days_overdue'], reverse=True)

    unique_eng = len(set(str(a.get('engineer_id')) for a in overdue))

    elements.append(Paragraph("SUMMARY", S['section']))
    summary_rows = [
        ["Total Overdue", str(len(overdue))],
        ["Engineers Affected", str(unique_eng)],
        ["Most Overdue", f"{overdue[0]['_days_overdue']} days" if overdue else "—"],
    ]
    summary_tbl = Table(summary_rows, colWidths=[2.5*inch, 2.5*inch])
    summary_tbl.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), SLATE),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_RED),
    ]))
    elements.append(summary_tbl)
    elements.append(Spacer(1, 0.25 * inch))

    if overdue:
        elements.append(Paragraph("OVERDUE DETAIL", S['section']))
        rows = [['Engineer', 'Module', 'Due Date', 'Days Overdue', 'Status']]
        for a in overdue:
            eng = app_data["engineers"].get(str(a.get('engineer_id', '')), {})
            eng_name = eng.get('name', 'Unknown')
            mid = str(a.get('module_id', ''))
            if a.get('type') == 'assessment':
                mod_name = app_data.get("assessments", {}).get(mid, {}).get("name", f"Assessment {mid}")
            else:
                mod_name = app_data.get("modules", {}).get(mid, {}).get("name") or a.get("module_name") or f"Module {mid}"
            due = (a.get('due_date') or '—')[:10]
            days_over = a['_days_overdue']
            severity = "CRITICAL" if days_over > 7 else "WARNING" if days_over > 3 else "MINOR"
            status = _status_label(a.get('status'))
            rows.append([eng_name, mod_name, due, f"{days_over}d ({severity})", status])

        tbl = _navy_header_table(rows, [1.5*inch, 1.8*inch, 1.0*inch, 1.3*inch, 1.0*inch], header_color=RED)
        for row_idx in range(1, len(rows)):
            if "CRITICAL" in str(rows[row_idx][3]):
                tbl.setStyle(TableStyle([
                    ('TEXTCOLOR', (3, row_idx), (3, row_idx), RED),
                    ('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'),
                ]))
        elements.append(tbl)
        elements.append(Spacer(1, 0.25 * inch))

        elements.append(Paragraph("RECOMMENDED ACTIONS", S['section']))
        recs = [
            "Follow up immediately with engineers who have CRITICAL (>7 days) overdue items.",
            "Consider extending deadlines for WARNING (>3 days) items if blocked by dependencies.",
            "Send reminder notifications for MINOR items that may have been overlooked.",
        ]
        for r in recs:
            elements.append(Paragraph(f"•  {r}", S['body']))
            elements.append(Spacer(1, 4))
    else:
        elements.append(Paragraph(
            "All engineers are on track — no overdue assignments found.", S['body']))

    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  ·  CloudSuccess LevelUp",
        S['footer']))
    doc.build(elements)
    return filename
