#!/usr/bin/env python3
import os
from pathlib import Path
import requests
from guessit import guessit
import argparse
from datetime import datetime
import re
import struct

# ---------------- CONFIG ----------------
CONFIG_FILE = "/opt/subtitles/config.env"
LOG_FILE = "/var/log/subtitles.log"

API_KEY = None
DEFAULT_LANG = "en"  # default fallback

# ---------------- LOAD CONFIG ----------------
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        for line in f:
            if line.strip().startswith("API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]
            if line.strip().startswith("DEFAULT_LANG="):
                DEFAULT_LANG = line.strip().split("=", 1)[1]

if not API_KEY:
    print(f"❌ API key is missing in {CONFIG_FILE}. Please run install.sh and provide your API key.")
    exit(1)

HEADERS = {
    "Api-Key": API_KEY,
    "User-Agent": "download-subtitles v1.0",
    "Accept": "application/json"
}

API_URL = "https://api.opensubtitles.com/api/v1/subtitles"
DOWNLOAD_URL = "https://api.opensubtitles.com/api/v1/download"

# ---------------- UTILS ----------------
def log_to_file(method, url, status_code):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {method} {url} => {status_code}\n")

def clean_title(title: str) -> str:
    title = title.replace(".", " ").replace("_", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return title

def build_query(info: dict, video_name: str) -> str:
    title = info.get("title", "")
    season = info.get("season")
    episode = info.get("episode")
    year = info.get("year")
    release_group = info.get("releaseGroup")
    video_resolution = info.get("screen_size")
    source = info.get("source")

    if not release_group:
        m = re.search(r'-\s*([\w\d]+)$', video_name)
        if m:
            release_group = m.group(1)

    query_parts = []
    if year:
        query_parts.append(str(year))
    query_parts.append(title)
    if season and episode:
        query_parts.append(f"S{season:02d}E{episode:02d}")
    if release_group:
        query_parts.append(release_group)
    if video_resolution:
        query_parts.append(video_resolution)
    if source:
        query_parts.append(source)

    query = " ".join(query_parts)
    query = clean_title(query)
    return query

def compute_hash(file_path):
    try:
        longlongformat = '<q'
        bytesize = 8
        f = open(file_path, "rb")
        filesize = os.path.getsize(file_path)
        hash_val = filesize

        if filesize < 65536 * 2:
            raise Exception("File too small to compute hash")

        # first 64KB
        for _ in range(65536 // bytesize):
            buffer = f.read(bytesize)
            (l,) = struct.unpack(longlongformat, buffer)
            hash_val += l
            hash_val &= 0xFFFFFFFFFFFFFFFF

        # last 64KB
        f.seek(max(0, filesize - 65536))
        for _ in range(65536 // bytesize):
            buffer = f.read(bytesize)
            (l,) = struct.unpack(longlongformat, buffer)
            hash_val += l
            hash_val &= 0xFFFFFFFFFFFFFFFF

        f.close()
        return f"{hash_val:016x}"
    except Exception as e:
        print(f"❌ Error computing hash for {file_path}: {e}")
        return None

# ---------------- MAIN FUNCTION ----------------
def download_subtitles(video_path: Path, lang=DEFAULT_LANG, debug=False):
    lang_code = lang.lower()
    srt_path = video_path.with_name(f"{video_path.stem}.{lang_code}.srt")

    # Skip if subtitle already exists
    if srt_path.exists():
        if debug:
            print(f"ℹ️ Subtitle already exists: {srt_path.name}, skipping download.")
        return

    video_name = video_path.stem
    info = guessit(video_name)

    movie_hash = compute_hash(video_path)
    params = {"languages[]": lang, "order_by": "downloads", "order_direction": "desc", "limit": 1}

    if movie_hash:
        params["moviehash"] = movie_hash
        if debug:
            print(f"\n📤 Attempting to download subtitles by movie hash: {movie_hash}")
    else:
        query = build_query(info, video_name)
        params["query"] = query
        if debug:
            print(f"\n📤 Movie hash unavailable, using query: {query}")

    if debug:
        print(f"URL: {API_URL}")
        print(f"Params: {params}")
        print(f"Headers: {HEADERS}")

    r = requests.get(API_URL, headers=HEADERS, params=params)
    log_to_file("GET", API_URL, r.status_code)

    if debug:
        print(f"Status code: {r.status_code}")
        try:
            print(r.json())
        except:
            print(r.text)

    data = r.json().get("data", [])
    if not data and "moviehash" in params:
        # Fallback if hash returns no results
        query = build_query(info, video_name)
        params.pop("moviehash")
        params["query"] = query
        if debug:
            print(f"\n📤 Fallback: no results for hash, using query: {query}")

        r = requests.get(API_URL, headers=HEADERS, params=params)
        log_to_file("GET", API_URL, r.status_code)
        if debug:
            print(f"Status code: {r.status_code}")
            try:
                print(r.json())
            except:
                print(r.text)
        data = r.json().get("data", [])

    if not data:
        print(f"❌ No subtitles found for: {video_name}")
        return

    files = data[0]["attributes"].get("files", [])
    if not files:
        print(f"❌ No subtitle files found for: {video_name}")
        return

    file_id = files[0]["file_id"]

    download_response = requests.post(DOWNLOAD_URL, headers=HEADERS, json={"file_id": file_id})
    log_to_file("POST", DOWNLOAD_URL, download_response.status_code)
    download_json = download_response.json()
    subtitle_file_url = download_json.get("link")
    if not subtitle_file_url:
        print(f"❌ No link to download subtitle for {video_name}")
        return

    r_sub = requests.get(subtitle_file_url)
    log_to_file("GET", subtitle_file_url, r_sub.status_code)

    with open(srt_path, "wb") as f:
        f.write(r_sub.content)
    print(f"✅ Subtitle saved: {srt_path.name}")

# ---------------- ENTRY POINT ----------------
def main():
    parser = argparse.ArgumentParser(description="Download subtitles for movies and TV shows")
    parser.add_argument("folder", help="Path to torrent folder")
    parser.add_argument("-d", "--debug", action="store_true", help="Display requests and responses in console")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"❌ Folder {folder} does not exist.")
        return

    video_extensions = {".mp4", ".mkv", ".avi", ".mov"}
    videos = [f for f in folder.rglob("*") if f.suffix.lower() in video_extensions]

    if not videos:
        print(f"❌ No video files found in {folder}")
        return

    for video in videos:
        print(f"\n🎬 Searching subtitles for: {video.name}")
        download_subtitles(video, lang=DEFAULT_LANG, debug=args.debug)

if __name__ == "__main__":
    main()
