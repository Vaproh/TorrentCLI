# Torrent CLI (qBittorrent Automation Tool)

A command-line tool to automatically add `.torrent` files to **qBittorrent**, enforce clean folder structure, rename files, keep only video + subtitles, and respect category-based download paths.

This tool is designed primarily for **movie torrents** (YTS-style or similar).

---

## Features

- Automatically adds `.torrent` files to qBittorrent
- Uses **Movies / MOVIES / movies** category if it exists
- Falls back to a default download path if the category does not exist
- Forces **folder creation** even for single-file torrents
- Renames:
  - Root folder → `Movie Name (Year) [720p/1080p]`
  - Video file → `Movie Name (Year) [720p/1080p].mp4/.mkv`
  - Subtitles → `subtitles.srt`, `subtitles_2.srt`, etc.
- Downloads **only**:
  - Main video file
  - All `.srt` subtitle files
- Disables all junk files (images, txt, samples, etc.)
- Applies per-torrent speed limits
- Skips torrents already processed
- Safe to re-run multiple times
- Works as a Python script or standalone EXE

---

## Requirements

### Software
- Windows
- qBittorrent (Web UI enabled)
- Python 3.9+ (only if running as `.py`)
- PyInstaller (only if building EXE)

---

## qBittorrent Setup (IMPORTANT)

### 1. Enable Web UI
1. Open **qBittorrent**
2. Go to **Tools → Options → Web UI**
3. Enable **Web User Interface**
4. Set:
   - Port (default: `8080`)
   - Username
   - Password
5. Click **Apply**

---

### 2. Create a Movies Category (Recommended)

1. In qBittorrent, right-click **Categories**
2. Add a category named **one of these**:
   - `movies`
   - `Movies`
   - `MOVIES`
3. Set its **Save Path** (example):
```

D:\Movies

```

If none of these categories exist, the tool will fall back to the default download path.

---

## Folder Structure Example (Result)

```

D:\Movies
└─ The Astronaut (2025) [1080p]
├─ The Astronaut (2025) [1080p].mp4
├─ subtitles.srt
└─ subtitles_2.srt

````

---

## Configuration (`config.txt`)

Create a file named **`config.txt`** in the same folder as the script or EXE.

### Example `config.txt`

```ini
qb_url=http://localhost:8080
qb_user=admin
qb_pass=your_password_here

download_path=D:/Movies

dl_limit=1048576
ul_limit=512000
````

### Config Options Explained

| Key             | Description                                |
| --------------- | ------------------------------------------ |
| `qb_url`        | qBittorrent Web UI URL                     |
| `qb_user`       | Web UI username                            |
| `qb_pass`       | Web UI password                            |
| `download_path` | Fallback path if no Movies category exists |
| `dl_limit`      | Download speed per torrent (bytes/sec)     |
| `ul_limit`      | Upload speed per torrent (bytes/sec)       |

**Notes**

* `1048576` = 1 MB/s
* `512000` = 500 KB/s

---

## How to Use (Python Script)

```powershell
python torrent_cli.py "path\to\torrents" --unsafe --verbose
```

### Arguments

| Argument           | Description                        |
| ------------------ | ---------------------------------- |
| `path\to\torrents` | Folder containing `.torrent` files |
| `--unsafe`         | Actually add torrents (required)   |
| `--verbose`        | Print detailed logs                |

⚠️ Without `--unsafe`, the tool will **not** add torrents.

---

## How to Use (EXE)

```powershell
torrent-cli.exe "path\to\torrents" --unsafe --verbose
```

Make sure these files are next to the EXE:

```
torrent-cli.exe
config.txt
processed_torrents.txt (auto-created)
failed_torrents.txt    (auto-created)
```

---

## Processed & Failed Files

* **`processed_torrents.txt`**

  * Stores hashes of torrents already handled
  * Prevents duplicate downloads on re-runs

* **`failed_torrents.txt`**

  * Logs torrents that failed due to errors

Delete these files if you want to reprocess everything.

---

## Building the EXE (Optional)

```powershell
pip install pyinstaller
pyinstaller --onefile --name torrent-cli torrent_cli.py
```

Result:

```
dist\torrent-cli.exe
```

---

## Known Behavior (By Design)

* Only `.mp4` / `.mkv` + `.srt` files are downloaded
* All other files are skipped
* Folder creation is forced by moving files into a folder path
* Works reliably for both single-file and multi-file torrents

---

## Disclaimer

This tool only automates qBittorrent behavior.
You are responsible for how and where you use it.

---
