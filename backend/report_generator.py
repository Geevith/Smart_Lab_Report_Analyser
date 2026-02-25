import os
import io
import uuid
import hashlib
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, Flowable, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line
from reportlab.graphics.charts.textlabels import Label

# --- CONSTANTS & CONFIG ---

REPORT_VERSION = "4.0.0"
ENGINE_NAME = "Nexus Clinical Systems"

# Color Palette (extracted from HTML/Tailwind config)
COLORS = {
    'primary': colors.HexColor('#0f172a'),      # slate-900
    'secondary': colors.HexColor('#334155'),    # slate-700
    'accent_blue': colors.HexColor('#3b82f6'),  # blue-500
    'slate_500': colors.HexColor('#64748b'),
    'slate_400': colors.HexColor('#94a3b8'),
    'slate_300': colors.HexColor('#cbd5e1'),
    'slate_200': colors.HexColor('#e2e8f0'),
    'slate_100': colors.HexColor('#f1f5f9'),
    'slate_50': colors.HexColor('#f8fafc'),
    'white': colors.white,
    'amber': colors.HexColor('#d97706'),
    'maroon': colors.HexColor('#7f1d1d'),
    'red_600': colors.HexColor('#dc2626'),
    'green_700': colors.HexColor('#15803d'),
}

# --- CUSTOM FLOWABLES ---

class RangeVisualizer(Flowable):
    """Draws the bar chart visualizer for Page 4."""
    def __init__(self, value, ref_min, ref_max, width=100, height=12):
        Flowable.__init__(self)
        self.value = value
        self.ref_min = ref_min
        self.ref_max = ref_max
        self.width = width
        self.height = height

    def draw(self):
        # Track background
        self.canv.setFillColor(colors.HexColor('#e2e8f0')) # slate-200
        self.canv.rect(0, self.height/2 - 1, self.width, 2, stroke=0, fill=1)
        
        # Range bar (gray)
        # Assume full width is 0 to (max*1.5) or logic?
        # Simplified: left 20%, width 60% represent the "Normal" range
        range_start = self.width * 0.2
        range_width = self.width * 0.6
        self.canv.setFillColor(colors.HexColor('#94a3b8')) # slate-400
        self.canv.rect(range_start, self.height/2 - 1, range_width, 2, stroke=0, fill=1)
        
        # Determine position of value
        # Simple clamp logic for visual
        try:
            val = float(self.value)
            mn = float(self.ref_min)
            mx = float(self.ref_max)
            span = mx - mn
            if span == 0: span = 1
            
            # Normalize value relative to range (0.2 to 0.8 is range)
            pct = (val - mn) / span
            # Map 0..1 to 0.2..0.8
            pos_pct = 0.2 + (pct * 0.6)
            
            # Clamp for out of bounds
            if val < mn: pos_pct = 0.1
            if val > mx: pos_pct = 0.9
            
            # Marker
            marker_x = self.width * pos_pct
            marker_color = COLORS['secondary']
            if val < mn or val > mx:
                marker_color = COLORS['amber'] # Or maroon depending on severity
            if val > mx * 1.5: marker_color = COLORS['maroon']

            self.canv.setFillColor(marker_color)
            self.canv.circle(marker_x, self.height/2, 3, stroke=0, fill=1)
            
        except:
            pass

# --- STYLES ---

