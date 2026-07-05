import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from datetime import datetime
import json


# ─────────────────────────────────────────
# AUDIENCE CLUSTERING
# ─────────────────────────────────────────

def cluster_audience(artist_profile: dict):
    """
    Analyses the artist's audience and clusters them
    into segments based on available data.
    Returns audience personas.
    """

    spotify = artist_profile.get("spotify", {})
    youtube = artist_profile.get("youtube", {})

    # Extract metrics
    followers = spotify.get("profile", {}).get("followers", 0)
    popularity = spotify.get("profile", {}).get("popularity", 0)
    genres = spotify.get("profile", {}).get("genres", [])
    subscribers = youtube.get("channel", {}).get("subscribers", 0)
    total_views = youtube.get("channel", {}).get("total_views", 0)
    video_count = youtube.get("channel", {}).get("video_count", 1)

    # Calculate engagement metrics
    avg_views_per_video = total_views / max(video_count, 1)
    youtube_to_spotify_ratio = subscribers / max(followers, 1)
    engagement_score = (popularity + (subscribers / 100000)) / 2

    # Build audience segments based on platform behaviour
    segments = []

    # Segment 1 — Core Streaming Fans
    segments.append({
        "segment": "Core Streaming Fans",
        "description": "Dedicated listeners who follow the artist on Spotify and stream regularly",
        "estimated_size": f"{int(followers * 0.6):,}",
        "platform": "Spotify",
        "behaviour": "Regular streaming, playlist saves, album follows",
        "engagement": "High"
    })

    # Segment 2 — Visual Content Consumers
    segments.append({
        "segment": "Visual Content Consumers",
        "description": "Fans primarily engaged through music videos and YouTube content",
        "estimated_size": f"{int(subscribers * 0.7):,}",
        "platform": "YouTube",
        "behaviour": f"Average {int(avg_views_per_video):,} views per video",
        "engagement": "Medium to High"
    })

    # Segment 3 — Casual Listeners
    segments.append({
        "segment": "Casual Listeners",
        "description": "Occasional listeners who discover music through playlists or recommendations",
        "estimated_size": f"{int(followers * 0.3):,}",
        "platform": "Cross-platform",
        "behaviour": "Passive listening, discovery-driven",
        "engagement": "Low to Medium"
    })

    # Segment 4 — Cross-Platform Superfans
    segments.append({
        "segment": "Cross-Platform Superfans",
        "description": "Highly engaged fans active across all platforms",
        "estimated_size": f"{int(min(followers, subscribers) * 0.1):,}",
        "platform": "All platforms",
        "behaviour": "Streams, watches, shares, and attends events",
        "engagement": "Very High"
    })

    return {
        "total_estimated_audience": f"{int(followers + subscribers):,}",
        "engagement_score": round(engagement_score, 2),
        "primary_genre": genres[0] if genres else "Not specified",
        "youtube_to_spotify_ratio": round(youtube_to_spotify_ratio, 3),
        "segments": segments
    }


# ─────────────────────────────────────────
# RELEASE TIMING PREDICTOR
# ─────────────────────────────────────────

