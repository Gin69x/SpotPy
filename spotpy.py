# -*- coding: utf-8 -*-
import os
import sys
import argparse
import spotipy
import logging
import time
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython import VideosSearch
import yt_dlp
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import json

from colorama import init as colorama_init
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

# ── CONFIG LOADING ────────────────────────────────────────────────────────────
colorama_init(autoreset=True)
console = Console()

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
if not os.path.isfile(CONFIG_PATH):
    console.print(f"[red]✖ config.json not found at {CONFIG_PATH}[/red]")
    sys.exit(1)

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
except Exception as e:
    console.print(f"[red]✖ Failed to parse config.json:[/] {e}")
    sys.exit(1)

# Require these keys in config.json
for key in ("CLIENT_ID", "CLIENT_SECRET", "PREFERRED_DIR"):
    if key not in cfg or not cfg[key]:
        console.print(f"[red]✖ Missing required '{key}' in config.json[/red]")
        sys.exit(1)

CLIENT_ID     = cfg["CLIENT_ID"]
CLIENT_SECRET = cfg["CLIENT_SECRET"]
PREFERRED_DIR = cfg["PREFERRED_DIR"]

# Prepare fallback directory
FALLBACK_DIR = os.path.join(SCRIPT_DIR, "songs")
os.makedirs(FALLBACK_DIR, exist_ok=True)

# Suppress Spotify cache warnings
logging.getLogger("spotipy").setLevel(logging.ERROR)
# ── END CONFIG LOADING ────────────────────────────────────────────────────────

def is_youtube_link(url):
    return any(domain in url for domain in ["youtube.com/watch", "youtu.be/", "youtube.com/playlist"])

def is_soundcloud_link(url):
    return "soundcloud.com" in url


def parse_args():
    parser = argparse.ArgumentParser(
        prog="spotpy",
        description="Download or show tracks from Spotify/YouTube/SoundCloud links as MP3",
        epilog=(
            "Examples:\n"
            "  spotpy -d https://open.spotify.com/track/...\n"
            "  spotpy --show https://youtu.be/...\n"
            "  spotpy -d https://soundcloud.com/artist/track\n"
            "  spotpy --search \"Imagine Dragons Believer\" -d\n"
            "  spotpy -d --limit 5 https://www.youtube.com/playlist?list=...\n"
            "  spotpy -d --overwrite -o C:\\MyMusic https://..."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--download', action='store_true', help='Download MP3s')
    group.add_argument('-s', '--show', action='store_true', help='Show track list only')
    parser.add_argument('--search', metavar='QUERY', help='Search YouTube manually and process result')
    parser.add_argument('--limit', type=int, help='Limit number of tracks to process/download')
    parser.add_argument('-o', '--output-dir', metavar='DIR', help='Custom output directory for downloads')
    parser.add_argument('--overwrite', action='store_true', help='Redownload even if file exists')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--search-limit', type=int, help='Number of YouTube search results to show (default: uses --limit or 5)')
    parser.add_argument('link', nargs='?', help='Spotify, YouTube, or SoundCloud URL')
    return parser.parse_args()


def get_spotify_songs(sp, url):
    def info_to_str(track):
        return track['name'], track['artists'][0]['name']

    items = []
    if 'track' in url:
        items.append(sp.track(url))
    elif 'album' in url:
        items.extend(sp.album(url)['tracks']['items'])
    elif 'playlist' in url:
        items.extend(item['track'] for item in sp.playlist_tracks(url)['items'] if item.get('track'))
    elif 'artist' in url:
        items.extend(sp.artist_top_tracks(url)['tracks'][:15])
    return [info_to_str(t) for t in items]

def get_youtube_search_results(query, total_limit):
    search = VideosSearch(query, limit=20)  # always set high per-page limit
    all_results = []

    while len(all_results) < total_limit:
        result = search.result()
        all_results.extend(result.get("result", []))
        if not search.next():
            break  # no more pages
    return all_results[:total_limit]  # return only up to requested limit

def get_videos_info(url):
    is_sc = is_soundcloud_link(url)
    is_yt = is_youtube_link(url)
    is_playlist = "playlist?" in url or "&list=" in url

    # Choose extractor options
    if is_sc:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'force_generic_extractor': True,
        }
    elif is_yt and is_playlist:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
    else:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'force_generic_extractor': False,
        }

    # Attempt extraction with clear error handling
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.ExtractorError as ee:
        console.print(f"[red]✖  Extraction error:[/] {ee}")
        return []
    except yt_dlp.utils.DownloadError as de:
        console.print(f"[red]✖  Download error:[/] {de}")
        return []
    except Exception as e:
        console.print(f"[red]✖  Unexpected error parsing URL:[/] {e}")
        return []

    # Gather entries (playlists or single videos)
    entries = info.get('entries') or []
    if is_sc and not entries:
        entries = info.get('tracks') or []

    # Single video fallback
    if not entries and 'title' in info:
        entries = [info]

    if not entries:
        console.print(f"[yellow]⚠ No tracks found at this URL.[/yellow]")
        return []

    # Build track list
    tracks = []
    for e in entries:
        link = e.get('webpage_url') or e.get('url') or e.get('id')
        title = e.get('title') or e.get('id')
        uploader = e.get('uploader') or info.get('uploader') or ''

        # Rebuild YouTube URL if needed
        if is_yt and not str(link).startswith('http'):
            link = f"https://www.youtube.com/watch?v={link}"

        tracks.append((link, title, uploader))

    return tracks

