#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from pathlib import Path
import requests
from guessit import guessit
from qbitsubtitles.utils import compute_hash, build_query, get_first_file_link
from qbitsubtitles.logging import log_to_file

CONFIG_FILE = "/opt/subtitles/config.env"
HEADERS = {}
DEFAULT_LANG = "pl"
API_URL = "https://api.opensubtitles.com/api/v1/subtitles"
DOWNLOAD_URL = "https://api.opensubtitles.com/api/v1/download"

# Load config
if not os.path.exists(CONFIG_FILE):
    print(f"❌ Config file not found: {CONFIG_FILE}")
    sys.exit(1)

config = {}
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if "=" in line and not line.lstrip().startswith("#"):
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

def normalize(s):
    """Normalize strings for robust comparison."""
    if not s:
        return ""
    return s.replace('.', '').replace('-', '').replace('_', '').replace(' ', '').lower()

def save_subtitle(path, url, method):
    if not url:
        print(f"❌ No download link found")
        return False
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            if DEBUG or DEBUG_VERBOSE:
                print(f"❌ Download returned HTTP {r.status_code} for {url}")
            log_to_file(f"Failed download {path.name} url={url} status={r.status_code}")
            return False
        # avoid saving HTML pages
        start = r.content[:200].decode(errors="ignore").lower()
        if start.strip().startswith("<!doctype") or "<html" in start:
            if DEBUG or DEBUG_VERBOSE:
                print("❌ Received HTML instead of subtitle content, skipping.")
            log_to_file(f"Received HTML when fetching subtitle for {path.name} url={url}")
            return False
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"✅ Subtitle saved: {path.name} (method: {method})")
        log_to_file(f"{path.name}: subtitle downloaded via {method}")
        return True
    except Exception as e:
        print(f"❌ Exception while downloading subtitle: {e}")
        log_to_file(f"Exception while downloading subtitle {path.name}: {e}")
        return False

def select_best_from_results(data, file_release_group, headers, download_url):
    """
    Select best subtitle entry from API results:
    - Prefer first entry whose normalized slug contains file_release_group and has files with a valid link.
    - Otherwise return first entry that has files (fallback).
    - If chosen entry has no download link, try to find any entry in list that yields a valid link.
    Returns tuple (chosen_entry, method, link) or (None, None, None)
    """
    if not data:
        return None, None, None

    file_rg_norm = normalize(file_release_group)
    first_fallback = None
    # First pass: try to find direct release_group match (and ensure it has files)
    for idx, item in enumerate(data, start=1):
        attrs = item.get("attributes", {}) or {}
        slug = normalize(attrs.get("slug", ""))
        files = attrs.get("files", []) or []
        if DEBUG_VERBOSE:
            print(f"📝 Result {idx}: slug='{slug}' files={len(files)}")
            log_to_file(f"Result {idx} slug='{slug}' files={len(files)}")
        if files and first_fallback is None:
            first_fallback = item
        if file_rg_norm and file_rg_norm in slug and files:
            # Try to get download link for this item
            link = None
            try:
                link = get_first_file_link(item, headers, download_url)
            except Exception as e:
                if DEBUG_VERBOSE:
                    print(f"⚠️ get_first_file_link exception: {e}")
                log_to_file(f"get_first_file_link exception: {e}")
            if link:
                return item, "query + string match group", link
            else:
                if DEBUG_VERBOSE:
                    print("⚠️ Matched slug but couldn't obtain file link; will try other entries.")
                log_to_file("Matched slug but no link returned")
                # continue searching for other matches / fallbacks

    # Second pass: use first fallback (first entry with files) and try to get link
    if first_fallback:
        try:
            link = get_first_file_link(first_fallback, headers, download_url)
        except Exception as e:
            link = None
            if DEBUG_VERBOSE:
                print(f"⚠️ get_first_file_link exception for fallback: {e}")
            log_to_file(f"get_first_file_link exception for fallback: {e}")
        if link:
            return first_fallback, "general_query", link

    # Last resort: try any entry in data to find a working link
    for idx, item in enumerate(data, start=1):
        attrs = item.get("attributes", {}) or {}
        files = attrs.get("files", []) or []
        if not files:
            continue
        try:
            link = get_first_file_link(item, headers, download_url)
        except Exception as e:
            link = None
            if DEBUG_VERBOSE:
                print(f"⚠️ get_first_file_link exception while scanning: {e}")
            log_to_file(f"get_first_file_link exception while scanning: {e}")
        if link:
            # determine method label: if slug contains file_release_group label as match, mark accordingly
            slug = normalize(attrs.get("slug", ""))
            method = "query + string match group" if (file_rg_norm and file_rg_norm in slug) else "general_query"
            return item, method, link

    return None, None, None

