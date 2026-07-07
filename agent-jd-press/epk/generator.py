from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os


# ─────────────────────────────────────────
# BRAND COLOURS — JD Agent Suite
# ─────────────────────────────────────────

INDIGO = HexColor("#4B0082")        # Suite mark
CORAL = HexColor("#FF6B6B")         # Agent JD: Press colour
WHITE = HexColor("#FFFFFF")
LIGHT_GREY = HexColor("#F5F5F5")
DARK_GREY = HexColor("#333333")
MID_GREY = HexColor("#777777")
ACCENT = HexColor("#FF8E8E")        # Coral accent


# ─────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────

def get_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "EPKTitle",
        fontSize=32,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "EPKSubtitle",
        fontSize=13,
        textColor=ACCENT,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=4
    )

    generated_style = ParagraphStyle(
        "EPKGenerated",
        fontSize=9,
        textColor=WHITE,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=0
    )

    section_header_style = ParagraphStyle(
        "EPKSectionHeader",
        fontSize=14,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceBefore=16,
        spaceAfter=8,
        leftIndent=10
    )

    body_style = ParagraphStyle(
        "EPKBody",
        fontSize=10,
        textColor=DARK_GREY,
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=6,
        leading=16
    )

    label_style = ParagraphStyle(
        "EPKLabel",
        fontSize=9,
        textColor=MID_GREY,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=2
    )

    value_style = ParagraphStyle(
        "EPKValue",
        fontSize=11,
        textColor=DARK_GREY,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=6
    )

    quote_style = ParagraphStyle(
        "EPKQuote",
        fontSize=13,
        textColor=CORAL,
        fontName="Helvetica-BoldOblique",
        alignment=TA_CENTER,
        spaceAfter=8,
        spaceBefore=8,
        leading=20
    )

    footer_style = ParagraphStyle(
        "EPKFooter",
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
        "quote": quote_style,
        "footer": footer_style
    }


# ─────────────────────────────────────────
# SECTION HEADER BLOCK
# ─────────────────────────────────────────