class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): console.print(f"[red]{msg}[/red]")


def download_audio(url, title, download_dir, overwrite):
    safe = ''.join(c for c in title if c.isalnum() or c in ' .-_')
    out_path = os.path.join(download_dir, safe)
    mp3_path = out_path + '.mp3'

    if os.path.exists(mp3_path) and not overwrite:
        console.print(f"[yellow]⚠  Skipping:[/] {title}.mp3 already exists")
        return

    opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'postprocessor_args': ['-metadata', f"title={title}"],
        'ffmpeg_location': r"C:\Program Files\ffmpeg-7.1-essentials_build\bin",
        'quiet': True,
        'no_warnings': True,
        'logger': QuietLogger()
    }
    with console.status(f"[cyan]Downloading:[/] {title}", spinner="dots"):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            console.print(f"[green]✔ Downloaded:[/] {title}.mp3")
        except Exception as e:
            console.print(f"[red]✖ Failed:[/] {title} — {e}")


def show_table(tracks, source):
    color_map = {"Spotify": "green", "YouTube": "red", "SoundCloud": "orange1", "Search Results": "blue"}
    color = color_map.get(source, "white")
    table = Table(title=f"[{color}]{source} Tracks[/{color}]", show_lines=True)
    table.add_column("#", justify="right", style="bold")
    table.add_column("Artist", style="bright_blue")
    table.add_column("Title", style="bright_white")
    
    for idx, item in enumerate(tracks, 1):
        if source == "Spotify":
            title, artist = item  # Spotify returns (song, artist)
        else:
            artist, title = item  # Others return (artist, title)
        table.add_row(str(idx), artist or "—", title)
    
    console.print(table)