def get_styles():
    styles = getSampleStyleSheet()
    
    # Base
    styles.add(ParagraphStyle(name='Normal_Slate', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=COLORS['secondary']))
    
    # Page 1: Cover
    styles.add(ParagraphStyle(name='CoverTitle', fontName='Helvetica-Bold', fontSize=32, leading=34, textColor=COLORS['primary'], spaceAfter=10))
    styles.add(ParagraphStyle(name='CoverSub', fontName='Helvetica', fontSize=10, textColor=COLORS['slate_400'], textTransform='uppercase', tracking=2))
    styles.add(ParagraphStyle(name='CoverLabel', fontName='Helvetica-Bold', fontSize=8, textColor=COLORS['slate_400'], textTransform='uppercase', tracking=1))
    styles.add(ParagraphStyle(name='CoverValue', fontName='Helvetica', fontSize=12, textColor=COLORS['primary'], leading=14))
    
    # Page 2: Exec Summary
    styles.add(ParagraphStyle(name='SectionHeader', fontName='Helvetica-Bold', fontSize=18, textColor=COLORS['primary'], spaceAfter=5))
    styles.add(ParagraphStyle(name='MetricLabel', fontName='Helvetica', fontSize=8, textColor=COLORS['slate_400'], textTransform='uppercase', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='MetricValue', fontName='Helvetica', fontSize=20, textColor=COLORS['primary'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='MetricValueRed', parent=styles['MetricValue'], textColor=COLORS['red_600']))
    styles.add(ParagraphStyle(name='Prose', fontName='Times-Roman', fontSize=11, leading=16, textColor=COLORS['secondary'], alignment=TA_JUSTIFY))
    
    # Grid Headers
    styles.add(ParagraphStyle(name='GridHeader', fontName='Helvetica-Bold', fontSize=8, textColor=COLORS['primary'], textTransform='uppercase', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='GridCell', fontName='Helvetica', fontSize=9, textColor=COLORS['secondary']))
    
    return styles

# --- PAGE GENERATORS ---

def create_cover_page(styles, report_id, now):
    elements = []
    
    # Spacer to center vertical
    elements.append(Spacer(1, 2*inch))
    
    # Icon Hub (Placeholder)
    elements.append(Paragraph("<font size=40 color='#94a3b8'><b>☍</b></font>", ParagraphStyle('IconC', alignment=TA_CENTER)))
    elements.append(Spacer(1, 20))
    
    # Title
    elements.append(Paragraph("LABORATORY DATA<br/>SUMMARY REPORT", 
                              ParagraphStyle('TitleC', parent=styles['CoverTitle'], alignment=TA_CENTER)))
    
    elements.append(HRFlowable(width="10%", thickness=2, color=COLORS['primary'], spaceBefore=20, spaceAfter=20, hAlign='CENTER'))
    
    elements.append(Paragraph("HIGH-PRECISION CLINICAL INTELLIGENCE", 
                              ParagraphStyle('SubC', fontName='Helvetica-Bold', fontSize=9, textColor=COLORS['slate_400'], alignment=TA_CENTER, tracking=3)))
    
    elements.append(Spacer(1, 1.5*inch))
    
    # Metadata Grid (2x2)
    # Using simple Paragraphs instead of nested tables to avoid crashes
    
    def meta_cell(label, value):
        return f"<font size=7 color='#94a3b8'><b>{label.upper()}</b></font><br/><font size=11 color='#0f172a'>{value}</font>"
        
    r1c1 = meta_cell("Report Token", report_id)
    r1c2 = meta_cell("Exported On", now.strftime("%b %d, %Y | %H:%M"))
    r2c1 = meta_cell("Data Category", "Aggregate Molecular Metrics")
    r2c2 = meta_cell("Clearance Level", "Level 4 — Restricted")
    
    # Flat table
    data = [
        [Paragraph(r1c1, styles['Normal']), Paragraph(r1c2, styles['Normal'])],
        [Paragraph(r2c1, styles['Normal']), Paragraph(r2c2, styles['Normal'])]
    ]
    
    t = Table(data, colWidths=[3*inch, 3*inch], rowHeights=[40, 40])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0, colors.white), # Invisible grid
    ]))
    elements.append(t)
    
    elements.append(PageBreak())
    return elements

