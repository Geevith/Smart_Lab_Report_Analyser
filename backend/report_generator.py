import os
import io
import uuid
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Flowable, HRFlowable, CondPageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

# --- CONSTANTS & CONFIG ---
REPORT_VERSION = "5.0.0"
CLINIC_NAME = "Central Reference Laboratory"
CLINIC_ADDRESS = "123 Medical Plaza, Suite 400 | City, ST 12345"
CLINIC_CONTACT = "Ph: (555) 123-4567 | Fax: (555) 123-4568 | www.centralreflab.com"

# Clinical Color Palette
COLORS = {
    'navy': colors.HexColor('#1a365d'),       # Deep blue for headers/borders
    'text': colors.HexColor('#333333'),       # Dark gray for regular text
    'gray_light': colors.HexColor('#f3f4f6'), # Light gray for alternating rows
    'gray_border': colors.HexColor('#e5e7eb'),# Border gray
    'gray_dark': colors.HexColor('#4b5563'),  # Subheadings
    'red_critical': colors.HexColor('#dc2626'),# Red for High/Critical
    'blue_low': colors.HexColor('#2563eb'),   # Blue for Low
    'green_normal': colors.HexColor('#15803d'),# Green for Normal
    'white': colors.white,
}

# --- STYLES ---

def get_clinical_styles():
    styles = getSampleStyleSheet()
    
    # Base Document Style
    styles.add(ParagraphStyle(name='Clinical_Normal', fontName='Helvetica', fontSize=9, textColor=COLORS['text'], leading=12))
    styles.add(ParagraphStyle(name='Clinical_Bold', fontName='Helvetica-Bold', fontSize=9, textColor=COLORS['text'], leading=12))
    
    # Headers
    styles.add(ParagraphStyle(name='Section_Header', fontName='Helvetica-Bold', fontSize=12, textColor=COLORS['navy'], spaceAfter=6, spaceBefore=12))
    styles.add(ParagraphStyle(name='Sub_Header', fontName='Helvetica-Bold', fontSize=10, textColor=COLORS['gray_dark'], spaceAfter=4))
    
    # Demographics
    styles.add(ParagraphStyle(name='Demo_Label', fontName='Helvetica-Bold', fontSize=8, textColor=COLORS['gray_dark']))
    styles.add(ParagraphStyle(name='Demo_Value', fontName='Helvetica', fontSize=9, textColor=COLORS['text']))
    
    # Table Grid
    styles.add(ParagraphStyle(name='TH', fontName='Helvetica-Bold', fontSize=9, textColor=COLORS['white'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='TD', fontName='Helvetica', fontSize=9, textColor=COLORS['text'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='TD_Left', fontName='Helvetica', fontSize=9, textColor=COLORS['text'], alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='TD_Flag_H', fontName='Helvetica-Bold', fontSize=9, textColor=COLORS['red_critical'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='TD_Flag_L', fontName='Helvetica-Bold', fontSize=9, textColor=COLORS['blue_low'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='TD_Flag_C', fontName='Helvetica-Bold', fontSize=9, textColor=COLORS['red_critical'], alignment=TA_CENTER, backColor=colors.HexColor('#fee2e2')))
    
    # Physician Notes
    styles.add(ParagraphStyle(name='Note_Text', fontName='Times-Roman', fontSize=10, leading=14, textColor=COLORS['text'], alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='Note_Item_Title', fontName='Helvetica-Bold', fontSize=10, textColor=COLORS['navy'], spaceBefore=8, spaceAfter=2))
    styles.add(ParagraphStyle(name='Note_Item_Text', fontName='Times-Roman', fontSize=10, leading=14, textColor=COLORS['text'], leftIndent=10))

    return styles

# --- HELPER PARSERS ---

def parse_reference_range(range_str):
    if not range_str: return None, None
    match = re.search(r'([\d.]+)\s*[-–]\s*([\d.]+)', range_str)
    if match:
        try: return float(match.group(1)), float(match.group(2))
        except: return None, None
    return None, None

def _get_system_for_param(param_name):
    try:
        from backend.systems_impact import SYSTEM_GROUPINGS
        for system, params in SYSTEM_GROUPINGS.items():
            if param_name in params: return system
    except: pass
    return "General"

# --- PAGE LAYOUT TEMPLATE ---

class ClinicalPageTemplate(object):
    def __init__(self, report_id, user_info, now):
        self.report_id = report_id
        self.user_info = user_info or {}
        self.now = now
        
    def draw_header(self, canvas, doc):
        canvas.saveState()
        # Top Header line
        canvas.setStrokeColor(COLORS['navy'])
        canvas.setLineWidth(2)
        canvas.line(doc.leftMargin, A4[1] - 40, A4[0] - doc.rightMargin, A4[1] - 40)
        
        # Clinic Info (Left)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(COLORS['navy'])
        canvas.drawString(doc.leftMargin, A4[1] - 30, CLINIC_NAME)
        
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLORS['gray_dark'])
        canvas.drawString(doc.leftMargin, A4[1] - 42, CLINIC_ADDRESS)
        canvas.drawString(doc.leftMargin, A4[1] - 52, CLINIC_CONTACT)
        
        # Report Title (Right)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.setFillColor(COLORS['navy'])
        canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 30, "LABORATORY REPORT")
        
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(COLORS['text'])
        canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 44, f"Accession / Report ID: {self.report_id}")
        canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 56, f"Report Date: {self.now.strftime('%b %d, %Y %H:%M')}")
        
        canvas.restoreState()

    def draw_footer(self, canvas, doc):
        canvas.saveState()
        # Bottom Footer line
        canvas.setStrokeColor(COLORS['navy'])
        canvas.setLineWidth(1)
        canvas.line(doc.leftMargin, 50, A4[0] - doc.rightMargin, 50)
        
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLORS['gray_dark'])
        disclaimer = "This report is generated for clinical review. Pathologist validation is required before interpreting the diagnostic findings."
        canvas.drawString(doc.leftMargin, 38, disclaimer)
        
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawRightString(A4[0] - doc.rightMargin, 38, f"Page {doc.page}")
        canvas.restoreState()

    def on_page(self, canvas, doc):
        self.draw_header(canvas, doc)
        self.draw_footer(canvas, doc)