def section_header(title: str, styles: dict):
    header_data = [[Paragraph(f"  {title}", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[7 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CORAL),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return header_table


# ─────────────────────────────────────────
# BIO GENERATOR
# ─────────────────────────────────────────

def generate_bio(
    artist_name: str,
    genre: str,
    bio: str,
    achievements: str,
    pulse_data: dict
) -> str:
    """
    Generates a professional artist bio.
    Uses provided bio if available, otherwise
    constructs one from available data.
    """

    # If artist provided their own bio, polish it
    if bio and len(bio) > 50:
        return bio

    # Build bio from available data
    spotify = pulse_data.get("spotify", {})
    youtube = pulse_data.get("youtube", {})

    genres = spotify.get("profile", {}).get("genres", [])
    primary_genre = genres[0] if genres else genre if genre else "music"

    subscribers = youtube.get("channel", {}).get("subscribers", 0)
    total_views = youtube.get("channel", {}).get("total_views", 0)
    discography = spotify.get("discography", [])
    album_count = len([d for d in discography if d.get("type") == "album"])

    # Build bio paragraphs
    paragraphs = []

    # Opening
    if primary_genre:
        paragraphs.append(
            f"{artist_name} is a dynamic force in {primary_genre}, "
            f"delivering music that resonates across borders and generations."
        )
    else:
        paragraphs.append(
            f"{artist_name} is an independent artist whose music "
            f"resonates across borders and generations."
        )

    # Discography mention
    if album_count > 0:
        paragraphs.append(
            f"With {album_count} studio {'album' if album_count == 1 else 'albums'} "
            f"to their name, {artist_name} has demonstrated a consistent commitment "
            f"to artistic growth and creative excellence."
        )

    # YouTube presence
    if subscribers > 0:
        if subscribers >= 1000000:
            sub_str = f"{subscribers/1000000:.1f} million"
        elif subscribers >= 1000:
            sub_str = f"{int(subscribers/1000)}K"
        else:
            sub_str = str(subscribers)

        paragraphs.append(
            f"Their digital presence continues to grow, with {sub_str} subscribers "
            f"on YouTube and over {int(total_views):,} total views — "
            f"a testament to their expanding global audience."
        )

    # Achievements
    if achievements:
        paragraphs.append(achievements)

    # Closing
    paragraphs.append(
        f"{artist_name} continues to push boundaries, connecting with audiences "
        f"through authentic storytelling and undeniable artistry."
    )

    return " ".join(paragraphs)


# ─────────────────────────────────────────
# TALKING POINTS GENERATOR
# ─────────────────────────────────────────

def generate_talking_points(
    artist_name: str,
    genre: str,
    pulse_data: dict
) -> list:
    """
    Generates media talking points for press interviews.
    """

    spotify = pulse_data.get("spotify", {})
    youtube = pulse_data.get("youtube", {})
    discography = spotify.get("discography", [])
    genres = spotify.get("profile", {}).get("genres", [])
    primary_genre = genres[0] if genres else genre if genre else "music"

    talking_points = []

    # Talking point 1 — Origin and identity
    talking_points.append({
        "topic": "Origin & Identity",
        "point": f"Ask {artist_name} about their musical journey — "
                 f"how they discovered their sound and what drives their artistry."
    })

    # Talking point 2 — Genre and influences
    if primary_genre:
        talking_points.append({
            "topic": "Sound & Influences",
            "point": f"Explore {artist_name}'s relationship with {primary_genre} "
                     f"and the artists and experiences that shaped their musical identity."
        })

    # Talking point 3 — Discography
    if discography:
        latest = discography[0]
        talking_points.append({
            "topic": "Latest Release",
            "point": f"Discuss '{latest.get('name', 'their latest project')}' — "
                     f"the creative process, the message behind the music, "
                     f"and what listeners can expect."
        })

    # Talking point 4 — Digital presence
    subscribers = youtube.get("channel", {}).get("subscribers", 0)
    if subscribers > 0:
        talking_points.append({
            "topic": "Digital Community",
            "point": f"With a growing YouTube presence, ask {artist_name} "
                     f"about how they connect with fans online and the role "
                     f"of social media in their career."
        })

    # Talking point 5 — Future
    talking_points.append({
        "topic": "Vision & Future",
        "point": f"Ask {artist_name} about what's next — upcoming projects, "
                 f"collaborations, live performances, and their long-term vision "
                 f"for their career."
    })

    # Talking point 6 — African music scene
    talking_points.append({
        "topic": "African Music Globally",
        "point": f"Explore {artist_name}'s perspective on the rise of African "
                 f"music on the global stage and their role in that movement."
    })

    return talking_points


# ─────────────────────────────────────────
# EPK GENERATOR
# ─────────────────────────────────────────

def generate_epk(
    artist_name: str,
    genre: str = "",
    bio: str = "",
    achievements: str = "",
    social_links: dict = {},
    contact_email: str = "",
    pulse_data: dict = {},
    output_dir: str = "epk/output"
) -> str:
    """
    Generates a professional EPK PDF for an artist.
    Returns the file path of the generated EPK.
    """

    os.makedirs(output_dir, exist_ok=True)

    safe_name = artist_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_EPK_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    filepath = os.path.join(output_dir, filename)

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
        [Paragraph("ELECTRONIC PRESS KIT", styles["title"])],
        [Paragraph(artist_name.upper(), styles["subtitle"])],
        [Paragraph(
            f"Genre: {genre}" if genre else "Independent Artist",
            styles["subtitle"]
        )],
        [Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            styles["generated"]
        )],
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

    # ── SECTION 1: ARTIST BIO ──
    elements.append(section_header("01  Artist Biography", styles))
    elements.append(Spacer(1, 0.1 * inch))

    artist_bio = generate_bio(
        artist_name, genre, bio, achievements, pulse_data
    )
    elements.append(Paragraph(artist_bio, styles["body"]))
    elements.append(Spacer(1, 0.2 * inch))

    # ── SECTION 2: QUICK FACTS ──
    elements.append(section_header("02  Quick Facts", styles))
    elements.append(Spacer(1, 0.1 * inch))

    spotify = pulse_data.get("spotify", {})
    youtube = pulse_data.get("youtube", {})
    discography = spotify.get("discography", [])
    genres_list = spotify.get("profile", {}).get("genres", [])
    subscribers = youtube.get("channel", {}).get("subscribers", 0)
    total_views = youtube.get("channel", {}).get("total_views", 0)
    album_count = len([d for d in discography if d.get("type") == "album"])
    single_count = len([d for d in discography if d.get("type") == "single"])

    facts_data = []

    if genre or genres_list:
        facts_data.append(["Genre", genre or genres_list[0]])
    if album_count > 0:
        facts_data.append(["Albums Released", str(album_count)])
    if single_count > 0:
        facts_data.append(["Singles Released", str(single_count)])
    if subscribers > 0:
        facts_data.append([
            "YouTube Subscribers",
            f"{int(subscribers):,}"
        ])
    if total_views > 0:
        facts_data.append([
            "Total YouTube Views",
            f"{int(total_views):,}"
        ])
    if contact_email:
        facts_data.append(["Booking & Press", contact_email])

    if facts_data:
        facts_table = Table(facts_data, colWidths=[2.5*inch, 4.5*inch])
        facts_table.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GREY]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), CORAL),
            ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
        ]))
        elements.append(facts_table)

    elements.append(Spacer(1, 0.2 * inch))

    # ── SECTION 3: DISCOGRAPHY ──
    if discography:
        elements.append(section_header("03  Discography", styles))
        elements.append(Spacer(1, 0.1 * inch))

        disc_data = [["TITLE", "TYPE", "YEAR", "TRACKS"]]
        for item in discography[:10]:
            release_date = item.get("release_date", "")
            year = release_date[:4] if release_date else "N/A"
            disc_data.append([
                Paragraph(item.get("name", ""), styles["body"]),
                Paragraph(item.get("type", "").title(), styles["body"]),
                Paragraph(year, styles["body"]),
                Paragraph(str(item.get("total_tracks", "")), styles["body"]),
            ])

        disc_table = Table(
            disc_data,
            colWidths=[3.5*inch, 1.2*inch, 1*inch, 1.3*inch]
        )
        disc_table.setStyle(TableStyle([
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
        elements.append(disc_table)
        elements.append(Spacer(1, 0.2 * inch))

    # ── SECTION 4: MEDIA TALKING POINTS ──
    elements.append(section_header("04  Media Talking Points", styles))
    elements.append(Spacer(1, 0.1 * inch))

    talking_points = generate_talking_points(
        artist_name, genre, pulse_data
    )

    for i, tp in enumerate(talking_points, 1):
        topic_data = [[
            Paragraph(f"{i}. {tp['topic']}", styles["label"]),
        ]]
        topic_table = Table(topic_data, colWidths=[7*inch])
        topic_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(topic_table)
        elements.append(Paragraph(tp["point"], styles["body"]))
        elements.append(Spacer(1, 0.05 * inch))

    elements.append(Spacer(1, 0.2 * inch))

    # ── SECTION 5: SOCIAL LINKS ──
    if social_links:
        elements.append(section_header("05  Connect", styles))
        elements.append(Spacer(1, 0.1 * inch))

        social_data = []
        for platform, url in social_links.items():
            social_data.append([
                Paragraph(platform.title(), styles["label"]),
                Paragraph(url, styles["body"])
            ])

        if social_data:
            social_table = Table(
                social_data,
                colWidths=[2*inch, 5*inch]
            )
            social_table.setStyle(TableStyle([
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GREY]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), CORAL),
                ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
            ]))
            elements.append(social_table)
            elements.append(Spacer(1, 0.2 * inch))

    # ── SECTION 6: YOUTUBE HIGHLIGHTS ──
    recent_videos = youtube.get("recent_videos", [])
    if recent_videos:
        elements.append(section_header("06  Recent Releases", styles))
        elements.append(Spacer(1, 0.1 * inch))

        video_data = [["TITLE", "PUBLISHED", "LINK"]]
        for video in recent_videos[:5]:
            published = video.get("published_at", "")[:10]
            video_data.append([
                Paragraph(video.get("title", ""), styles["body"]),
                Paragraph(published, styles["body"]),
                Paragraph(video.get("video_url", ""), styles["body"]),
            ])

        video_table = Table(
            video_data,
            colWidths=[3*inch, 1.2*inch, 2.8*inch]
        )
        video_table.setStyle(TableStyle([
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
        elements.append(video_table)
        elements.append(Spacer(1, 0.2 * inch))

    # ── FOOTER ──
    elements.append(HRFlowable(width="100%", thickness=1, color=CORAL))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "Generated by Agent JD: Press  |  The JD Agent Suite  |  Powered by The JD Consultancy",
        styles["footer"]
    ))
    elements.append(Paragraph(
        "This EPK is confidential and intended solely for the named artist and their representatives.",
        styles["footer"]
    ))

    doc.build(elements)
    print(f"\nEPK generated: {filepath}")
    return filepath


# ─────────────────────────────────────────
# TEST — Run this file directly to test
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    # Import Pulse data pipeline for A2A simulation
    sys.path.append(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "..",
            "agent-jd-pulse"
        )
    )

    artist = input("Enter an artist name to generate an EPK: ")
    genre = input("Enter genre (or press Enter to skip): ")
    bio = input("Enter a short bio (or press Enter to skip): ")

    print(f"\nGenerating EPK for {artist}...")

    # Try to pull Pulse data for richer EPK
    try:
        from data.ingest import get_full_artist_profile
        print("Pulling artist data from Agent JD: Pulse pipeline...")
        pulse_data = get_full_artist_profile(artist)
    except Exception:
        pulse_data = {}

    filepath = generate_epk(
        artist_name=artist,
        genre=genre,
        bio=bio,
        pulse_data=pulse_data
    )

    print(f"\nDone! EPK saved at: {filepath}")