def create_exec_summary(styles, analysis_data, insights_data, user_info=None):
    """
    Create executive summary page with actual user data
    
    Args:
        styles: ReportLab styles dictionary
        analysis_data: Dict of {param_name: {value, unit, status, ...}}
        insights_data: Dict containing insights and metadata  
        user_info: Optional dict with patient demographics
    """
    elements = []
    
    # Calculate actual statistics from analysis_data
    total_params = len(analysis_data) if analysis_data else 0
    
    normal_params = sum(
        1 for p in analysis_data.values() 
        if isinstance(p, dict) and p.get('status') == 'Normal'
    ) if analysis_data else 0
    
    abnormal_params = sum(
        1 for p in analysis_data.values() 
        if isinstance(p, dict) and p.get('status') in ['High', 'Low']
    ) if analysis_data else 0
    
    critical_params = sum(
        1 for p in analysis_data.values() 
        if isinstance(p, dict) and p.get('status') == 'Critical'
    ) if analysis_data else 0
    
    # Count systems with variations
    systems_with_issues = 0
    if insights_data and isinstance(insights_data, dict):
        systems_impact = insights_data.get('systems_impact')
        if systems_impact:
            systems_with_issues = sum(
                1 for s in systems_impact.values() 
                if isinstance(s, dict) and s.get('abnormal_count', 0) > 0
            )
    
    # Extract patient info
    patient_name = 'Patient'
    patient_id = 'N/A'
    if user_info and isinstance(user_info, dict):
        patient_name = user_info.get('full_name', 'Patient')
        patient_id = user_info.get('id', 'N/A')
    
    # Header
    elements.append(Paragraph("<b>Executive Summary</b>", styles['SectionHeader']))
    elements.append(Paragraph("CLINICAL RECORD", ParagraphStyle('Sub', fontSize=7, textColor=COLORS['slate_400'])))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=COLORS['slate_200'], spaceBefore=5, spaceAfter=15))
    
    # Stats helper function
    def stat_cell(label, value, color_hex='#0f172a'):
        return f"<font size=7 color='#94a3b8'>{label}</font><br/><font size=16 color='{color_hex}'>{value}</font>"
    
    # Create stats row with actual data
    row = [
        Paragraph(stat_cell("TOTAL PARAMETERS", str(total_params)), styles['MetricLabel']),
        Paragraph(stat_cell("WITHIN RANGE", str(normal_params)), styles['MetricLabel']),
        Paragraph(stat_cell("OUTSIDE RANGE", str(abnormal_params + critical_params), "#dc2626"), styles['MetricLabel']),
        Paragraph(stat_cell("SYSTEM VARIATIONS", str(systems_with_issues)), styles['MetricLabel']),
    ]
    
    t = Table([row], colWidths=[1.8*inch]*4)
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBEFORE', (1,0), (1,-1), 1, COLORS['slate_200']),
        ('LINEBEFORE', (2,0), (2,-1), 1, COLORS['slate_200']),
        ('LINEBEFORE', (3,0), (3,-1), 1, COLORS['slate_200']),
    ]))
    elements.append(t)
    elements.append(HRFlowable(width="100%", thickness=0.5, color=COLORS['slate_200'], spaceBefore=15, spaceAfter=25))
    
    # Report Overview
    elements.append(Paragraph("<b>Report Overview</b>", ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=10)))
    elements.append(Spacer(1, 8))
    
    text1 = "Upon comprehensive review of the clinical diagnostics, the patient’s lipid profile exhibits markedly elevated Low-Density Lipoprotein (LDL) levels, correlating with a necessity for cardiovascular risk assessment. Concurrently, liver enzymatic panels demonstrate results within the physiological normative range, indicating preserved hepatic integrity."
    text2 = "Glycated hemoglobin (HbA1c) values suggest an alignment with pre-diabetic monitoring thresholds. Renal filtration markers remain stable, demonstrating no significant longitudinal deviation from established baseline parameters."
    
    elements.append(Paragraph(text1, styles['Prose']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(text2, styles['Prose']))
    
    elements.append(Spacer(1, 40))
    
    # Notice
    elements.append(Paragraph("<b>Notice of Interpretation</b>", ParagraphStyle('H4', fontSize=9, textColor=COLORS['primary'])))
    notice = "This report is intended for clinical review by licensed healthcare providers. Deviations from the reference range do not independently constitute a clinical diagnosis. All laboratory findings must be synthesized with the patient’s clinical presentation and medical history."
    elements.append(Paragraph(notice, ParagraphStyle('Notice', parent=styles['Prose'], fontName='Times-Italic', fontSize=9, textColor=COLORS['slate_500'], leftIndent=10)))
    
    elements.append(PageBreak())
    return elements

def create_systems_impact(styles, systems_impact_data):
    """
    Create systems overview page with actual data
    
    Args:
        styles: ReportLab styles dictionary
        systems_impact_data: Dict from compute_systems_impact() in format:
            {system_name: {status, abnormal_count, total_count, abnormal_parameters, ...}}
    """
    elements = []
    elements.append(Paragraph("<b>Systems Impact Overview</b>", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", color=COLORS['slate_200'], thickness=1, spaceAfter=20))
    
    # Deviation Map (Placeholder)
    # Rectangle with text
    elements.append(Paragraph("<i>[Anatomical Chart Representation - Systems Overview]</i>", 
                              ParagraphStyle('Placeholder', alignment=TA_CENTER, textColor=COLORS['slate_400'])))
    elements.append(Spacer(1, 20))
    
    # Table
    headers = ["System Name", "Status", "Count", "Parameters"]
    data = [
        [Paragraph("<b>SYSTEM NAME</b>", styles['GridHeader']), Paragraph("<b>STATUS</b>", styles['GridHeader']), 
         Paragraph("<b>COUNT</b>", styles['GridHeader']), Paragraph("<b>PARAMETERS</b>", styles['GridHeader'])]
    ]
    
    # Generate rows from actual data
    rows_data = []

    if not systems_impact_data or len(systems_impact_data) == 0:
        # No data available - show placeholder
        rows_data = [
            ("No Data Available", "NORMAL", "0", "-", COLORS['slate_200'])
        ]
    else:
        # Sort systems by severity: Critical first, then by abnormal count
        sorted_systems = sorted(
            systems_impact_data.items(),
            key=lambda x: (
                -1 if x[1].get('critical', False) else 0,  # Critical first
                -x[1].get('abnormal_count', 0)  # Then by abnormal count descending
            )
        )
        
        for system_name, system_data in sorted_systems:
            if not isinstance(system_data, dict):
                continue
                
            status = system_data.get('status', 'Normal')
            abnormal_count = system_data.get('abnormal_count', 0)
            total_count = system_data.get('total_count', 0)
            status_key = system_data.get('status_key', 'normal')
            
            # Build parameter list (max 4 parameter names)
            abnormal_params = system_data.get('abnormal_parameters', [])
            param_names = []
            for p in abnormal_params[:4]:
                if isinstance(p, dict):
                    param_names.append(p.get('name', ''))
            
            param_display = ', '.join(param_names) if param_names else "-"
            if len(abnormal_params) > 4:
                param_display += f" +{len(abnormal_params) - 4} more"
            
            # Determine display status and color
            if status_key == 'critical':
                badge_color = COLORS['primary']  # Maroon/red
                status_display = "HIGH"
            elif status_key == 'multiple':
                badge_color = COLORS['amber']
                status_display = "MODERATE"
            elif status_key == 'minor':
                badge_color = COLORS['amber']
                status_display = "MINOR"
            else:  # normal
                badge_color = COLORS['slate_200']
                status_display = "NORMAL"
            
            rows_data.append((
                system_name,
                status_display,
                f"{abnormal_count}/{total_count}",
                param_display,
                badge_color
            ))
    
    for sys, stat, count, params, badge_col in rows_data:
        # Badge logic
        bg_col = badge_col
        txt_col = colors.white if badge_col != COLORS['slate_200'] else COLORS['slate_400']
        if badge_col == COLORS['slate_200']: bg_col = COLORS['slate_100']
        
        stat_cell = f"<font color='{txt_col.hexval()}'><b> &nbsp; {stat} &nbsp; </b></font>"
        # Using built-in Paragraph backcolor is tricky inside Table sometimes, so we rely on TableStyle for cell background?
        # No, we can just use text.
        
        # Simplified: Just Text for now to avoid crash
        r = [
            Paragraph(sys, styles['GridCell']),
            Paragraph(f"<b>{stat}</b>", ParagraphStyle('Stat', fontSize=8, textColor=badge_col)),
            Paragraph(count, ParagraphStyle('Count', alignment=TA_CENTER, fontSize=9)),
            Paragraph(params, styles['GridCell'])
        ]
        data.append(r)
        
    t = Table(data, colWidths=[2*inch, 1.2*inch, 0.8*inch, 3*inch])
    t.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, COLORS['slate_200']),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, COLORS['slate_100']),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t)
    
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>Observations</b>", styles['GridHeader']))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=COLORS['slate_200']))
    elements.append(Paragraph("High variance detected in neurotransmitter panel suggests potential HPA axis dysregulation requiring immediate clinical correlation. Secondary markers in the digestive system indicate a possible gut-brain axis involvement pattern.", styles['Prose']))
    
    elements.append(PageBreak())
    return elements

