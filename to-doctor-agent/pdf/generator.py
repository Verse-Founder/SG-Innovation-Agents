"""
pdf/generator.py
PDF 报告生成 — 使用 ReportLab
"""
import os
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


def generate_pdf_report(report_data: dict, output_path: str = None) -> str:
    """生成 PDF 医疗报告"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        )
        from reportlab.lib import colors
    except ImportError:
        logger.warning("[PDF] ReportLab 未安装，跳过 PDF 生成")
        return ""

    # 输出路径
    if not output_path:
        os.makedirs(settings.PDF_OUTPUT_DIR, exist_ok=True)
        patient_id = report_data.get("report_metadata", {}).get("patient_id", "unknown")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            settings.PDF_OUTPUT_DIR, f"report_{patient_id}_{timestamp}.pdf"
        )

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    elements = []

    # ── 标题 ─────────────────────────────────────────────
    metadata = report_data.get("report_metadata", {})
    elements.append(Paragraph("Diabetes Health Report", styles["Title"]))
    elements.append(Paragraph(
        f"Patient: {metadata.get('patient_id', 'N/A')} | "
        f"Date: {metadata.get('generated_at', '')[:10]} | "
        f"Period: {metadata.get('data_period_days', 30)} days",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 10 * mm))

    # ── 数据完整性 ───────────────────────────────────────
    completeness = metadata.get("data_completeness", {})
    if not metadata.get("is_data_complete"):
        elements.append(Paragraph(
            "<b>Note:</b> Some data sections are incomplete. "
            "Report is generated based on available data.",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 5 * mm))

    # ── 血糖 ─────────────────────────────────────────────
    glucose = report_data.get("glucose_analysis", {})
    if glucose.get("status") == "analyzed":
        elements.append(Paragraph("Blood Glucose Summary", styles["Heading2"]))
        glucose_table_data = [
            ["Metric", "Value"],
            ["Average", f"{glucose.get('average', 'N/A')} mmol/L"],
            ["Max", f"{glucose.get('max', 'N/A')} mmol/L"],
            ["Min", f"{glucose.get('min', 'N/A')} mmol/L"],
            ["High Episodes", str(glucose.get("high_count", 0))],
            ["Low Episodes", str(glucose.get("low_count", 0))],
            ["Dawn Phenomenon", "Yes" if glucose.get("dawn_phenomenon") else "No"],
        ]
        t = Table(glucose_table_data, colWidths=[80 * mm, 80 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 8 * mm))

    # ── 肾功能 ───────────────────────────────────────────
    egfr = report_data.get("renal_function", {})
    if egfr.get("status") == "analyzed":
        elements.append(Paragraph("Renal Function", styles["Heading2"]))
        egfr_data = [
            ["Metric", "Value"],
            ["Latest eGFR", f"{egfr.get('latest', 'N/A')} mL/min/1.73m2"],
            ["CKD Stage", egfr.get("ckd_stage", "N/A")],
            ["Declining Trend", "Yes" if egfr.get("declining") else "No"],
        ]
        t = Table(egfr_data, colWidths=[80 * mm, 80 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 8 * mm))

    # ── 用药依从性 ───────────────────────────────────────
    med = report_data.get("medication_adherence", {})
    if med.get("status") == "analyzed":
        elements.append(Paragraph("Medication Adherence", styles["Heading2"]))
        elements.append(Paragraph(
            f"Current adherence rate: {med.get('latest_pct', 'N/A')}% "
            f"(average: {med.get('average_pct', 'N/A')}%, "
            f"trend: {med.get('trend', 'N/A')})",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 8 * mm))

    # ── 预约建议 ─────────────────────────────────────────
    appointments = report_data.get("appointment_suggestions", [])
    if appointments:
        elements.append(Paragraph("Appointment Recommendations", styles["Heading2"]))
        appt_data = [["Department", "Urgency", "Reason", "Suggested Date"]]
        for a in appointments:
            appt_data.append([
                a.get("department", ""),
                a.get("urgency", ""),
                a.get("reason", "")[:60] + "..." if len(a.get("reason", "")) > 60 else a.get("reason", ""),
                a.get("suggested_date", ""),
            ])
        t = Table(appt_data, colWidths=[35 * mm, 25 * mm, 75 * mm, 30 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(t)

    # 构建 PDF
    try:
        doc.build(elements)
        logger.info(f"[PDF] 报告已生成: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"[PDF] 生成失败: {e}")
        return ""