# --- GENERATORS ---

def create_demographics_block(styles, user_info, now, report_id):
    patient_name = user_info.get('full_name', 'UNKNOWN PATIENT').upper() if user_info else 'UNKNOWN PATIENT'
    dob = user_info.get('date_of_birth', 'Not Provided') if user_info else 'Not Provided'
    gender = user_info.get('gender', 'Not Provided') if user_info else 'Not Provided'
    patient_id = user_info.get('id', 'N/A')[:8] if user_info and 'id' in user_info else 'N/A'
    
    # Constructing a clean demographics box
    data = [
        [Paragraph(f"<b>PATIENT NAME:</b> {patient_name}", styles['Clinical_Normal']),
         Paragraph(f"<b>MRN / PATIENT ID:</b> {patient_id}", styles['Clinical_Normal']),
         Paragraph(f"<b>COLLECTED:</b> {now.strftime('%b %d, %Y')}", styles['Clinical_Normal'])],
         
        [Paragraph(f"<b>DOB / AGE:</b> {dob}", styles['Clinical_Normal']),
         Paragraph(f"<b>GENDER:</b> {gender}", styles['Clinical_Normal']),
         Paragraph(f"<b>PROVIDER:</b> Referring Physician", styles['Clinical_Normal'])]
    ]
    
    table = Table(data, colWidths=[2.5*inch, 2.5*inch, 2.2*inch], rowHeights=[20, 20])
    table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, COLORS['navy']),
        ('BACKGROUND', (0,0), (-1,-1), COLORS['white']),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    
    # Spacer handles the header offset
    return [Spacer(1, 10), table, Spacer(1, 15)]

def create_results_table(styles, analysis_data):
    elements = []
    elements.append(Paragraph("Laboratory Results", styles['Section_Header']))
    
    headers = [
        Paragraph("Test Name", styles['TH']),
        Paragraph("Result", styles['TH']),
        Paragraph("Flag", styles['TH']),
        Paragraph("Units", styles['TH']),
        Paragraph("Reference Range", styles['TH']),
        Paragraph("System", styles['TH'])
    ]
    
    data = [headers]
    
    def status_priority(item):
        _, param_data = item
        if not isinstance(param_data, dict): return 999
        status = param_data.get('status', 'Normal')
        if status == 'Critical': return 0
        if status in ['High', 'Low']: return 1
        if status == 'Normal': return 2
        return 3
    
    sorted_params = sorted(analysis_data.items(), key=status_priority) if analysis_data else []
    
    row_shading = []
    
    for idx, (param_name, param_data) in enumerate(sorted_params):
        if not isinstance(param_data, dict): continue
        
        value = param_data.get('value', 'N/A')
        unit = param_data.get('unit', '')
        status = param_data.get('status', 'Normal')
        range_str = param_data.get('range', '')
        
        # Formatting Flags
        flag_p = ""
        if status == 'Critical':
            flag_p = Paragraph("<b>*CRIT*</b>", styles['TD_Flag_C'])
        elif status == 'High':
            flag_p = Paragraph("<b>H</b>", styles['TD_Flag_H'])
        elif status == 'Low':
            flag_p = Paragraph("<b>L</b>", styles['TD_Flag_L'])
        else:
            flag_p = Paragraph("", styles['TD'])
            
        # Value display
        if isinstance(value, (int, float)):
            val_str = f"{value:.2f}" if isinstance(value, float) else str(value)
        else:
            val_str = str(value)
            
        value_p = Paragraph(val_str, styles['TD'])
        if status != 'Normal':
            value_p = Paragraph(f"<b>{val_str}</b>", styles['TD_Flag_H'] if status == 'High' else (styles['TD_Flag_L'] if status == 'Low' else styles['TD_Flag_C']))
            
        row = [
            Paragraph(param_name, styles['TD_Left']),
            value_p,
            flag_p,
            Paragraph(unit, styles['TD']),
            Paragraph(range_str, styles['TD']),
            Paragraph(_get_system_for_param(param_name), styles['TD'])
        ]
        data.append(row)
        
        # Alternating row color
        if idx % 2 != 0:
            row_shading.append(('BACKGROUND', (0, idx+1), (-1, idx+1), COLORS['gray_light']))
            
    if len(data) == 1:
        data.append([Paragraph("No parameters analyzed", styles['TD_Left']), "", "", "", "", ""])
    
    col_widths = [2.2*inch, 0.8*inch, 0.7*inch, 0.8*inch, 1.4*inch, 1.3*inch]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), COLORS['navy']),
        ('TEXTCOLOR', (0,0), (-1,0), COLORS['white']),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, COLORS['gray_border']),
        ('BOX', (0,0), (-1,-1), 1, COLORS['navy']),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]
    t_style.extend(row_shading)
    t.setStyle(TableStyle(t_style))
    
    elements.append(t)
    return elements

