import requests
import sys
import time
import re
import hashlib
from pathlib import Path

# ================= CONFIG =================
CONFIG = {
    "qb_url": "http://localhost:8080",
    "qb_user": "",
    "qb_pass": "",
    "download_path": "D:/Movies",
    "categories": ["movies", "Movies", "MOVIES"],
    "dl_limit": 1048576,   # 1 MB/s
    "ul_limit": 512000,    # 500 KB/s
    "processed": "processed_torrents.txt",
    "failed": "failed_torrents.txt",
}

# ================= LOAD CONFIG.TXT =================
if Path("config.txt").exists():
    for line in Path("config.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        CONFIG[k.strip()] = v.strip()

QB_URL = CONFIG["qb_url"]
QB_USER = CONFIG["qb_user"]
QB_PASS = CONFIG["qb_pass"]

# ================= UTILS =================
def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ================= QB API =================
def qb_login(s):
    r = s.post(
        f"{QB_URL}/api/v2/auth/login",
        data={"username": QB_USER, "password": QB_PASS},
    )
    if r.text != "Ok.":
        raise RuntimeError("qBittorrent login failed")

def qb_categories(s):
    return s.get(f"{QB_URL}/api/v2/torrents/categories").json()

def qb_add(s, torrent, category):
    data = {"paused": "true"}
    if category:
        data["category"] = category
    else:
        data["savepath"] = CONFIG["download_path"]

    with open(torrent, "rb") as f:
        s.post(
            f"{QB_URL}/api/v2/torrents/add",
            files={"torrents": f},
            data=data,
        )

def qb_latest(s):
    t = s.get(f"{QB_URL}/api/v2/torrents/info").json()
    t.sort(key=lambda x: x["added_on"], reverse=True)
    return t[0]

def qb_set_location(s, h, path):
    s.post(
        f"{QB_URL}/api/v2/torrents/setLocation",
        data={"hashes": h, "location": path},
    )

def qb_files(s, h):
    return s.get(
        f"{QB_URL}/api/v2/torrents/files",
        params={"hash": h},
    ).json()

def qb_prio(s, h, idx, prio):
    s.post(
        f"{QB_URL}/api/v2/torrents/filePrio",
        data={"hash": h, "id": idx, "priority": prio},
    )

def qb_rename_file(s, h, old, new):
    s.post(
        f"{QB_URL}/api/v2/torrents/renameFile",
        data={"hash": h, "oldPath": old, "newPath": new},
    )

def qb_set_limits(s, h):
    s.post(
        f"{QB_URL}/api/v2/torrents/setDownloadLimit",
        data={"hashes": h, "limit": int(CONFIG["dl_limit"])},
    )
    s.post(
        f"{QB_URL}/api/v2/torrents/setUploadLimit",
        data={"hashes": h, "limit": int(CONFIG["ul_limit"])},
    )

def qb_resume(s, h):
    s.post(
        f"{QB_URL}/api/v2/torrents/resume",
        data={"hashes": h},
    )

def qb_delete(s, h):
    s.post(
        f"{QB_URL}/api/v2/torrents/delete",
        data={"hashes": h, "deleteFiles": "true"},
    )

# ================= PARSING =================
def parse_name(name):
    m = re.search(r"^(.+?)[\s.\(]+(\d{4}).*?(720p|1080p)", name, re.I)
    if not m:
        return None
    title = re.sub(r"[.\[]+", " ", m.group(1)).strip()
    return f"{title} ({m.group(2)}) [{m.group(3).lower()}]"

# ================= HELP =================
def print_help():
    print("""
Torrent CLI – qBittorrent Automation Tool v1.0.0

Usage:
  torrent-cli.exe <torrent_folder> [options]

Arguments:
  <torrent_folder>   Path to folder containing .torrent files

Options:
  --unsafe           Actually add torrents to qBittorrent
                     (without this, nothing is downloaded)
  --verbose          Print detailed logs
  --help             Show this help message

Examples:
  torrent-cli.exe ".\\torrents" --unsafe
  torrent-cli.exe ".\\torrents" --unsafe --verbose

Notes:
- Uses Movies / MOVIES / movies category if it exists
- Otherwise falls back to configured download_path
- Only downloads video + subtitles
""")

# ================= MAIN =================
def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return

    if len(sys.argv) < 2:
        print_help()
        return

    torrent_dir = Path(sys.argv[1])
    verbose = "--verbose" in sys.argv
    unsafe = "--unsafe" in sys.argv
    dry = not unsafe

    processed_file = Path(CONFIG["processed"])
    failed_file = Path(CONFIG["failed"])

    processed = set(processed_file.read_text().splitlines()) if processed_file.exists() else set()

    s = requests.Session()
    qb_login(s)

    cats = qb_categories(s)
    chosen_category = None
    category_path = None

    for c in CONFIG["categories"]:
        if c in cats:
            chosen_category = c
            category_path = cats[c].get("savePath")
            break

    if verbose:
        if chosen_category:
            print(f"Using category '{chosen_category}' → {category_path}")
        else:
            print("No category found, using default path")

    for tfile in torrent_dir.glob("*.torrent"):
        h = sha1(tfile)
        if h in processed:
            if verbose:
                print(f"SKIP: {tfile.name}")
            continue

        try:
            if verbose:
                print(f"Processing: {tfile.name}")

            qb_add(s, tfile, chosen_category)
            time.sleep(1)

            tor = qb_latest(s)

            if chosen_category and category_path:
                qb_set_location(s, tor["hash"], category_path)

            qb_set_limits(s, tor["hash"])

            clean = parse_name(tor["name"])
            if not clean:
                raise RuntimeError("Name parse failed")

            files = qb_files(s, tor["hash"])

            video = max(
                (f for f in files if f["name"].lower().endswith((".mkv", ".mp4"))),
                key=lambda x: x["size"],
            )
            subs = [f for f in files if f["name"].lower().endswith(".srt")]

            for f in files:
                qb_prio(s, tor["hash"], f["index"], 1 if f == video or f in subs else 0)

            folder = clean
            ext = Path(video["name"]).suffix

            qb_rename_file(
                s,
                tor["hash"],
                video["name"],
                f"{folder}/{folder}{ext}",
            )

            for i, sub in enumerate(subs):
                name = "subtitles.srt" if i == 0 else f"subtitles_{i+1}.srt"
                qb_rename_file(
                    s,
                    tor["hash"],
                    sub["name"],
                    f"{folder}/{name}",
                )

            qb_resume(s, tor["hash"])

            processed_file.open("a").write(h + "\n")

            if verbose:
                print(f"SUCCESS: {clean}")

        except Exception as e:
            failed_file.open("a").write(tfile.name + "\n")
            qb_delete(s, tor["hash"])
            print(f"FAILED: {tfile.name} | {e}")

if __name__ == "__main__":
    main()
