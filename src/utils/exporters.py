"""
Multi-Format Data Exporter Utility (Excel, PDF, PNG Image, CSV)
"""
import io
import pandas as pd

def export_excel(df: pd.DataFrame, filename: str) -> bytes:
    """Export DataFrame to Excel (.xlsx) format bytes."""
    towrite = io.BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    return towrite.getvalue()

def export_pdf(df: pd.DataFrame, title: str) -> bytes:
    """Export DataFrame to styled PDF report bytes."""
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=15,
        textColor=colors.HexColor("#3B82F6")
    )
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))

    if df.empty:
        story.append(Paragraph("No records found matching the specified query or filter criteria.", styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    # Limit to 500 rows to avoid massive page size
    preview_df = df.head(500)
    data = [list(preview_df.columns)]
    for _, row in preview_df.iterrows():
        data.append([str(val) for val in row.values])

    col_width = (792 - 40) / max(1, len(preview_df.columns))
    t = Table(data, colWidths=[col_width]*len(preview_df.columns))
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#111827")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 7),
    ]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def export_image(df: pd.DataFrame, title: str) -> bytes:
    """Export DataFrame to rendered Table PNG image bytes."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if df.empty:
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.axis('off')
        ax.text(0.5, 0.5, "No records matching search or filter criteria.",
                horizontalalignment='center', verticalalignment='center',
                fontsize=12, color='#4B5563', weight='bold')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    # Render top 50 rows in image for readability
    preview_df = df.head(50)
    fig, ax = plt.subplots(figsize=(14, max(2.5, len(preview_df) * 0.3 + 1.5)))
    ax.axis('tight')
    ax.axis('off')

    table = ax.table(
        cellText=preview_df.values,
        colLabels=preview_df.columns,
        loc='center',
        cellLoc='left'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.3)

    for (row_idx, col_idx), cell in table.get_celld().items():
        if row_idx == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#111827')
        else:
            cell.set_facecolor('#f8fafc' if row_idx % 2 == 0 else '#ffffff')

    plt.title(f"{title} (Showing top {len(preview_df)} records)", fontsize=14, color='#111827', weight='bold', pad=20)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