def create_physician_notes(styles, insights_data, systems_impact):
    elements = []
    
    elements.append(CondPageBreak(2*inch))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Clinical Interpretations & Pathologist Notes", styles['Section_Header']))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLORS['navy'], spaceAfter=15))
    
    sys_impacts = []
    if systems_impact and isinstance(systems_impact, dict):
        for sys_name, sys_info in systems_impact.items():
            if isinstance(sys_info, dict) and sys_info.get('abnormal_count', 0) > 0:
                sys_impacts.append(f"{sys_name} ({sys_info.get('abnormal_count')} anomalies)")
                
    if sys_impacts:
        intro_text = f"Primary system anomalies detected in: {', '.join(sys_impacts)}. Clinical correlation is advised based on the following parameter deviations."
        elements.append(Paragraph(intro_text, styles['Note_Text']))
    else:
        elements.append(Paragraph("Systemic parameters appear to be within normal physiological ranges. No overt systemic anomalies detected in the analyzed panel.", styles['Note_Text']))
        
    elements.append(Spacer(1, 15))
    
    detailed_insights = insights_data.get('detailed_insights', []) if insights_data is not None and isinstance(insights_data, dict) else []
    
    if detailed_insights:
        elements.append(Paragraph("Specific Parameter Observations:", styles['Sub_Header']))
        for insight in detailed_insights[:10]:
            if not isinstance(insight, dict): continue
            
            param = insight.get('parameter', 'Unknown')
            status = insight.get('status', 'Abnormal')
            text = insight.get('insight', '')
            
            p_title = Paragraph(f"{param.upper()} | Flag: {status.upper()}", styles['Note_Item_Title'])
            p_text = Paragraph(text, styles['Note_Item_Text'])
            elements.append(KeepTogether([p_title, p_text]))
    else:
        elements.append(Paragraph("No specific abnormal parameter observations to report.", styles['Note_Item_Text']))
        
    elements.append(Spacer(1, 40))
    elements.append(HRFlowable(width="30%", thickness=1, color=COLORS['gray_dark'], hAlign='LEFT', spaceAfter=5))
    elements.append(Paragraph("<i>Electronically authenticated by Nexus Clinical Systems</i>", ParagraphStyle('Auth', fontName='Times-Italic', fontSize=9, textColor=COLORS['text'])))
    
    return elements

# --- MAIN GENERATOR POINT ---

def generate_pdf(analysis_data, insights_data, systems_impact=None, source_filename="report.pdf", user_info=None):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=0.5*inch, 
        leftMargin=0.5*inch, 
        topMargin=1.5*inch, 
        bottomMargin=1.0*inch
    )
    
    styles = get_clinical_styles()
    report_id = f"RLP-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now()
    
    story = []
    
    story.extend(create_demographics_block(styles, user_info, now, report_id))
    story.extend(create_results_table(styles, analysis_data))
    story.extend(create_physician_notes(styles, insights_data, systems_impact))
    
    template = ClinicalPageTemplate(report_id, user_info, now)
    doc.build(story, onFirstPage=template.on_page, onLaterPages=template.on_page)
    
    buffer.seek(0)
    return buffer

def get_report_filename(report_id="REPORT"):
    return f"ClinicalReport_{report_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
