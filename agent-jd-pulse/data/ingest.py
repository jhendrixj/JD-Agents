import os
import requests
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables from .env file
load_dotenv()

# ─────────────────────────────────────────
# SPOTIFY SETUP
# ─────────────────────────────────────────

def get_spotify_client():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def get_artist_data(artist_name: str):
    """
    Fetches core artist data from Spotify.
    """
    sp = get_spotify_client()

    # Search for the artist
    results = sp.search(q=artist_name, type="artist", limit=1)
    artists = results.get("artists", {}).get("items", [])

    if not artists:
        return {"error": f"Artist '{artist_name}' not found on Spotify."}

    artist = artists[0]
    artist_id = artist.get("id", "")

    # Fetch full artist object directly for complete data
    full_artist = sp.artist(artist_id)

    return {
        "name": full_artist.get("name", "Unknown"),
        "spotify_id": artist_id,
        "popularity": full_artist.get("popularity", 0),
        "followers": full_artist.get("followers", {}).get("total", 0),
        "genres": full_artist.get("genres", []),
        "spotify_url": full_artist.get("external_urls", {}).get("spotify", ""),
        "image_url": full_artist["images"][0]["url"] if full_artist.get("images") else None
    }


def get_artist_top_tracks(artist_id: str, market: str = "KE"):
    """
    Fetches the artist's top tracks using album tracks endpoint.
    """
    sp = get_spotify_client()
    
    # Get artist's albums first
    albums = sp.artist_albums(artist_id, album_type="album,single", limit=3)
    album_items = albums.get("items", [])
    
    top_tracks = []
    
    for album in album_items:
        # Get tracks from each album
        tracks = sp.album_tracks(album["id"], limit=3)
        track_items = tracks.get("items", [])
        
        for track in track_items:
            top_tracks.append({
                "name": track.get("name", ""),
                "duration_ms": track.get("duration_ms", 0),
                "album": album.get("name", ""),
                "release_date": album.get("release_date", ""),
                "spotify_url": track.get("external_urls", {}).get("spotify", ""),
                "track_number": track.get("track_number", 0)
            })
    
    # Return top 10
    return top_tracks[:10]


def get_artist_albums(artist_id: str):
    """
    Fetches the artist's discography - albums and singles.
    """
    sp = get_spotify_client()
    
    results = sp.artist_albums(
        artist_id,
        album_type="album,single",
        limit=10
    )
    albums = results.get("items", [])

    discography = []
    for album in albums:
        discography.append({
            "name": album.get("name", ""),
            "type": album.get("album_type", ""),
            "release_date": album.get("release_date", ""),
            "total_tracks": album.get("total_tracks", 0),
            "spotify_url": album.get("external_urls", {}).get("spotify", "")
        })

    return discography


def get_related_artists(artist_id: str):
    """
    Finds similar artists by searching within the same genres.
    Used for competitive benchmarking.
    """
    sp = get_spotify_client()

    # First get the artist's genres
    artist = sp.artist(artist_id)
    genres = artist.get("genres", [])

    if not genres:
        return []

    # Search for artists in the same genre
    genre_query = genres[0]  # Use primary genre
    results = sp.search(
        q=f"genre:{genre_query}",
        type="artist",
        limit=5
    )

    artists = results.get("artists", {}).get("items", [])

    benchmarks = []
    for a in artists:
        # Skip if it's the same artist
        if a["id"] == artist_id:
            continue
        benchmarks.append({
            "name": a.get("name", ""),
            "popularity": a.get("popularity", 0),
            "followers": a.get("followers", {}).get("total", 0),
            "genres": a.get("genres", []),
            "spotify_url": a.get("external_urls", {}).get("spotify", "")
        })

    # Return top 3
    return benchmarks[:3]


# ─────────────────────────────────────────
# YOUTUBE SETUP
# ─────────────────────────────────────────

def get_youtube_channel_data(artist_name: str):
    """
    Searches YouTube for the artist's channel and
    returns subscriber count, view count, and video count.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    base_url = "https://www.googleapis.com/youtube/v3"

    # Search for the channel
    search_url = f"{base_url}/search"
    search_params = {
        "part": "snippet",
        "q": artist_name,
        "type": "channel",
        "maxResults": 1,
        "key": api_key
    }

    search_response = requests.get(search_url, params=search_params)
    search_data = search_response.json()
    items = search_data.get("items", [])

    if not items:
        return {"error": f"No YouTube channel found for '{artist_name}'."}

    channel_id = items[0]["id"]["channelId"]
    channel_title = items[0]["snippet"]["title"]

    # Get channel statistics
    stats_url = f"{base_url}/channels"
    stats_params = {
        "part": "statistics,snippet",
        "id": channel_id,
        "key": api_key
    }

    stats_response = requests.get(stats_url, params=stats_params)
    stats_data = stats_response.json()
    channel_info = stats_data.get("items", [{}])[0]
    stats = channel_info.get("statistics", {})

    return {
        "channel_name": channel_title,
        "channel_id": channel_id,
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "youtube_url": f"https://www.youtube.com/channel/{channel_id}"
    }


def get_youtube_recent_videos(channel_id: str):
    """
    Fetches the 5 most recent videos from the artist's YouTube channel.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    base_url = "https://www.googleapis.com/youtube/v3"

    search_url = f"{base_url}/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 5,
        "order": "date",
        "type": "video",
        "key": api_key
    }

    response = requests.get(search_url, params=params)
    data = response.json()
    items = data.get("items", [])

    videos = []
    for item in items:
        video_id = item["id"]["videoId"]
        videos.append({
            "title": item["snippet"]["title"],
            "published_at": item["snippet"]["publishedAt"],
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
        })

    return videos


# ─────────────────────────────────────────
# MASTER FUNCTION
# ─────────────────────────────────────────

def get_full_artist_profile(artist_name: str):
    """
    Master function that pulls all data for an artist
    from both Spotify and YouTube in one call.
    """
    print(f"Fetching data for: {artist_name}")

    # Spotify data
    spotify_profile = get_artist_data(artist_name)

    if "error" in spotify_profile:
        return {"error": spotify_profile["error"]}

    artist_id = spotify_profile["spotify_id"]
    top_tracks = get_artist_top_tracks(artist_id)
    discography = get_artist_albums(artist_id)
    related_artists = get_related_artists(artist_id)

    # YouTube data
    youtube_data = get_youtube_channel_data(artist_name)
    recent_videos = []

    if "error" not in youtube_data:
        recent_videos = get_youtube_recent_videos(
            youtube_data["channel_id"]
        )

    return {
        "artist_name": artist_name,
        "spotify": {
            "profile": spotify_profile,
            "top_tracks": top_tracks,
            "discography": discography,
            "related_artists": related_artists
        },
        "youtube": {
            "channel": youtube_data,
            "recent_videos": recent_videos
        }
    }


# ─────────────────────────────────────────
# TEST — Run this file directly to test
# ─────────────────────────────────────────

if __name__ == "__main__":
    import json
    artist = input("Enter an artist name to test: ")
    profile = get_full_artist_profile(artist)
    print(json.dumps(profile, indent=2))