def predict_release_timing(artist_profile: dict):
    """
    Analyses the artist's release history and recommends
    optimal release windows based on patterns.
    """

    discography = artist_profile.get("spotify", {}).get("discography", [])

    if not discography:
        return {"error": "No discography data available."}

    # Extract release dates
    release_dates = []
    for item in discography:
        date_str = item.get("release_date", "")
        if date_str and len(date_str) >= 7:
            try:
                if len(date_str) == 10:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    date = datetime.strptime(date_str[:7], "%Y-%m")
                release_dates.append({
                    "name": item.get("name", ""),
                    "date": date,
                    "month": date.month,
                    "quarter": (date.month - 1) // 3 + 1,
                    "type": item.get("type", "")
                })
            except ValueError:
                continue

    if not release_dates:
        return {"error": "Could not parse release dates."}

    # Analyse release patterns
    months = [r["month"] for r in release_dates]
    quarters = [r["quarter"] for r in release_dates]

    # Find most active months and quarters
    month_counts = pd.Series(months).value_counts()
    quarter_counts = pd.Series(quarters).value_counts()

    most_active_month = month_counts.index[0]
    most_active_quarter = quarter_counts.index[0]

    # Month names
    month_names = {
        1: "January", 2: "February", 3: "March",
        4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September",
        10: "October", 11: "November", 12: "December"
    }

    quarter_names = {
        1: "Q1 (January - March)",
        2: "Q2 (April - June)",
        3: "Q3 (July - September)",
        4: "Q4 (October - December)"
    }

    # Calculate average gap between releases
    if len(release_dates) > 1:
        sorted_dates = sorted(release_dates, key=lambda x: x["date"])
        gaps = []
        for i in range(1, len(sorted_dates)):
            gap = (sorted_dates[i]["date"] - sorted_dates[i-1]["date"]).days
            gaps.append(gap)
        avg_gap_days = int(np.mean(gaps))
        avg_gap_months = round(avg_gap_days / 30, 1)
    else:
        avg_gap_days = 0
        avg_gap_months = 0

    # Industry best practice recommendations
    recommendations = []

    if most_active_quarter in [1, 4]:
        recommendations.append(
            "This artist performs well in Q1 and Q4 — consider January or October releases"
        )
    if most_active_quarter in [2, 3]:
        recommendations.append(
            "This artist performs well in Q2 and Q3 — consider April or July releases"
        )

    recommendations.append(
        f"Based on release history, aim for a new release every {avg_gap_months} months"
    )

    recommendations.append(
        "Industry standard: Release singles 4-6 weeks before an album to build momentum"
    )

    recommendations.append(
        "Avoid releasing on major holiday weekends — streams drop as social activity increases"
    )

    return {
        "total_releases_analysed": len(release_dates),
        "most_active_month": month_names.get(most_active_month, "Unknown"),
        "most_active_quarter": quarter_names.get(most_active_quarter, "Unknown"),
        "average_release_gap_months": avg_gap_months,
        "recommended_next_window": month_names.get(most_active_month, "Unknown"),
        "recommendations": recommendations,
        "release_history": [
            {
                "name": r["name"],
                "date": r["date"].strftime("%B %Y"),
                "type": r["type"]
            }
            for r in sorted(release_dates, key=lambda x: x["date"], reverse=True)
        ]
    }


# ─────────────────────────────────────────
# REVENUE GAP ANALYSIS
# ─────────────────────────────────────────

def analyse_revenue_gaps(artist_profile: dict):
    """
    Identifies revenue opportunities the artist
    may be missing based on their profile data.
    """

    spotify = artist_profile.get("spotify", {})
    youtube = artist_profile.get("youtube", {})

    followers = spotify.get("profile", {}).get("followers", 0)
    subscribers = youtube.get("channel", {}).get("subscribers", 0)
    total_views = youtube.get("channel", {}).get("total_views", 0)
    video_count = youtube.get("channel", {}).get("video_count", 1)
    discography = spotify.get("discography", [])

    gaps = []
    opportunities = []

    # Streaming revenue estimate
    # Industry average: $0.003 - $0.005 per stream
    estimated_monthly_streams = followers * 0.3
    estimated_monthly_streaming_revenue = estimated_monthly_streams * 0.004
    opportunities.append({
        "stream": "Spotify Streaming",
        "estimated_monthly_revenue": f"${estimated_monthly_streaming_revenue:,.0f}",
        "basis": f"Based on {followers:,} followers at industry average stream rate"
    })

    # YouTube revenue estimate
    # Industry average: $1 - $3 per 1000 views
    avg_views_per_video = total_views / max(video_count, 1)
    estimated_youtube_monthly = (avg_views_per_video * 0.002) * 4
    opportunities.append({
        "stream": "YouTube Ad Revenue",
        "estimated_monthly_revenue": f"${estimated_youtube_monthly:,.0f}",
        "basis": f"Based on {int(avg_views_per_video):,} average views per video"
    })

    # Gap Analysis
    if subscribers < followers * 0.1:
        gaps.append({
            "gap": "Low YouTube Presence",
            "insight": "YouTube subscribers are significantly lower than Spotify followers",
            "recommendation": "Invest in consistent video content to convert Spotify fans to YouTube subscribers",
            "potential_impact": "High"
        })

    if video_count < 20:
        gaps.append({
            "gap": "Limited Video Catalogue",
            "insight": f"Only {video_count} videos on YouTube limits ad revenue potential",
            "recommendation": "Increase video output — behind the scenes, lyric videos, and live sessions perform well",
            "potential_impact": "Medium to High"
        })

    if len(discography) < 3:
        gaps.append({
            "gap": "Limited Catalogue Depth",
            "insight": "A small catalogue limits streaming revenue from passive playlist discovery",
            "recommendation": "Consistent single releases between albums maintain streaming momentum",
            "potential_impact": "High"
        })

    # Sync licensing opportunity
    gaps.append({
        "gap": "Sync Licensing",
        "insight": "Music placement in film, TV, and advertising is often underutilised by independent artists",
        "recommendation": "Register with sync licensing platforms like Musicbed, Artlist, or Songtradr",
        "potential_impact": "Very High"
    })

    # Merchandise opportunity
    gaps.append({
        "gap": "Merchandise Revenue",
        "insight": "Artists with strong fanbases often underutilise merchandise as a revenue stream",
        "recommendation": "Launch a merchandise store via Shopify or Printful integrated with social platforms",
        "potential_impact": "Medium"
    })

    return {
        "revenue_opportunities": opportunities,
        "identified_gaps": gaps,
        "total_gaps_found": len(gaps),
        "priority_action": gaps[0]["recommendation"] if gaps else "Revenue streams appear well optimised"
    }