def main():
    args = parse_args()

    # Configure debug
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("[magenta]Debug mode on[/magenta]")

    # Determine download directory
    base_dir = args.output_dir or (PREFERRED_DIR if os.path.exists(PREFERRED_DIR) else FALLBACK_DIR)
    os.makedirs(base_dir, exist_ok=True)

    # Manual search
    if args.search:
        # Determine how many search results to fetch
        search_limit = args.search_limit or args.limit or 5  # Default to 5 if neither is set

        console.print(f"[blue]🔍 Searching YouTube:[/] {args.search} (showing top {search_limit})")
        results = get_youtube_search_results(args.search, search_limit)

        items = []
        for item in results:
            channel = item.get('channel', {}).get('name', item.get('uploader', 'Unknown'))
            title = item.get('title', 'No Title')
            items.append((channel, title))
        show_table(items, 'Search Results')

        # If download flag, download ALL results
        if args.download and results:
            for item in results:
                link = item.get('link')
                channel = item.get('channel', {}).get('name', item.get('uploader', 'Unknown'))
                title = item.get('title')
                full = f"{channel} - {title}"
                download_audio(link, full, base_dir, args.overwrite)
        return

    # From here on, we expect a link
    link = args.link
    if not link:
        console.print("[red]Error:[/] No link provided.")
        sys.exit(1)

    # Special‐case YouTube watch URLs: keep only the v= parameter
    if is_youtube_link(link) and "watch" in link:
        parsed = urlparse(link)
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            clean_query = urlencode({"v": qs["v"][0]})
            clean_parsed = parsed._replace(query=clean_query, path=parsed.path)
            clean_link = urlunparse(clean_parsed)
            console.print(f"[yellow]⚠  Stripping extra YouTube params.[/yellow]")
            console.print(f"    Using: [cyan]{clean_link}[/cyan]")
            link = clean_link
        else:
            console.print(f"[yellow]⚠  No v= parameter found in YouTube URL; using base.[/yellow]")
            link = f"https://www.youtube.com/watch?v={parsed.path.split('=')[-1]}"

    # For any other link (SoundCloud or non-watch YouTube), strip all params
    elif '?' in link:
        base, _ = link.split('?', 1)
        console.print(f"[yellow]⚠  Stripping query parameters from URL to avoid shell errors.[/yellow]")
        console.print(f"    Using: [cyan]{base}[/cyan]")
        link = base

    # Now process based on link type

    # YouTube or SoundCloud
    if is_youtube_link(link) or is_soundcloud_link(link):
        source = 'YouTube' if is_youtube_link(link) else 'SoundCloud'
        start_time = time.monotonic()
        vids = get_videos_info(link)
        if not vids:
            console.print(f"[red]✖  No valid tracks found in the provided {source} link.[/red]")
            return
        elapsed = time.monotonic() - start_time
        if elapsed > 10:
            console.print("[yellow]⚠ This operation took longer than 10 seconds, please be patient...[/yellow]")

        # Apply limit
        if args.limit:
            vids = vids[:args.limit]

        tracks = [(uploader, title) for _, title, uploader in vids]
        if args.show:
            show_table(tracks, source)
        else:
            for url_item, title, uploader in vids:
                full = f"{uploader} - {title}" if uploader else title
                download_audio(url_item, full, base_dir, args.overwrite)
        console.print(f"\n[bold green]✅  All downloads completed.[/bold green]")
        return

    # Spotify handling
    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=CLIENT_ID, client_secret=CLIENT_SECRET
            )
        )
        start_time = time.monotonic()
        songs = get_spotify_songs(sp, link)
    except Exception as e:
        console.print(f"[red]✖  Spotify error:[/] Unable to connect to Spotify API ({e}).")
        console.print("[yellow]⚠  Please check your internet connection or your client credentials.[/yellow]")
        return
    elapsed = time.monotonic() - start_time
    if elapsed > 10:
        console.print("[yellow]⚠  This operation took longer than 10 seconds, please be patient...[/yellow]")

    if args.limit:
        songs = songs[:args.limit]

    if args.show:
        show_table(songs, "Spotify")
    else:
        console.print("[bold cyan]🎵 Downloading Spotify Tracks:[/bold cyan]")
        for name, artist in songs:
            console.print(f"→ [cyan]{artist}[/cyan] - [magenta]{name}[/magenta]")
            res = VideosSearch(f"{name} {artist}", limit=1).result()
            if res['result']:
                download_audio(res['result'][0]['link'], f"{artist} - {name}", base_dir, args.overwrite)
            else:
                console.print(f"[red]✖ No YouTube result for: {artist} - {name}[/red]")
        console.print(f"\n[bold green]✅  All downloads completed.[/bold green]")

if __name__ == '__main__':
    main()
