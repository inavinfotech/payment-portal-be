import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def export_to_csv(data: list[dict]) -> BytesIO:
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

def export_to_excel(data: list[dict]) -> BytesIO:
    df = pd.DataFrame(data)
    output = BytesIO()
    # Use context manager to save to BytesIO
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Payments')
    output.seek(0)
    return output

def export_to_pdf(data: list[dict]) -> BytesIO:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Payment History", styles['Title']))
    
    if not data:
        elements.append(Paragraph("No data available", styles['Normal']))
        doc.build(elements)
        output.seek(0)
        return output

    # Prepare data for table
    # Get headers from the first dictionary
    headers = list(data[0].keys())
    table_data = [headers]
    
    for row in data:
        table_data.append([str(row.get(h, "")) for h in headers])

    # Create table
    table = Table(table_data)
    
    # Add style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Reduce font size to fit more columns
    ])
    table.setStyle(style)
    
    elements.append(table)
    doc.build(elements)
    output.seek(0)
    return output