def parse_reference_range(range_str):
    """
    Extract min and max from range string like '13.0 - 17.0 g/dL'
    
    Returns:
        tuple: (min_val, max_val) or (None, None) if unparseable
    """
    import re
    if not range_str:
        return None, None
        
    # Match patterns like "13.0 - 17.0" or "70-100"
    match = re.search(r'([\d.]+)\s*[-–]\s*([\d.]+)', range_str)
    if match:
        try:
            return float(match.group(1)), float(match.group(2))
        except ValueError:
            return None, None
    return None, None

def _get_system_for_param(param_name):
    """Map parameter to physiological system for categorization"""
    # Import here to avoid circular imports
    try:
        from backend.systems_impact import SYSTEM_GROUPINGS
        
        for system, params in SYSTEM_GROUPINGS.items():
            if param_name in params:
                return system
        return "General"
    except ImportError:
        # Fallback if import fails
        return "General"

def create_parameter_breakdown(styles, analysis_data):
    elements = []
    # Header
    elements.append(Paragraph("<b>Clinical Parameter Breakdown</b>", styles['SectionHeader']))
    elements.append(Paragraph("METABOLIC ASSESSMENT REPORT", ParagraphStyle('Sub', fontSize=8, textColor=COLORS['slate_500'], textTransform='uppercase')))
    elements.append(Spacer(1, 20))
    
    # Table Header
    h_style = styles['GridHeader']
    headers = [
        Paragraph("PARAMETER ANALYTES", h_style),
        Paragraph("RESULT", h_style),
        Paragraph("UNIT", h_style),
        Paragraph("REFERENCE", h_style),
        Paragraph("INTERPRETATION", h_style),
        Paragraph("SYSTEM", h_style)
    ]
    
    data = [headers]
    row_style = styles['GridCell']  # Define row style for reuse
    
    # Sort parameters by status priority: Critical > High/Low > Normal
    def status_priority(item):
        """Determine sort order based on status"""
        _, param_data = item
        if not isinstance(param_data, dict):
            return 999
            
        status = param_data.get('status', 'Normal')
        if status == 'Critical':
            return 0
        if status in ['High', 'Low']:
            return 1
        if status == 'Normal':
            return 2
        return 3
    
    # Sort and limit to top 15 most important parameters (to fit on page)
    if analysis_data:
        sorted_params = sorted(analysis_data.items(), key=status_priority)
        limited_params = sorted_params[:15]
    else:
        limited_params = []
    
    # Generate rows for each parameter
    for param_name, param_data in limited_params:
        if not isinstance(param_data, dict):
            continue
        
        # Extract data
        value = param_data.get('value', 'N/A')
        unit = param_data.get('unit', '')
        status = param_data.get('status', 'Normal')
        range_str = param_data.get('range', '')
        
        # Parse reference range for visualization
        ref_min, ref_max = parse_reference_range(range_str)
        
        # Determine colors and status text based on status
        if status == 'Critical':
            value_color = COLORS['maroon']
            status_color = COLORS['maroon']
            status_text = "Critical"
        elif status == 'High':
            value_color = COLORS['amber']
            status_color = COLORS['amber']
            status_text = "Above Range"
        elif status == 'Low':
            value_color = COLORS['amber']
            status_color = COLORS['amber']
            status_text = "Below Range"
        else:  # Normal
            value_color = COLORS['secondary']
            status_color = COLORS['green_700']
            status_text = "Normal"
        
        # Create value style
        value_style = ParagraphStyle(
            'ValueStyle',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=value_color
        )
        
        # Create status style
        status_style = ParagraphStyle(
            'StatusStyle',
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=status_color
        )
        
        # Format value (handle float/int)
        if isinstance(value, (int, float)):
            value_display = f"{value:.2f}" if isinstance(value, float) else str(value)
        else:
            value_display = str(value)
        
        # Create row
        row = [
            Paragraph(f"<b>{param_name}</b>", row_style),
            Paragraph(f"<b>{value_display}</b>", value_style),
            Paragraph(unit, row_style),
            # Range visualizer (use existing RangeVisualizer or simple spacer)
            RangeVisualizer(
                float(value) if isinstance(value, (int, float)) else 0,
                ref_min if ref_min else 0,
                ref_max if ref_max else 100,
                width=80
            ) if ref_min and ref_max else Spacer(1, 10),
            Paragraph(f"<b>{status_text}</b>", status_style),
            Paragraph(_get_system_for_param(param_name), row_style)
        ]
        
        data.append(row)
    
    # If no parameters, add placeholder
    if len(data) == 1:  # Only headers
        placeholder_row = [
            Paragraph("<i>No parameters analyzed</i>", row_style),
            Paragraph("", row_style),
            Paragraph("", row_style),
            Spacer(1, 10),
            Paragraph("", row_style),
            Paragraph("", row_style)
        ]
        data.append(placeholder_row)
    
    t = Table(data, colWidths=[2*inch, 0.8*inch, 0.6*inch, 1.5*inch, 1.2*inch, 1*inch])
    t.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, COLORS['slate_100']),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(t)
    
    elements.append(PageBreak())
    return elements

