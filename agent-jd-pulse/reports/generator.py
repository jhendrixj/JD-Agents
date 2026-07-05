from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os


# ─────────────────────────────────────────
# BRAND COLOURS — JD Agent Suite
# ─────────────────────────────────────────

INDIGO = HexColor("#4B0082")      # Suite mark
TEAL = HexColor("#008080")        # Agent JD: Pulse
WHITE = HexColor("#FFFFFF")
LIGHT_GREY = HexColor("#F5F5F5")
DARK_GREY = HexColor("#333333")
MID_GREY = HexColor("#777777")
ACCENT = HexColor("#00CED1")      # Teal accent


# ─────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────

def get_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        fontSize=28,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        fontSize=13,
        textColor=ACCENT,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=4
    )

    generated_style = ParagraphStyle(
        "Generated",
        fontSize=9,
        textColor=WHITE,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=0
    )

    section_header_style = ParagraphStyle(
        "SectionHeader",
        fontSize=14,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceBefore=16,
        spaceAfter=8,
        leftIndent=10
    )

    body_style = ParagraphStyle(
        "Body",
        fontSize=10,
        textColor=DARK_GREY,
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=6,
        leading=16
    )

    label_style = ParagraphStyle(
        "Label",
        fontSize=9,
        textColor=MID_GREY,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=2
    )

    value_style = ParagraphStyle(
        "Value",
        fontSize=11,
        textColor=DARK_GREY,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=6
    )

    recommendation_style = ParagraphStyle(
        "Recommendation",
        fontSize=10,
        textColor=DARK_GREY,
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=4,
        leftIndent=12,
        leading=16
    )

    footer_style = ParagraphStyle(
        "Footer",
        fontSize=8,
        textColor=MID_GREY,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceBefore=10
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "generated": generated_style,
        "section_header": section_header_style,
        "body": body_style,
        "label": label_style,
        "value": value_style,
        "recommendation": recommendation_style,
        "footer": footer_style
    }


# ─────────────────────────────────────────
# SECTION HEADER BLOCK
# ─────────────────────────────────────────

