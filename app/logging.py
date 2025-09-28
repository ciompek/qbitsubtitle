from datetime import datetime
LOG_FILE = "/opt/subtitles/subtitles.log"

def log_to_file(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