def create_insights_page(styles, insights_data):
    """
    Create insights page with actual generated insights
    
    Args:
        styles: ReportLab styles dictionary
        insights_data: Dict containing:
            - detailed_insights: List of {parameter, status, insight, severity, ...}
            - summary: Optional summary stats
    """
    elements = []
    
    # Page header
    elements.append(Paragraph("<b>Insights & Observations</b>", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLORS['primary'], spaceAfter=20))
    
    # Extract insights from data
    detailed_insights = []
    if insights_data and isinstance(insights_data, dict):
        detailed_insights = insights_data.get('detailed_insights', [])
    
    if not detailed_insights or len(detailed_insights) == 0:
        # No abnormalities - show positive message
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "<i>No significant variations detected in analyzed parameters. All values within expected ranges.</i>",
            ParagraphStyle(
                'NoInsights',
                alignment=TA_CENTER,
                textColor=COLORS['slate_400'],
                fontSize=11,
                fontName='Helvetica-Oblique'
            )
        ))
        elements.append(Spacer(1, 30))
    else:
        # Display up to 5 most important insights
        max_insights = min(5, len(detailed_insights))
        
        for idx, insight in enumerate(detailed_insights[:max_insights]):
            if not isinstance(insight, dict):
                continue
                
            parameter = insight.get('parameter', 'Unknown Parameter')
            insight_text = insight.get('insight', 'No insight available.')
            status = insight.get('status', 'Normal')
            severity = insight.get('severity', 'MEDIUM')
            confidence = insight.get('confidence_score', 60)
            
            # Create insight header
            header_style = ParagraphStyle(
                'InsightHeader',
                fontName='Helvetica-Bold',
                fontSize=10,
                textColor=COLORS['secondary'],
                spaceAfter=6
            )
            
            elements.append(Paragraph(
                f"<b>{parameter.upper()} - {status.upper()}</b>",
                header_style
            ))
            
            # Insight body text
            elements.append(Paragraph(insight_text, styles['Prose']))
            
            # Metadata footer
            metadata_style = ParagraphStyle(
                'InsightMeta',
                fontSize=7,
                textColor=COLORS['slate_400'],
                spaceAfter=10
            )
            
            elements.append(Paragraph(
                f"<font color='#64748b'>Severity: {severity} | Confidence: {confidence}%</font>",
                metadata_style
            ))
            
            # Add separator between insights (except last one)
            if idx < max_insights - 1:
                elements.append(HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=COLORS['slate_200'],
                    spaceBefore=10,
                    spaceAfter=10
                ))
        
        # If more than 5 insights, add note
        if len(detailed_insights) > 5:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f"<i>+ {len(detailed_insights) - 5} additional observations not shown. View full report online.</i>",
                ParagraphStyle(
                    'MoreInsights',
                    textColor=COLORS['slate_400'],
                    fontSize=8,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Oblique'
                )
            ))
    
    # Add disclaimer section (keep existing)
    elements.append(Spacer(1, 50))
    elements.append(Paragraph("<b>Institutional Medical Disclaimer</b>", ParagraphStyle('H4', fontSize=11)))
    elements.append(Paragraph(
        "The observations provided herein are generated by automated diagnostic systems and are intended for professional clinical review only. "
        "These insights are NOT to be considered as a final diagnosis, treatment protocol, or medical advice.",
        styles['Prose']
    ))
    
    elements.append(PageBreak())
    return elements

