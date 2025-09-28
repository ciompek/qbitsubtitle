import re
import requests

def compute_hash(file_path):
    """Compute a simple hash for OpenSubtitles."""
    try:
        with open(file_path, "rb") as f:
            data = f.read(64 * 1024)
            return f"{sum(data):x}"
    except Exception:
        return None

def clean_title(title):
    title = re.sub(r"[^A-Za-z0-9 ]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def build_query(info, video_name):
    """Build a query string based on guessit info."""
    parts = []
    title = clean_title(info.get("title", video_name))
    parts.append(title)
    year = info.get("year")
    if year:
        parts.insert(0, str(year))
    season = info.get("season")
    episode = info.get("episode")
    if season and episode:
        parts.append(f"S{season:02d}E{episode:02d}")
    resolution = info.get("screen_size")
    if resolution:
        parts.append(resolution)
    source = info.get("source")
    if source:
        parts.append(source)
    release_group = info.get("releaseGroup")
    if release_group:
        parts.append(release_group)
    return " ".join(parts)

def get_first_file_link(subtitle_data, headers, download_url):
    """Get the download link of the first subtitle file."""
    files = subtitle_data["attributes"].get("files", [])
    if not files:
        return None
    file_id = files[0]["file_id"]
    r = requests.post(download_url, headers=headers, json={"file_id": file_id})
    return r.json().get("link")
