# SpotPy CLI 

**A simple cross-platform command-line tool to download tracks from Spotify, YouTube & SoundCloud as MP3.**

> Made by Gin ([@Gin69x](https://github.com/Gin69x))

---

## 📖 Description

**SpotPy** (invoked via the `spotpy` command) lets you:
- Fetch track lists from any Spotify track, album, playlist or artist → download them via YouTube.
- Download individual YouTube or SoundCloud URLs or entire playlists/sets.
- Manually search YouTube for any query and grab the top N results.
- Display a beautifully formatted table of tracks without downloading (using `--show`).
- Automate your music downloads in a clean, colorized CLI experience.

Under the hood it uses:
- [Spotipy](https://github.com/plamere/spotipy) for Spotify API access  
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading & extracting audio  
- [youtubesearchpython](https://github.com/alexmercerind/youtube-search-python) for search  
- [Rich](https://github.com/Textualize/rich) & [Colorama](https://github.com/tartley/colorama) for styling  

---

## ⚙️ Features & Examples

| Feature                          | Example                                          |
|----------------------------------|--------------------------------------------------|
| **Show Spotify tracks**          | `spotpy -s https://open.spotify.com/album/…`     |
| **Download Spotify tracks**      | `spotpy -d https://open.spotify.com/track/…`     |
| **Show YouTube/SoundCloud list** | `spotpy -s https://youtu.be/…`                   |
| **Download YouTube/SoundCloud**  | `spotpy -d https://soundcloud.com/artist/track`  |
| **YouTube manual search**        | `spotpy --search "Imagine Dragons Believer" -s`  |
| **Limit number of items**        | `spotpy -d --limit 5 https://www.youtube.com/…`  |
| **Show without download**        | Always add `-s` / `--show`                       |
| **Overwrite existing**           | Add `--overwrite` to force re-download           |
| **Debug mode**                   | Add `--debug` for verbose logs                   |

---

## 🚀 Installation

### 1. Prerequisites
- **Python 3.8+** installed and on your `PATH`  
- Required packages:
  ```bash
  pip install spotipy yt-dlp youtubesearchpython rich colorama
  ```

### 2. Bootstrap Installation (Windows PowerShell)

Open PowerShell in the directory where you want to install `spotpy` and run:

```powershell
iwr https://raw.githubusercontent.com/Gin69x/SpotPy/55ee1361a8de6e4857e2701662066509cd4db76c/bootstrap-dwdpy.ps1 -UseBasicParsing | iex
```

This will:
- Create a `spotpy` folder
- Download `spotpy.py` and `config.json`
- Create a `spotpy.bat` launcher that uses the correct path
- Add the `spotpy` folder to your User PATH
- Open the folder in File Explorer at the end

Restart your terminal after the script finishes.

### 3. Manual Install

```bash
git clone https://github.com/Gin69x/SpotPy.git spotpy
cd spotpy
# Edit config.json with your credentials
# Add this folder to your PATH manually, or use:
python spotpy.py -h
```

---

## 🔧 Configuration

Edit `config.json` inside the `spotpy` directory:

```json
{
  "CLIENT_ID":     "your_spotify_client_id",
  "CLIENT_SECRET": "your_spotify_client_secret",
  "PREFERRED_DIR": "E:\\Music"
}
```

- You must register your app on [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) to get the `CLIENT_ID` and `CLIENT_SECRET`.
- `PREFERRED_DIR` is where the downloaded MP3s will be saved by default.

---

## 🛠 Usage

```bash
# Show help
spotpy --help

# Show Spotify playlist contents
spotpy -s https://open.spotify.com/playlist/…

# Download from YouTube search query
spotpy --search "Lo-fi beats" -d --search-limit 10

# Download a YouTube playlist
spotpy -d --limit 5 "https://www.youtube.com/playlist?list=…"

# Download a SoundCloud track or set
spotpy -d https://soundcloud.com/artist/track
```

---

## 🧹 Uninstallation

To uninstall `spotpy`:

### 1. Delete the `spotpy` folder

Simply remove the folder where it was installed.

### 2. Remove it from your PATH

#### Option A: Via GUI
- Open **Environment Variables**
- Under **User variables**, edit `Path`
- Remove the entry ending in `\spotpy`

#### Option B: Via PowerShell
```powershell
$p = [Environment]::GetEnvironmentVariable('Path','User').Split(';') 
$new = ($p | Where-Object { $_ -notlike '*\spotpy' }) -join ';'
[Environment]::SetEnvironmentVariable('Path',$new,'User')
```

---


> Built with ❤️ by **Gin**  
> [GitHub](https://github.com/Gin69x)