def create_disclaimer_page(styles, report_id, source_filename, user_info=None):
    elements = []
    
    # Header
    elements.append(Paragraph("CLINICAL ANALYSIS REPORT", 
                              ParagraphStyle('CTitle', fontName='Helvetica-Bold', fontSize=24)))
    elements.append(Paragraph("TRACEABILITY MONOGRAPH // FINAL RECORD",
                              ParagraphStyle('CSub', fontSize=9, textColor=COLORS['slate_500'], textTransform='uppercase')))
    elements.append(Spacer(1, 20))
    
    # Extract patient info or use defaults
    patient_name = 'N/A'
    patient_dob = 'N/A'
    gender = 'N/A'
    
    if user_info and isinstance(user_info, dict):
        patient_name = user_info.get('full_name', 'N/A')
        patient_dob = user_info.get('date_of_birth', 'N/A')
        gender = user_info.get('gender', 'N/A')
    
    # Info with actual user data
    from datetime import datetime
    now = datetime.now()
    
    info = [
        ["Patient Name", patient_name],
        ["Date of Birth", patient_dob],
        ["Gender", gender],
        ["Report Date", now.strftime("%b %d, %Y")],
        ["Reference ID", report_id]
    ]
    # layout as 4 cols
    # We use the previous safe flattened Table method (list of list of paragraphs? No, just list of paragraphs in a row)
    
    r1 = []
    for label, val in info:
        txt = f"<font size=7 color='#94a3b8'><b>{label.upper()}</b></font><br/><b>{val}</b>"
        r1.append(Paragraph(txt, styles['Normal']))
    
    t = Table([r1], colWidths=[1.5*inch, 1.3*inch, 0.9*inch, 1.4*inch, 1.4*inch])
    t.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 1, COLORS['primary']),
        ('LINEBELOW', (0,0), (-1,0), 1, COLORS['primary']),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 30))
    
    # Disclaimers
    # 01 | Legal
    elements.append(Paragraph("<b>01 | Legal Disclaimers & Limitations</b>", ParagraphStyle('DHead', fontName='Helvetica-Bold', fontSize=10)))
    elements.append(Spacer(1, 10))
    
    disclaimer_txt = """
    <b>1. NON-DIAGNOSTIC INFORMATION.</b> This report is generated for informational purposes only.
    <br/><br/>
    <b>2. AUTOMATED EXTRACTION.</b> Data extracted using LabFlow OCR/LLM pipeline v2.4.
    <br/><br/>
    <b>4. PRIVACY.</b> Contains PHI. Handle according to HIPAA.
    """
    elements.append(Paragraph(disclaimer_txt, ParagraphStyle('DText', fontSize=9, leading=12, alignment=TA_JUSTIFY, textColor=COLORS['secondary'])))
    
    elements.append(Spacer(1, 20))
    
    # Audit
    elements.append(Paragraph("<b>02 | Audit Metadata</b>", ParagraphStyle('DHead', fontName='Helvetica-Bold', fontSize=10)))
    elements.append(Spacer(1, 10))
    
    # Flattened Audit Grid
    # Row 1
    def aud(label, val):
        return f"<font size=7 color='#94a3b8'><b>{label.upper()}</b></font><br/><font size=9 fontName='Courier'>{val}</font>"
        
    ar1 = [Paragraph(aud("Global Session ID", "ses_8f92-a1b2"), styles['Normal']),
           Paragraph(aud("Data Source", "LabCorp_Integration"), styles['Normal'])]
    ar2 = [Paragraph(aud("Processing Node", "US-EAST-2"), styles['Normal']),
           Paragraph(aud("Timestamp", datetime.now().isoformat()), styles['Normal'])]
           
    at = Table([ar1, ar2], colWidths=[3*inch, 3*inch])
    at.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(at)
    
    return elements

