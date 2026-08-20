"""
YouTube Downloader - GUI version (Dark Mode + Format Explorer)
------------------------------------------------------------------
UI:      FreeSimpleGUI (custom dark theme)
Engine:  yt-dlp (handles YouTube bot-detection far better than pytube)

Install dependencies:
    pip install FreeSimpleGUI yt-dlp
    (add --break-system-packages on Linux if needed)

FFMPEG:
    The script first looks for ffmpeg on your system PATH. If it can't find
    it there, it falls back to the hardcoded FFMPEG_FALLBACK_PATH below.
    Edit that constant to match where ffmpeg.exe actually lives on your PC
    (e.g. after downloading a static build and extracting it somewhere).
    ffmpeg is required to merge separate video+audio streams (needed for
    "1080p", "Best Quality", etc.) and to extract mp3 audio.

Workflow:
    1. Paste a YouTube URL.
    2. Click "Fetch Formats" -> queries the video and lists every format
       actually available for that specific video (resolution, fps, codec,
       filesize, whether it already has audio).
    3. Pick a friendly option from the "Quality to download" dropdown
       (built dynamically from what that video actually offers), e.g.:
           - Best Quality (video + audio)
           - 1080p (video + audio, merged)
           - 720p (video + audio, merged)
           - 480p (video + audio, merged)
           - Audio only (mp3)
    4. Choose a save folder, or leave blank to auto-use your Windows
       Downloads folder (~\\Downloads).
    5. Click "Download".
"""

import os
import shutil
import threading
import FreeSimpleGUI as sg
from yt_dlp import YoutubeDL


# --------------------------------------------------------------------------
# ffmpeg location
# --------------------------------------------------------------------------
# Hardcoded fallback path used ONLY if ffmpeg is not found on PATH.
# Change this to wherever ffmpeg.exe actually sits on your machine.
FFMPEG_FALLBACK_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"


def resolve_ffmpeg_path():
    """
    Returns a directory or file path to pass to yt-dlp as 'ffmpeg_location',
    or None if ffmpeg genuinely can't be found anywhere.

    Order of preference:
      1. ffmpeg already on system PATH (shutil.which)
      2. FFMPEG_FALLBACK_PATH hardcoded above, if it exists on disk
    """
    found_on_path = shutil.which("ffmpeg")
    if found_on_path:
        return found_on_path

    if os.path.isfile(FFMPEG_FALLBACK_PATH):
        return FFMPEG_FALLBACK_PATH

    return None


# --------------------------------------------------------------------------
# Dark theme
# --------------------------------------------------------------------------
def setup_dark_theme():
    sg.theme_add_new(
        "YTDark",
        {
            "BACKGROUND": "#181818",
            "TEXT": "#f1f1f1",
            "INPUT": "#272727",
            "TEXT_INPUT": "#f1f1f1",
            "SCROLL": "#3d3d3d",
            "BUTTON": ("#ffffff", "#cc0000"),   # YouTube-red accent buttons
            "PROGRESS": ("#cc0000", "#272727"),
            "BORDER": 1,
            "SLIDER_DEPTH": 0,
            "PROGRESS_DEPTH": 0,
        },
    )
    sg.theme("YTDark")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def get_default_downloads_folder() -> str:
    home = os.path.expanduser("~")
    downloads = os.path.join(home, "Downloads")
    return downloads if os.path.isdir(downloads) else home


def human_size(num_bytes):
    if not num_bytes:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}TB"


def fetch_info(url: str, window: sg.Window):
    """Runs in a thread: pulls format list for the given URL."""
    try:
        with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        window.write_event_value("-INFO-READY-", info)
    except Exception as e:
        window.write_event_value("-INFO-ERROR-", str(e))