def section_header(title: str, styles: dict):
    """Creates a teal section header bar."""
    header_data = [[Paragraph(f"  {title}", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[7 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [TEAL]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return header_table


# ─────────────────────────────────────────
# METRIC CARD ROW
# ─────────────────────────────────────────

def metric_row(metrics: list, styles: dict):
    """
    Creates a row of metric cards.
    metrics = [{"label": "...", "value": "..."}, ...]
    """
    cell_data = []
    for m in metrics:
        cell = [
            Paragraph(m["label"], styles["label"]),
            Paragraph(m["value"], styles["value"])
        ]
        cell_data.append(cell)

    col_width = 7 * inch / len(metrics)
    table = Table([cell_data], colWidths=[col_width] * len(metrics))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINEAFTER", (0, 0), (-2, -1), 1, WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


# ─────────────────────────────────────────
# REPORT GENERATOR
# ─────────────────────────────────────────

def generate_report(analytics_results: dict, output_dir: str = "reports/output"):
    """
    Generates a professional PDF report for Agent JD: Pulse.
    Takes the full analytics results dict and saves a PDF.
    Returns the file path of the generated report.
    """

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    artist_name = analytics_results.get("artist", "Unknown Artist")
    generated_at = analytics_results.get("generated_at", "")

    # Clean filename
    safe_name = artist_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_Pulse_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    filepath = os.path.join(output_dir, filename)

    # Document setup
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.75 * inch
    )

    styles = get_styles()
    elements = []

    # ── COVER HEADER ──
    header_data = [
        [Paragraph("AGENT JD: PULSE", styles["title"])],
        [Paragraph("Music Intelligence Report", styles["subtitle"])],
        [Paragraph(f"Prepared for: {artist_name}", styles["subtitle"])],
        [Paragraph(f"Generated: {generated_at}", styles["generated"])],
    ]
    header_table = Table(header_data, colWidths=[7 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INDIGO),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3 * inch))

    # ── SECTION 1: AUDIENCE ANALYSIS ──
    audience = analytics_results.get("audience_analysis", {})
    elements.append(section_header("01  Audience Analysis", styles))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(metric_row([
        {"label": "TOTAL ESTIMATED AUDIENCE",
            "value": audience.get("total_estimated_audience", "N/A")},
        {"label": "ENGAGEMENT SCORE",
            "value": str(audience.get("engagement_score", "N/A"))},
        {"label": "PRIMARY GENRE",
            "value": audience.get("primary_genre", "N/A")},
    ], styles))
    elements.append(Spacer(1, 0.15 * inch))

    # Audience segments table
    segments = audience.get("segments", [])
    if segments:
        seg_data = [["SEGMENT", "ESTIMATED SIZE", "PLATFORM", "ENGAGEMENT"]]
        for seg in segments:
            seg_data.append([
                Paragraph(seg.get("segment", ""), styles["body"]),
                Paragraph(seg.get("estimated_size", ""), styles["body"]),
                Paragraph(seg.get("platform", ""), styles["body"]),
                Paragraph(seg.get("engagement", ""), styles["body"]),
            ])

        seg_table = Table(seg_data, colWidths=[
                          2.2*inch, 1.5*inch, 1.8*inch, 1.5*inch])
        seg_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(seg_table)

    elements.append(Spacer(1, 0.2 * inch))

    # ── SECTION 2: RELEASE TIMING ──
    timing = analytics_results.get("release_timing", {})
    elements.append(section_header("02  Release Timing Analysis", styles))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(metric_row([
        {"label": "MOST ACTIVE MONTH",
            "value": timing.get("most_active_month", "N/A")},
        {"label": "MOST ACTIVE QUARTER",
            "value": timing.get("most_active_quarter", "N/A")},
        {"label": "AVG RELEASE GAP",
            "value": f"{timing.get('average_release_gap_months', 0)} months"},
        {"label": "RECOMMENDED WINDOW",
            "value": timing.get("recommended_next_window", "N/A")},
    ], styles))
    elements.append(Spacer(1, 0.15 * inch))

    # Recommendations
    recommendations = timing.get("recommendations", [])
    if recommendations:
        elements.append(
            Paragraph("Strategic Recommendations:", styles["label"]))
        elements.append(Spacer(1, 0.05 * inch))
        for i, rec in enumerate(recommendations, 1):
            elements.append(
                Paragraph(f"{i}.  {rec}", styles["recommendation"]))
        elements.append(Spacer(1, 0.1 * inch))

    # Release history table
    history = timing.get("release_history", [])
    if history:
        elements.append(Paragraph("Release History:", styles["label"]))
        elements.append(Spacer(1, 0.05 * inch))
        hist_data = [["TITLE", "DATE", "TYPE"]]
        for item in history:
            hist_data.append([
                Paragraph(item.get("name", ""), styles["body"]),
                Paragraph(item.get("date", ""), styles["body"]),
                Paragraph(item.get("type", "").title(), styles["body"]),
            ])

        hist_table = Table(hist_data, colWidths=[4*inch, 1.5*inch, 1.5*inch])
        hist_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(hist_table)

    elements.append(Spacer(1, 0.2 * inch))

    # ── SECTION 3: REVENUE ANALYSIS ──
    revenue = analytics_results.get("revenue_analysis", {})
    elements.append(section_header("03  Revenue Analysis", styles))
    elements.append(Spacer(1, 0.1 * inch))

    # Revenue opportunities
    opportunities = revenue.get("revenue_opportunities", [])
    if opportunities:
        elements.append(
            Paragraph("Current Revenue Streams:", styles["label"]))
        elements.append(Spacer(1, 0.05 * inch))
        opp_data = [["REVENUE STREAM", "EST. MONTHLY REVENUE", "BASIS"]]
        for opp in opportunities:
            opp_data.append([
                Paragraph(opp.get("stream", ""), styles["body"]),
                Paragraph(opp.get(
                    "estimated_monthly_revenue", ""), styles["body"]),
                Paragraph(opp.get("basis", ""), styles["body"]),
            ])

        opp_table = Table(
            opp_data, colWidths=[1.8*inch, 1.8*inch, 3.4*inch])
        opp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(opp_table)
        elements.append(Spacer(1, 0.15 * inch))

    # Revenue gaps
    gaps = revenue.get("identified_gaps", [])
    if gaps:
        elements.append(
            Paragraph("Identified Revenue Gaps:", styles["label"]))
        elements.append(Spacer(1, 0.05 * inch))
        gap_data = [["GAP", "INSIGHT", "POTENTIAL IMPACT"]]
        for gap in gaps:
            gap_data.append([
                Paragraph(gap.get("gap", ""), styles["body"]),
                Paragraph(gap.get("recommendation", ""), styles["body"]),
                Paragraph(gap.get("potential_impact", ""), styles["body"]),
            ])

        gap_table = Table(
            gap_data, colWidths=[1.5*inch, 4*inch, 1.5*inch])
        gap_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(gap_table)

    elements.append(Spacer(1, 0.2 * inch))

    # ── SECTION 4: COMPETITIVE BENCHMARK ──
    benchmark = analytics_results.get("competitive_benchmark", {})
    elements.append(section_header("04  Competitive Benchmark", styles))
    elements.append(Spacer(1, 0.1 * inch))

    if "peer_comparison" in benchmark:
        bench_data = [["PEER ARTIST", "FOLLOWERS",
                        "POPULARITY", "FOLLOWER DIFF", "POSITION"]]
        for peer in benchmark.get("peer_comparison", []):
            bench_data.append([
                Paragraph(peer.get("peer_name", ""), styles["body"]),
                Paragraph(peer.get("peer_followers", ""), styles["body"]),
                Paragraph(str(peer.get("peer_popularity", "")), styles["body"]),
                Paragraph(peer.get("follower_difference", ""), styles["body"]),
                Paragraph(peer.get("position", "").title(), styles["body"]),
            ])

        bench_table = Table(bench_data, colWidths=[
                            1.8*inch, 1.2*inch, 1.2*inch, 1.5*inch, 1.3*inch])
        bench_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(bench_table)
    else:
        elements.append(Paragraph(
            benchmark.get("message",
                          "Benchmarking data not available."),
            styles["body"]
        ))

    elements.append(Spacer(1, 0.3 * inch))

    # ── FOOTER ──
    elements.append(HRFlowable(
        width="100%", thickness=1, color=TEAL))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "Generated by Agent JD: Pulse  |  The JD Agent Suite  |  Powered by The JD Consultancy",
        styles["footer"]
    ))
    elements.append(Paragraph(
        "This report is confidential and intended solely for the named artist.",
        styles["footer"]
    ))

    # Build PDF
    doc.build(elements)
    print(f"\nReport generated: {filepath}")
    return filepath


# ─────────────────────────────────────────
# TEST — Run this file directly to test
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.ingest import get_full_artist_profile
    from models.analytics import run_full_analytics

    artist = input("Enter an artist name to generate a report: ")
    print(f"\nFetching data for {artist}...")
    profile = get_full_artist_profile(artist)

    print("Running analytics...")
    results = run_full_analytics(profile)

    print("Generating PDF report...")
    filepath = generate_report(results)

    print(f"\nDone! Open your report at: {filepath}")