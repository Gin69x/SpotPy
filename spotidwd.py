import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython import VideosSearch
import yt_dlp
import os

# Set up Spotify API authentication
client_id = "b34b1565beb945cd8a2dfc3f86310cec"
client_secret = "f4b45173f02644069ca5fa8b51608683"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Define the download directory
DOWNLOAD_DIR = r"E:\Music"

# Ensure the download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Function to search YouTube and return the first video link
def search_youtube(query):
    search = VideosSearch(query, limit=1).result()
    if search["result"]:
        return search["result"][0]["link"]
    return None

# Function to download YouTube video as MP3

def download_youtube_audio(url, song_name):
    file_path = os.path.join(DOWNLOAD_DIR, song_name)  # Remove .mp3 here

    # Check if the file already exists
    if os.path.exists(file_path + ".mp3"):  # Check for existing .mp3 file
        print(f"Skipping {song_name}.mp3 (Already Downloaded)")
        return  # Skip download

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": file_path,  # No .mp3 here; yt-dlp adds it automatically
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "postprocessor_args": ["-metadata", f"title={song_name}"],
        "ffmpeg_location": r"C:\Program Files\ffmpeg-7.1-essentials_build\bin",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"Download complete: {song_name}.mp3")


# Function to get song info
def get_song_info(track):
    song_name = track["name"]
    artist_name = track["artists"][0]["name"]
    return f"{song_name} - {artist_name}"

# Function to process a Spotify link
def process_spotify_link(spotify_url):
    song_list = []

    if "track" in spotify_url:  # Single song
        track_info = sp.track(spotify_url)
        song_list.append(get_song_info(track_info))

    elif "album" in spotify_url:  # Album
        album_info = sp.album(spotify_url)
        for track in album_info["tracks"]["items"]:
            song_list.append(get_song_info(track))

    elif "playlist" in spotify_url:  # Playlist
        playlist_info = sp.playlist_tracks(spotify_url)
        for track in playlist_info["items"]:
            song_list.append(get_song_info(track["track"]))

    elif "artist" in spotify_url:  # Artist (Top 15 songs)
        artist_info = sp.artist_top_tracks(spotify_url)
        for track in artist_info["tracks"][:15]:  # Get top 15 songs
            song_list.append(get_song_info(track))

    return song_list

# Get Spotify link from user
spotify_link = "https://open.spotify.com/playlist/6ohgtfo6GdyGi68N8JBCwi?si=3859e40cc46541d4" # Enter Spotify Link

# Get song list
songs = process_spotify_link(spotify_link)

# Output results and download videos
print("\nSongs Found:")
for song in songs:
    youtube_link = search_youtube(song)
    if youtube_link:
        print(f"{song}\nYouTube Link: {youtube_link}\nDownloading to {DOWNLOAD_DIR}...")
        download_youtube_audio(youtube_link, song)
    else:
        print(f"{song}\nYouTube Link: Not found.\n")

# Print the array
print("Array =", songs)