def build_table_rows(formats):
    """Raw table rows: every format yt-dlp reports for this video."""
    rows = []
    for f in formats:
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        has_video = vcodec != "none"
        has_audio = acodec != "none"
        kind = "video+audio" if has_video and has_audio else (
            "video only" if has_video else "audio only"
        )
        res = f.get("resolution") or (f"{f.get('height')}p" if f.get("height") else "-")
        rows.append([
            f.get("format_id", "-"),
            f.get("ext", "-"),
            str(res),
            str(f.get("fps") or "-"),
            kind,
            human_size(f.get("filesize") or f.get("filesize_approx")),
            f.get("format_note") or "",
        ])
    return rows


def build_quality_options(formats):
    """
    Build a friendly dropdown: label -> yt-dlp format selector string.
    Only offers resolutions that actually exist for this video.
    """
    options = {}

    heights = sorted(
        {f.get("height") for f in formats if f.get("height") and f.get("vcodec") != "none"},
        reverse=True,
    )

    options["Best Quality (video + audio, merged)"] = "bestvideo+bestaudio/best"

    for h in heights:
        label = f"{h}p (video + audio, merged)"
        options[label] = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"

    # Progressive (already-merged) formats some videos still offer
    for f in formats:
        if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("height"):
            label = f"{f['height']}p (pre-merged, single file, id {f['format_id']})"
            options[label] = f["format_id"]

    options["Audio only (mp3)"] = "bestaudio/best"

    return options