def download_subtitles(video_path: Path, lang=DEFAULT_LANG):
    srt_path = video_path.with_name(f"{video_path.stem}.{lang}.srt")
    if srt_path.exists():
        if DEBUG:
            print(f"ℹ️ Subtitle already exists: {srt_path.name}, skipping.")
        return

    video_name = video_path.stem
    info = guessit(video_name)
    # <-- FIX: use 'release_group' key from guessit -->
    release_group = info.get("release_group")
    file_release_group = release_group or None
    file_release_group_norm = normalize(file_release_group)
    movie_hash = compute_hash(video_path)

    if DEBUG_VERBOSE:
        print(f"\n🎬 Processing: {video_name}")
        print(f"  guessit info: {info}")
        print(f"  detected release_group: '{release_group}' normalized: '{file_release_group_norm}'")
        log_to_file(f"Processing {video_name}, release_group='{release_group}'")

    # 1) Try by movie hash
    if movie_hash:
        params = {
            "moviehash": movie_hash,
            "languages[]": lang,
            "order_by": "downloads",
            "order_direction": "desc",
            "limit": 10
        }
        if DEBUG:
            print(f"📤 Trying subtitles by hash: {movie_hash}")
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
            log_to_file(f"GET {r.url} status={r.status_code}")
            if r.status_code == 200:
                data = r.json().get("data", []) or []
            else:
                data = []
                if DEBUG_VERBOSE:
                    print(f"⚠️ Hash search returned HTTP {r.status_code}")
                log_to_file(f"Hash search HTTP {r.status_code} for {video_name}")
        except Exception as e:
            data = []
            log_to_file(f"Exception during hash search: {e}")
            if DEBUG_VERBOSE:
                print(f"⚠️ Exception during hash search: {e}")

        # choose first usable entry from hash results
        if data:
            # try to find first item with working link
            for item in data:
                attrs = item.get("attributes", {}) or {}
                files = attrs.get("files", []) or []
                if not files:
                    continue
                try:
                    link = get_first_file_link(item, HEADERS, DOWNLOAD_URL)
                except Exception as e:
                    link = None
                    if DEBUG_VERBOSE:
                        print(f"⚠️ get_first_file_link exception (hash results): {e}")
                    log_to_file(f"get_first_file_link exception (hash results): {e}")
                if link:
                    saved = save_subtitle(srt_path, link, "hash")
                    if saved:
                        return
            # if none of hash results yielded a link, continue to query
            if DEBUG_VERBOSE:
                print("⚠️ Hash results found but none provided usable file link, continuing to query search.")
            log_to_file("Hash results had no usable file link")

    # 2) Try by query (name)
    query = build_query(info, video_name)
    params = {
        "query": query,
        "languages[]": lang,
        "order_by": "downloads",
        "order_direction": "desc",
        "limit": 20
    }
    if DEBUG:
        print(f"📤 Trying subtitles by query: {query}")
    try:
        r = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        log_to_file(f"GET {r.url} status={r.status_code}")
        if r.status_code == 200:
            data = r.json().get("data", []) or []
        else:
            data = []
            if DEBUG_VERBOSE:
                print(f"⚠️ Query search returned HTTP {r.status_code}")
            log_to_file(f"Query search HTTP {r.status_code} for {video_name}")
    except Exception as e:
        data = []
        log_to_file(f"Exception during query search: {e}")
        if DEBUG_VERBOSE:
            print(f"⚠️ Exception during query search: {e}")

    if DEBUG_VERBOSE:
        print(f"🔹 Received {len(data)} results from OpenSubtitles for query '{query}'")
        log_to_file(f"Received {len(data)} results for query '{query}'")

    # select best entry using release group preference
    chosen_item, method, link = select_best_from_results(data, file_release_group, HEADERS, DOWNLOAD_URL)

    if not chosen_item:
        print(f"❌ No subtitles found for {video_name}")
        log_to_file(f"No subtitles found for {video_name}")
        return

    # if we already have link from selection, try saving; otherwise try obtain link now
    if not link:
        try:
            link = get_first_file_link(chosen_item, HEADERS, DOWNLOAD_URL)
        except Exception as e:
            link = None
            if DEBUG_VERBOSE:
                print(f"⚠️ get_first_file_link exception for chosen item: {e}")
            log_to_file(f"get_first_file_link exception for chosen item: {e}")

    if not link:
        # as a last effort, try to find any working link in all results
        if DEBUG_VERBOSE:
            print("⚠️ Chosen item had no link, scanning results for any working file...")
        for item in data:
            try:
                link = get_first_file_link(item, HEADERS, DOWNLOAD_URL)
            except Exception:
                link = None
            if link:
                # update method depending on whether slug matched
                attrs = item.get("attributes", {}) or {}
                slug = normalize(attrs.get("slug", ""))
                method = "query + string match group" if (file_release_group and file_release_group_norm in slug) else "general_query"
                chosen_item = item
                break

    if not link:
        print(f"❌ No downloadable subtitle files found for {video_name}")
        log_to_file(f"No downloadable subtitle files found for {video_name}")
        return

    saved = save_subtitle(srt_path, link, method)
    if saved:
        if DEBUG:
            print(f"ℹ️ Subtitles method used: {method}")
        log_to_file(f"{video_name}: subtitles downloaded via {method}")
    else:
        print(f"❌ Failed to save subtitles for {video_name}")
        log_to_file(f"{video_name}: failed to save subtitles via {method}")

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
