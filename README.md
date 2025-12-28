# TorrentCLI

A strict, opinionated command-line tool for automating **qBittorrent** downloads into
**clean, Jellyfin/Plex-compatible movie and TV libraries**.

TorrentCLI exists to enforce *correct filesystem structure*.
It does not guess. It does not “figure things out later”.
It normalizes torrents **at download time** so media servers behave predictably.

---

## Features

### General
- Adds `.torrent` files to qBittorrent via Web API
- Safe to re-run (processed torrents are tracked)
- Cleans up failed torrents automatically
- Works as a standalone EXE (no Python required)

### Movies
- Detects movie torrents automatically
- Enforces this structure:

```

Movies/
└── Movie Name (Year)/
├── Movie Name (Year).mkv
├── Movie Name (Year).en.srt
├── Movie Name (Year).en.sdh.srt

```

- Fails fast if the movie year is missing (prevents bad metadata)

### TV Shows (including anime)
- Detects TV torrents using `SxxEyy`, `SxxEyyEzz`, or `1x01` patterns
- Enforces this structure:

```

TV Shows/
└── Show Name (Year)/
└── Season 01/
├── Show Name - S01E01.mkv
├── Show Name - S01E01.en.srt

```

- Multi-episode files are supported (`S01E01E02`)
- Anime is treated as TV for scanner compatibility

### Subtitles
- Renamed to match the video file exactly
- Language + variant support:
  - Languages: `en`, `hi`, `ja`, `fr`, `es`
  - Variants: `forced`, `sdh`, `cc`

Examples:
```

Movie Name (2023).en.srt
Show Name - S01E01.en.forced.srt
Show Name - S01E01.en.sdh.srt

````

### qBittorrent Integration
- Uses **existing categories only**
  - Movies: `movies`, `Movies`, `MOVIES`
  - TV: `tv`, `TV`, `Shows`, `shows`
- Category save paths are respected if present
- Falls back to configured paths if categories do not exist
- Per-torrent download & upload limits
- Only the main video file and subtitles are downloaded

---

## Requirements

- Windows
- qBittorrent with **Web UI enabled**
- (Optional) Python 3.9+ if running as a script  
  *(EXE users do not need Python)*

---

## Setup

### 1. Enable qBittorrent Web UI
In qBittorrent:
1. `Tools → Options → Web UI`
2. Enable Web UI
3. Set username, password, and port (default: `8080`)

---

### 2. Configuration

Copy `config.example.txt` to `config.txt` and edit it:

```ini
qb_url=http://localhost:8080
qb_user=admin
qb_pass=your_password

fallback_movies=D:/Movies
fallback_tv=D:/TV Shows

dl_limit=1048576
ul_limit=512000
````

Categories are **optional**.
If they exist in qBittorrent, they are used.
If not, fallback paths are used.

---

## Usage

### Command Line

```powershell
torrent-cli.exe "path\to\torrents" --unsafe --verbose
```

or (Python):

```powershell
python torrent_cli.py "path\to\torrents" --unsafe --verbose
```

### Arguments

| Argument           | Description                        |
| ------------------ | ---------------------------------- |
| `<torrent_folder>` | Folder containing `.torrent` files |
| `--unsafe`         | Required to actually add torrents  |
| `--verbose`        | Print detailed logs                |
| `--help`           | Show usage help                    |

---

## Output Files

The following files are created automatically:

* `processed_torrents.txt`
  → Tracks already processed torrents (safe re-runs)
* `failed_torrents.txt`
  → Logs failures and parsing errors

---

## Design Philosophy

* Folder defines the media
* Filename defines the identity
* Subtitles match the filename
* Computers match strings, not intentions

If something is ambiguous, TorrentCLI **fails instead of guessing**.

---

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for detailed release notes.

---

## Disclaimer

This tool only automates qBittorrent behavior.
You are responsible for the legality of the content you download.