def download_worker(url: str, output_dir: str, format_selector: str, is_audio: bool, window: sg.Window):
    os.makedirs(output_dir, exist_ok=True)

    def progress_hook(d):
        if d["status"] == "downloading":
            pct_str = d.get("_percent_str", "0%").strip()
            speed = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()
            try:
                pct_num = float(pct_str.replace("%", ""))
            except ValueError:
                pct_num = 0
            window.write_event_value("-PROGRESS-", (pct_num, f"{pct_str}  |  {speed}  |  ETA {eta}"))
        elif d["status"] == "finished":
            window.write_event_value("-STATUS-", "Merging/processing file...")

    ydl_opts = {
        "format": format_selector,
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
    }

    ffmpeg_path = resolve_ffmpeg_path()
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    if is_audio:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        ydl_opts["merge_output_format"] = "mp4"

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        window.write_event_value("-DONE-", output_dir)
    except Exception as e:
        window.write_event_value("-ERROR-", str(e))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    setup_dark_theme()
    default_downloads = get_default_downloads_folder()

    table_headings = ["ID", "Ext", "Resolution", "FPS", "Type", "Size", "Note"]

    layout = [
        [sg.Text("YouTube Downloader", font=("Segoe UI", 18, "bold"), text_color="#ff4d4d")],
        [sg.HorizontalSeparator()],

        [sg.Text("Video URL:", size=(10, 1)),
         sg.Input(key="-URL-", expand_x=True),
         sg.Button("Fetch Formats", key="-FETCH-")],

        [sg.Text("", key="-TITLE-", font=("Segoe UI", 10, "italic"), text_color="#cccccc")],

        [sg.Text("Available formats for this video:", font=("Segoe UI", 9, "bold"))],
        [sg.Table(
            values=[],
            headings=table_headings,
            key="-TABLE-",
            auto_size_columns=False,
            col_widths=[8, 6, 11, 6, 12, 8, 14],
            justification="left",
            num_rows=8,
            expand_x=True,
            background_color="#272727",
            text_color="#f1f1f1",
            alternating_row_color="#202020",
            header_background_color="#cc0000",
            header_text_color="white",
        )],

        [sg.Text("Quality to download:", size=(15, 1)),
         sg.Combo([], key="-QUALITY-", readonly=True, expand_x=True)],

        [sg.Text("Save to:", size=(15, 1)),
         sg.Input(key="-FOLDER-", expand_x=True),
         sg.FolderBrowse("Browse", target="-FOLDER-")],
        [sg.Text(f"(Leave blank to use: {default_downloads})",
                 font=("Segoe UI", 8), text_color="#888888")],

        [sg.Button("Download", key="-DOWNLOAD-", disabled=True), sg.Button("Exit")],
        [sg.ProgressBar(100, orientation="h", size=(45, 20), key="-PROGBAR-",
                         bar_color=("#cc0000", "#272727"))],
        [sg.Text("", key="-STATUS-", size=(70, 1), text_color="#cccccc")],
    ]

    window = sg.Window("YouTube Downloader (yt-dlp)", layout, finalize=True)

    ffmpeg_path = resolve_ffmpeg_path()
    if ffmpeg_path:
        window["-STATUS-"].update(f"ffmpeg found: {ffmpeg_path}")
    else:
        window["-STATUS-"].update(
            "⚠️ ffmpeg not found on PATH or at FFMPEG_FALLBACK_PATH — "
            "merging/mp3 extraction will fail. Edit FFMPEG_FALLBACK_PATH in the script."
        )

    quality_map = {}  # label -> (format_selector, is_audio)

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Exit"):
            break

        if event == "-FETCH-":
            url = values["-URL-"].strip()
            if not url:
                sg.popup_error("Please enter a YouTube URL first.")
                continue
            window["-STATUS-"].update("Fetching available formats...")
            window["-FETCH-"].update(disabled=True)
            window["-TABLE-"].update(values=[])
            window["-QUALITY-"].update(values=[])
            window["-DOWNLOAD-"].update(disabled=True)
            threading.Thread(target=fetch_info, args=(url, window), daemon=True).start()

        elif event == "-INFO-READY-":
            info = values[event]
            formats = info.get("formats", [])
            window["-TITLE-"].update(f"🎬 {info.get('title', 'Unknown title')}  "
                                      f"({info.get('duration', '?')}s)")
            window["-TABLE-"].update(values=build_table_rows(formats))

            options = build_quality_options(formats)
            quality_map = {
                label: (selector, "Audio only" in label)
                for label, selector in options.items()
            }
            window["-QUALITY-"].update(values=list(options.keys()),
                                        value=list(options.keys())[0])
            window["-STATUS-"].update("Formats loaded. Pick a quality and download.")
            window["-FETCH-"].update(disabled=False)
            window["-DOWNLOAD-"].update(disabled=False)

        elif event == "-INFO-ERROR-":
            window["-STATUS-"].update("❌ Could not fetch formats.")
            window["-FETCH-"].update(disabled=False)
            sg.popup_error("Failed to fetch video info:", values[event])

        elif event == "-DOWNLOAD-":
            url = values["-URL-"].strip()
            folder = values["-FOLDER-"].strip()
            quality_label = values["-QUALITY-"]

            if not url:
                sg.popup_error("Please enter a YouTube URL first.")
                continue
            if not quality_label or quality_label not in quality_map:
                sg.popup_error("Please click 'Fetch Formats' and choose a quality first.")
                continue

            if not folder:
                folder = default_downloads
                window["-FOLDER-"].update(folder)

            format_selector, is_audio = quality_map[quality_label]

            window["-STATUS-"].update("Starting download...")
            window["-PROGBAR-"].update(0)
            window["-DOWNLOAD-"].update(disabled=True)

            threading.Thread(
                target=download_worker,
                args=(url, folder, format_selector, is_audio, window),
                daemon=True,
            ).start()

        elif event == "-PROGRESS-":
            pct_num, status_text = values[event]
            window["-PROGBAR-"].update(pct_num)
            window["-STATUS-"].update(status_text)

        elif event == "-STATUS-":
            window["-STATUS-"].update(values[event])

        elif event == "-DONE-":
            window["-PROGBAR-"].update(100)
            window["-STATUS-"].update(f"✅ Done! Saved to: {values[event]}")
            window["-DOWNLOAD-"].update(disabled=False)
            sg.popup("Download complete!", f"Saved to:\n{values[event]}")

        elif event == "-ERROR-":
            window["-STATUS-"].update("❌ Download failed.")
            window["-DOWNLOAD-"].update(disabled=False)
            sg.popup_error("Download failed:", values[event])

    window.close()


if __name__ == "__main__":
    main()