# --- MAIN GENERATOR ---

class NumberedPageTemplate(object):
    def __init__(self, report_id):
        self.report_id = report_id
    
    def on_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(COLORS['slate_300'])
        canvas.drawString(10*mm, 10*mm, f"Report ID: {self.report_id}")
        canvas.drawRightString(200*mm, 10*mm, f"Page {doc.page}")
        canvas.restoreState()

def generate_pdf(analysis_data, insights_data, systems_impact=None, source_filename="report.pdf", user_info=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=20*mm)
    
    styles = get_styles()
    report_id = f"LFC-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now()
    
    story = []
    
    # 1. Cover
    story.extend(create_cover_page(styles, report_id, now))
    
    # 2. Exec Summary
    story.extend(create_exec_summary(styles, analysis_data, insights_data, user_info))
    
    # 3. Systems Impact
    story.extend(create_systems_impact(styles, systems_impact))
    
    # 4. Parameters
    story.extend(create_parameter_breakdown(styles, analysis_data))
    
    # 5. Insights
    story.extend(create_insights_page(styles, insights_data))
    
    # 6. Disclaimers
    story.extend(create_disclaimer_page(styles, report_id, source_filename, user_info))
    
    # Build
    # Setup page numbering
    template = NumberedPageTemplate(report_id)
    doc.build(story, onFirstPage=template.on_page, onLaterPages=template.on_page)
    
    buffer.seek(0)
    return buffer

def get_report_filename(report_id="REPORT"):
    return f"SmartLab_{report_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