# ─────────────────────────────────────────
# COMPETITIVE BENCHMARKING
# ─────────────────────────────────────────

def benchmark_against_peers(artist_profile: dict):
    """
    Compares the artist against similar artists
    pulled from the data pipeline.
    """

    spotify = artist_profile.get("spotify", {})
    artist_name = artist_profile.get("artist_name", "This Artist")

    artist_followers = spotify.get("profile", {}).get("followers", 0)
    artist_popularity = spotify.get("profile", {}).get("popularity", 0)
    related = spotify.get("related_artists", [])

    if not related:
        return {
            "message": "No peer artists available for benchmarking at this time.",
            "artist_metrics": {
                "name": artist_name,
                "followers": f"{artist_followers:,}",
                "popularity_score": artist_popularity
            }
        }

    benchmarks = []
    for peer in related:
        peer_followers = peer.get("followers", 0)
        peer_popularity = peer.get("popularity", 0)

        follower_diff = artist_followers - peer_followers
        popularity_diff = artist_popularity - peer_popularity

        benchmarks.append({
            "peer_name": peer.get("name", "Unknown"),
            "peer_followers": f"{peer_followers:,}",
            "peer_popularity": peer_popularity,
            "follower_difference": f"{follower_diff:+,}",
            "popularity_difference": f"{popularity_diff:+}",
            "position": "ahead" if follower_diff > 0 else "behind"
        })

    return {
        "artist": artist_name,
        "artist_followers": f"{artist_followers:,}",
        "artist_popularity": artist_popularity,
        "peer_comparison": benchmarks
    }


# ─────────────────────────────────────────
# MASTER ANALYTICS FUNCTION
# ─────────────────────────────────────────

def run_full_analytics(artist_profile: dict):
    """
    Runs all analytics models on the artist profile
    and returns a complete intelligence report.
    """

    print("Running audience clustering...")
    audience = cluster_audience(artist_profile)

    print("Running release timing analysis...")
    timing = predict_release_timing(artist_profile)

    print("Running revenue gap analysis...")
    revenue = analyse_revenue_gaps(artist_profile)

    print("Running competitive benchmarking...")
    benchmark = benchmark_against_peers(artist_profile)

    return {
        "artist": artist_profile.get("artist_name", "Unknown"),
        "generated_at": datetime.now().strftime("%B %d, %Y at %H:%M"),
        "audience_analysis": audience,
        "release_timing": timing,
        "revenue_analysis": revenue,
        "competitive_benchmark": benchmark
    }


# ─────────────────────────────────────────
# TEST — Run this file directly to test
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.ingest import get_full_artist_profile
    import json

    artist = input("Enter an artist name to test: ")
    print(f"\nFetching data for {artist}...")
    profile = get_full_artist_profile(artist)

    print("\nRunning analytics...")
    results = run_full_analytics(profile)

    print(json.dumps(results, indent=2))