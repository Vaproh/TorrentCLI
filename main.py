import requests
import sys
import time
import re
import hashlib
from pathlib import Path

# ================= CONFIG =================
CONFIG = {
    "qb_url": "http://localhost:8080",
    "qb_user": "admin",
    "qb_pass": "adminadmin",
    "movie_categories": ["movies", "Movies", "MOVIES"],
    "tv_categories": ["tv", "TV", "Shows", "shows"],
    "fallback_movies": "D:/Movies",
    "fallback_tv": "D:/TV Shows",
    "dl_limit": 1048576,   # bytes/sec
    "ul_limit": 512000,    # bytes/sec
    "processed": "processed_torrents.txt",
    "failed": "failed_torrents.txt",
}

# ================= LOAD CONFIG =================
if Path("config.txt").exists():
    try:
        for line in Path("config.txt").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            CONFIG[k.strip()] = v.strip()
    except Exception as e:
        print(f"Warning: Error loading config.txt: {e}")

QB_URL = CONFIG["qb_url"].rstrip("/")
QB_USER = CONFIG["qb_user"]
QB_PASS = CONFIG["qb_pass"]

# ================= UTILS =================
def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def is_tv(name: str) -> bool:
    return bool(re.search(
        r"(S\d{1,2}E\d{1,2}(?:E\d{1,2})?|\d{1,2}x\d{1,2})",
        name,
        re.I
    ))

def clean_name(name: str) -> str:
    return re.sub(r"[._\[\]\(\)]+", " ", name).strip()

def parse_movie(name: str) -> str:
    cleaned = clean_name(name)
    m = re.search(r"(.+?)\s+((?:19|20)\d{2})\b", cleaned)
    if not m:
        raise ValueError(f"No year found in movie name: {name}")
    return f"{m.group(1)} ({m.group(2)})"

def parse_tv(name: str):
    cleaned = clean_name(name)

    season_ep = re.search(
        r"(S\d{1,2}E\d{1,2}(?:E\d{1,2})?|\d{1,2}x\d{1,2})",
        cleaned,
        re.I
    )
    if not season_ep:
        raise ValueError(f"Could not detect season/episode in: {name}")

    tag = season_ep.group().upper()

    if "X" in tag:
        season_num = tag.split("X")[0].zfill(2)
        ep_tag = f"S{season_num}E{tag.split('X')[1].zfill(2)}"
    else:
        season_match = re.search(r"S(\d{1,2})", tag)
        season_num = season_match.group(1).zfill(2) if season_match else "01"
        ep_tag = tag

    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned)

    split_regex = r"(" + re.escape(season_ep.group()) + r"|" + (year_match.group() if year_match else "NEVER") + r").*"
    show_name = re.sub(split_regex, "", cleaned, flags=re.I).strip()

    show_folder = f"{show_name} ({year_match.group()})" if year_match else show_name
    return show_folder, f"Season {season_num}", ep_tag

def detect_sub_tag(name: str) -> str:
    f = name.lower()
    variants = []

    if "forced" in f:
        variants.append("forced")
    if "sdh" in f:
        variants.append("sdh")
    if "cc" in f or "closed" in f:
        variants.append("cc")

    if re.search(r"\bhi\b|hindi", f):
        lang = "hi"
    elif re.search(r"\bja\b|japanese", f):
        lang = "ja"
    elif re.search(r"\bfr\b|french", f):
        lang = "fr"
    elif re.search(r"\bes\b|spanish", f):
        lang = "es"
    else:
        lang = "en"

    return f"{lang}.{'.'.join(variants)}" if variants else lang

# ================= QB API =================
def qb_login(s: requests.Session):
    r = s.post(f"{QB_URL}/api/v2/auth/login",
               data={"username": QB_USER, "password": QB_PASS})
    if r.text != "Ok.":
        raise RuntimeError("qBittorrent login failed")

def qb_categories(s):
    return s.get(f"{QB_URL}/api/v2/torrents/categories").json()

def qb_get_hashes(s):
    return {t["hash"] for t in s.get(f"{QB_URL}/api/v2/torrents/info").json()}

def qb_add(s, torrent_path: Path, category, fallback):
    data = {"paused": "true"}
    if category:
        data["category"] = category
    else:
        data["savepath"] = fallback

    with open(torrent_path, "rb") as f:
        s.post(f"{QB_URL}/api/v2/torrents/add",
               files={"torrents": (torrent_path.name, f)},
               data=data)

def qb_set_location(s, h, path):
    s.post(f"{QB_URL}/api/v2/torrents/setLocation",
           data={"hashes": h, "location": path})

