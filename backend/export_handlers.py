"""
Export Handlers for Multiple Formats
Supports PDF, Excel, CSV, and HL7 FHIR exports
"""

import io
import csv
import json
import qrcode
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ============================================================================
# Excel Export Handler
# ============================================================================

def export_to_excel(analysis_data: Dict, insights_data: Dict, systems_impact: Dict, 
                    user_info: Dict = None, source_filename: str = "report") -> io.BytesIO:
    """
    Export lab report to Excel format with multiple sheets
    
    Args:
        analysis_data: Parameter data in format {param_name: {value, unit, status, ...}}
        insights_data: Insights and recommendations
        systems_impact: Systems health data
        user_info: Patient demographics
        source_filename: Original report filename
        
    Returns:
        BytesIO buffer containing Excel file
    """
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create sheets
    _create_summary_sheet(wb, analysis_data, insights_data, user_info)
    _create_parameters_sheet(wb, analysis_data)
    _create_systems_sheet(wb, systems_impact)
    _create_insights_sheet(wb, insights_data)
    
    # Save to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer


def _create_summary_sheet(wb: Workbook, analysis_data: Dict, insights_data: Dict, user_info: Dict):
    """Create executive summary sheet"""
    ws = wb.create_sheet("Summary", 0)
    
    # Title
    ws['A1'] = "Lab Report Analysis Summary"
    ws['A1'].font = Font(size=16, bold=True, color="FFFFFF")
    ws['A1'].fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    ws['A1'].alignment = Alignment(horizontal="center")
    ws.merge_cells('A1:E1')
    
    # Patient Info
    row = 3
    if user_info:
        ws[f'A{row}'] = "Patient Information"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        ws[f'A{row}'] = "Name:"
        ws[f'B{row}'] = user_info.get('full_name', 'N/A')
        row += 1
        
        ws[f'A{row}'] = "Date of Birth:"
        ws[f'B{row}'] = user_info.get('date_of_birth', 'N/A')
        row += 1
        
        ws[f'A{row}'] = "Gender:"
        ws[f'B{row}'] = user_info.get('gender', 'N/A')
        row += 2
    
    # Summary Stats
    ws[f'A{row}'] = "Analysis Overview"
    ws[f'A{row}'].font = Font(bold=True, size=12)
    row += 1
    
    total = len(analysis_data)
    abnormal = sum(1 for p in analysis_data.values() if isinstance(p, dict) and p.get('status') in ['High', 'Low', 'Critical'])
    normal = total - abnormal
    
    ws[f'A{row}'] = "Total Parameters:"
    ws[f'B{row}'] = total
    row += 1
    
    ws[f'A{row}'] = "Normal:"
    ws[f'B{row}'] = normal
    ws[f'B{row}'].fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    row += 1
    
    ws[f'A{row}'] = "Abnormal:"
    ws[f'B{row}'] = abnormal
    ws[f'B{row}'].fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    row += 1
    
    # Report Date
    ws[f'A{row+1}'] = "Generated:"
    ws[f'B{row+1}'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 30


def _create_parameters_sheet(wb: Workbook, analysis_data: Dict):
    """Create detailed parameters sheet"""
    ws = wb.create_sheet("Parameters")
    
    # Headers
    headers = ['Parameter', 'Value', 'Unit', 'Reference Range', 'Status', 'Notes']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(1, col, header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    row = 2
    for param_name, data in analysis_data.items():
        if not isinstance(data, dict):
            continue
            
        ws.cell(row, 1, param_name)
        ws.cell(row, 2, str(data.get('value', '')))
        ws.cell(row, 3, data.get('unit', ''))
        ws.cell(row, 4, data.get('range', ''))
        
        status = data.get('status', 'Unknown')
        status_cell = ws.cell(row, 5, status)
        
        # Color code status
        if status == 'Critical':
            status_cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
            status_cell.font = Font(color="991B1B", bold=True)
        elif status in ['High', 'Low']:
            status_cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
            status_cell.font = Font(color="92400E")
        else:
            status_cell.fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
            status_cell.font = Font(color="065F46")
        
        notes = data.get('notes', [])
        ws.cell(row, 6, '; '.join(notes) if isinstance(notes, list) else str(notes))
        
        row += 1
    
    # Auto-adjust columns
    for col in range(1, 7):
        ws.column_dimensions[get_column_letter(col)].width = 20


def _create_systems_sheet(wb: Workbook, systems_impact: Dict):
    """Create systems impact sheet"""
    ws = wb.create_sheet("Systems Impact")
    
    # Headers
    headers = ['System', 'Health Score', 'Status', 'Abnormal Count', 'Total Count', 'Affected Parameters']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(1, col, header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    row = 2
    for system_name, data in systems_impact.items():
        ws.cell(row, 1, system_name)
        
        health_score = data.get('health_score', 100)
        ws.cell(row, 2, health_score)
        ws.cell(row, 3, data.get('status', 'Unknown'))
        ws.cell(row, 4, data.get('abnormal_count', 0))
        ws.cell(row, 5, data.get('total_count', 0))
        
        abnormal_params = data.get('abnormal_parameters', [])
        params_str = ', '.join([p.get('name', '') for p in abnormal_params])
        ws.cell(row, 6, params_str)
        
        row += 1
    
    # Auto-adjust columns
    for col in range(1, 7):
        ws.column_dimensions[get_column_letter(col)].width = 20


def _create_insights_sheet(wb: Workbook, insights_data: Dict):
    """Create insights sheet"""
    ws = wb.create_sheet("Insights")
    
    # Headers
    ws['A1'] = "Parameter"
    ws['B1'] = "Insight"
    ws['C1'] = "Severity"
    
    for col in range(1, 4):
        cell = ws.cell(1, col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")
    
    # Data
    detailed_insights = insights_data.get('detailed_insights', [])
    row = 2
    
    for insight in detailed_insights:
        ws.cell(row, 1, insight.get('parameter', ''))
        ws.cell(row, 2, insight.get('insight', ''))
        ws.cell(row, 3, insight.get('severity_label', ''))
        row += 1
    
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 60
    ws.column_dimensions['C'].width = 20


# ============================================================================
# CSV Export Handler
# ============================================================================

def export_to_csv(analysis_data: Dict, user_info: Dict = None) -> io.StringIO:
    """
    Export lab parameters to CSV format
    
    Args:
        analysis_data: Parameter data
        user_info: Patient demographics
        
    Returns:
        StringIO buffer containing CSV data
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Patient info header
    if user_info:
        writer.writerow(['Patient Information'])
        writer.writerow(['Name', user_info.get('full_name', 'N/A')])
        writer.writerow(['Date of Birth', user_info.get('date_of_birth', 'N/A')])
        writer.writerow(['Gender', user_info.get('gender', 'N/A')])
        writer.writerow([])
    
    # Report metadata
    writer.writerow(['Report Generated', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    
    # Parameters table
    writer.writerow(['Parameter', 'Value', 'Unit', 'Reference Range', 'Status', 'Notes'])
    
    for param_name, data in analysis_data.items():
        if not isinstance(data, dict):
            continue
        
        notes = data.get('notes', [])
        notes_str = '; '.join(notes) if isinstance(notes, list) else str(notes)
        
        writer.writerow([
            param_name,
            str(data.get('value', '')),
            data.get('unit', ''),
            data.get('range', ''),
            data.get('status', ''),
            notes_str
        ])
    
    buffer.seek(0)
    return buffer


# ============================================================================
# HL7 FHIR Export Handler
# ============================================================================

def export_to_hl7_fhir(analysis_data: Dict, user_info: Dict = None, source_filename: str = "report") -> dict:
    """
    Export lab report to HL7 FHIR format (simplified)
    
    Args:
        analysis_data: Parameter data
        user_info: Patient demographics
        source_filename: Original filename
        
    Returns:
        FHIR-compliant JSON structure
    """
    
    # Create FHIR DiagnosticReport resource
    report = {
        "resourceType": "DiagnosticReport",
        "id": f"lab-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                "code": "LAB",
                "display": "Laboratory"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "11502-2",
                "display": "Laboratory report"
            }],
            "text": "Lab Report Analysis"
        },
        "issued": datetime.now().isoformat(),
        "result": []
    }
    
    # Add patient info if available
    if user_info:
        report["subject"] = {
            "display": user_info.get('full_name', 'Patient'),
            "type": "Patient"
        }
    
    # Convert parameters to FHIR Observation resources
    for param_name, data in analysis_data.items():
        if not isinstance(data, dict):
            continue
        
        observation = {
            "resourceType": "Observation",
            "id": f"obs-{param_name.lower().replace(' ', '-')}",
            "status": "final",
            "code": {
                "text": param_name
            },
            "valueQuantity": {
                "value": data.get('value'),
                "unit": data.get('unit', '')
            },
            "interpretation": [{
                "coding": [{
                    "code": data.get('status', 'normal').lower(),
                    "display": data.get('status', 'Normal')
                }]
            }]
        }
        
        # Add reference range if available
        range_str = data.get('range', '')
        if range_str:
            observation["referenceRange"] = [{
                "text": range_str
            }]
        
        report["result"].append({
            "reference": f"#obs-{param_name.lower().replace(' ', '-')}",
            "display": param_name
        })
    
    return report


# ============================================================================
# QR Code Generator
# ============================================================================

def generate_qr_code(url: str, size: int = 10) -> io.BytesIO:
    """
    Generate QR code for shareable report URL
    
    Args:
        url: URL to encode
        size: QR code box size
        
    Returns:
        BytesIO buffer containing PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer


# ============================================================================
# Utility Functions
# ============================================================================

def get_export_filename(format_type: str, prefix: str = "lab_report") -> str:
    """
    Generate filename for export
    
    Args:
        format_type: 'excel', 'csv', 'hl7', 'pdf'
        prefix: Filename prefix
        
    Returns:
        Formatted filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extensions = {
        'excel': 'xlsx',
        'csv': 'csv',
        'hl7': 'json',
        'pdf': 'pdf'
    }
    
    ext = extensions.get(format_type, 'bin')
    return f"{prefix}_{timestamp}.{ext}"
