#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
import requests
from guessit import guessit
from qbitsubtitles.utils import compute_hash, build_query, get_first_file_link
from qbitsubtitles.logging import log_to_file
from datetime import datetime

CONFIG_FILE = "/opt/subtitles/config.env"
HEADERS = {}
DEFAULT_LANG = "pl"
API_URL = "https://api.opensubtitles.com/api/v1/subtitles"

# Load config
if not os.path.exists(CONFIG_FILE):
    print(f"❌ Config file not found: {CONFIG_FILE}")
    sys.exit(1)

config = {}
with open(CONFIG_FILE) as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            config[k.strip()] = v.strip()

API_KEY = config.get("API_KEY")
DEFAULT_LANG = config.get("DEFAULT_LANG", "pl")

HEADERS = {
    "Api-Key": API_KEY,
    "User-Agent": "qbitsubtitles v1.0",
    "Accept": "application/json"
}

# Argparse
parser = argparse.ArgumentParser(description="Download subtitles from OpenSubtitles")
parser.add_argument("folder", type=str, help="Folder with videos")
parser.add_argument("--debug", action="store_true")
parser.add_argument("--debug-verbose", action="store_true")
args = parser.parse_args()

DEBUG = args.debug
DEBUG_VERBOSE = args.debug_verbose

def save_subtitle(path, url, method):
    if not url:
        print(f"❌ No download link found")
        return
    r = requests.get(url)
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"✅ Subtitle saved: {path.name} (method: {method})")
    log_to_file(f"{path.name}: subtitle downloaded via {method}")

def download_subtitles(video_path: Path, lang=DEFAULT_LANG):
    srt_path = video_path.with_name(f"{video_path.stem}.{lang}.srt")
    if srt_path.exists():
        if DEBUG:
            print(f"ℹ️ Subtitle already exists: {srt_path.name}, skipping.")
        return

    video_name = video_path.stem
    info = guessit(video_name)
    release_group = info.get("releaseGroup")
    file_release_group = release_group.lower() if release_group else None
    movie_hash = compute_hash(video_path)

    # 1️⃣ Try by hash
    if movie_hash:
        params = {"languages[]": lang, "order_by": "downloads", "order_direction": "desc", "limit": 5, "moviehash": movie_hash}
        if DEBUG:
            print(f"📤 Trying subtitles by hash: {movie_hash}")
        r = requests.get(API_URL, headers=HEADERS, params=params)
        log_to_file(f"GET {r.url} status={r.status_code}")
        data = r.json().get("data", [])
        if data:
            url = get_first_file_link(data[0])
            save_subtitle(srt_path, url, "hash")
            return

    # 2️⃣ Try by query
    query = build_query(info, video_name)
    params = {"languages[]": lang, "order_by": "downloads", "order_direction": "desc", "limit": 5, "query": query}
    if DEBUG:
        print(f"📤 Trying subtitles by query: {query}")
    r = requests.get(API_URL, headers=HEADERS, params=params)
    log_to_file(f"GET {r.url} status={r.status_code}")
    data = r.json().get("data", [])

    # 3️⃣ Release group matching
    release_group_matches = []
    fallback_matches = []

    for d in data:
        slug = d["attributes"].get("slug", "").lower()
        if DEBUG_VERBOSE:
            print(f"📝 Checking slug: '{slug}' against file release group: '{file_release_group}'")
        if file_release_group and file_release_group in slug:
            release_group_matches.append(d)
        else:
            fallback_matches.append(d)

    if release_group_matches:
        chosen_dataset = release_group_matches
        method = "query + string match group"
    elif fallback_matches:
        chosen_dataset = fallback_matches
        method = "general_query"
    else:
        print(f"❌ No subtitles found for {video_name}")
        return

    url = get_first_file_link(chosen_dataset[0])
    save_subtitle(srt_path, url, method)
    if DEBUG:
        print(f"ℹ️ Subtitles method used: {method}")

def process_folder(folder_path: Path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith((".mkv", ".mp4", ".avi")):
                video_file = Path(root) / file
                download_subtitles(video_file)

def main():
    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        print(f"❌ Folder not found: {folder}")
        sys.exit(1)
    process_folder(folder)

if __name__ == "__main__":
    main()