def qb_files(s, h):
    return s.get(f"{QB_URL}/api/v2/torrents/files",
                 params={"hash": h}).json()

def qb_batch_prio(s, h, ids, prio):
    if not ids:
        return
    s.post(f"{QB_URL}/api/v2/torrents/filePrio",
           data={"hash": h, "id": "|".join(map(str, ids)), "priority": prio})

def qb_rename(s, h, old, new):
    s.post(f"{QB_URL}/api/v2/torrents/renameFile",
           data={"hash": h, "oldPath": old, "newPath": new})

def qb_limits(s, h):
    s.post(f"{QB_URL}/api/v2/torrents/setDownloadLimit",
           data={"hashes": h, "limit": int(CONFIG["dl_limit"])})
    s.post(f"{QB_URL}/api/v2/torrents/setUploadLimit",
           data={"hashes": h, "limit": int(CONFIG["ul_limit"])})

def qb_resume(s, h):
    s.post(f"{QB_URL}/api/v2/torrents/resume", data={"hashes": h})

def qb_delete(s, h):
    s.post(f"{QB_URL}/api/v2/torrents/delete",
           data={"hashes": h, "deleteFiles": "true"})

# ================= MAIN =================
def main():
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print("Usage: torrent_cli.py <torrent_folder> --unsafe [--verbose]")
        return

    if "--unsafe" not in sys.argv:
        print("Dry run blocked. Use --unsafe.")
        return

    torrent_dir = Path(sys.argv[1])
    verbose = "--verbose" in sys.argv

    processed_path = Path(CONFIG["processed"])
    processed = set(processed_path.read_text().splitlines()) if processed_path.exists() else set()

    s = requests.Session()
    qb_login(s)
    cats = qb_categories(s)

    for tfile in torrent_dir.glob("*.torrent"):
        file_hash = sha1(tfile)
        if file_hash in processed:
            continue

        tor_hash = None
        try:
            name = tfile.stem
            tv = is_tv(name)

            if tv:
                category = next((c for c in CONFIG["tv_categories"] if c in cats), None)
                fallback = CONFIG["fallback_tv"]
            else:
                category = next((c for c in CONFIG["movie_categories"] if c in cats), None)
                fallback = CONFIG["fallback_movies"]

            save_path = cats[category]["savePath"] if category else fallback

            before = qb_get_hashes(s)
            qb_add(s, tfile, category, fallback)

            for _ in range(10):
                time.sleep(1)
                after = qb_get_hashes(s)
                diff = after - before
                if diff:
                    tor_hash = diff.pop()
                    break

            if not tor_hash:
                raise RuntimeError("Torrent hash not detected")

            qb_set_location(s, tor_hash, save_path)
            qb_limits(s, tor_hash)

            files = qb_files(s, tor_hash)
            videos = [f for f in files if f["name"].lower().endswith((".mkv", ".mp4", ".avi"))]
            if not videos:
                raise RuntimeError("No video file found")

            main_video = max(videos, key=lambda x: x["size"])
            subs = [f for f in files if f["name"].lower().endswith(".srt")]

            keep_ids = [main_video["index"]] + [s["index"] for s in subs]
            drop_ids = [f["index"] for f in files if f["index"] not in keep_ids]

            qb_batch_prio(s, tor_hash, keep_ids, 1)
            qb_batch_prio(s, tor_hash, drop_ids, 0)

            if tv:
                show, season, ep = parse_tv(name)
                ext = Path(main_video["name"]).suffix
                qb_rename(s, tor_hash, main_video["name"],
                          f"{show}/{season}/{show} - {ep}{ext}")
                for sub in subs:
                    tag = detect_sub_tag(sub["name"])
                    qb_rename(s, tor_hash, sub["name"],
                              f"{show}/{season}/{show} - {ep}.{tag}.srt")
            else:
                movie = parse_movie(name)
                ext = Path(main_video["name"]).suffix
                qb_rename(s, tor_hash, main_video["name"],
                          f"{movie}/{movie}{ext}")
                for sub in subs:
                    tag = detect_sub_tag(sub["name"])
                    qb_rename(s, tor_hash, sub["name"],
                              f"{movie}/{movie}.{tag}.srt")

            qb_resume(s, tor_hash)
            processed_path.open("a").write(file_hash + "\n")

            if verbose:
                print(f"OK: {name}")

        except Exception as e:
            Path(CONFIG["failed"]).open("a").write(f"{tfile.name} | {e}\n")
            if tor_hash:
                qb_delete(s, tor_hash)
            print(f"FAIL: {tfile.name} | {e}")

if __name__ == "__main__":
    main()
