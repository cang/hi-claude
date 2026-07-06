#!/usr/bin/env python3
"""Fetch a YouTube video's metadata + transcript, driven by yt-dlp.

Usage: python driver.py <youtube-url-or-id> [preferred-langs]
  preferred-langs: comma-separated, default "vi,en"

Prints one JSON object to stdout:
{
  "video_id", "title", "uploader", "duration_sec", "upload_date",
  "description", "transcript_lang", "transcript_is_auto", "transcript"
}
If no captions exist, "transcript" is null, exit code 2, and "note"
explains why (caller should summarize from title+description only).
Exit code 1 means yt-dlp itself failed (bad URL, private/deleted video).

Key trick: YouTube throttles (HTTP 429) requests for *translated*
auto-captions (tlang=..) far more aggressively than requests for the
track in its own original/native language. So this script never asks
yt-dlp/YouTube to translate - it always pulls the native-language
track (whatever language that is) and lets the caller's LLM read/
translate/summarize it. Native tracks are identified by their
timedtext URL having no "tlang=" query param.
"""
import sys
import json
import subprocess
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def run_ytdlp_json(url):
    proc = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "-j", "--skip-download", "--no-warnings", url],
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {proc.stderr.strip()[-800:]}")
    return json.loads(proc.stdout)


def pick_native_track(caption_dict, preferred_langs=("vi", "en")):
    """Return (lang, json3_url) for a native (non-translated) track.

    Prefers preferred_langs when a native track exists in one of them,
    otherwise falls back to whichever native track is found first.
    A track is "native" if its URL has no tlang= param - translated
    tracks are excluded because YouTube 429s translation requests hard.
    """
    native = {}
    for lang, fmts in (caption_dict or {}).items():
        for f in fmts:
            if f.get("ext") == "json3" and "tlang=" not in (f.get("url") or ""):
                native[lang] = f["url"]
                break
    for lang in preferred_langs:
        if lang in native:
            return lang, native[lang]
    for lang, url in native.items():
        return lang, url
    return None, None


def json3_to_text(json3_bytes):
    data = json.loads(json3_bytes)
    parts = []
    for ev in data.get("events", []):
        for seg in ev.get("segs", []) or []:
            t = seg.get("utf8", "")
            if t:
                parts.append(t)
    text = "".join(parts)
    return "\n".join(line.strip() for line in text.split("\n") if line.strip())


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("Usage: python driver.py <youtube-url-or-id> [preferred-langs]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    preferred_langs = tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ("vi", "en")
    info = run_ytdlp_json(url)

    result = {
        "video_id": info.get("id"),
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration_sec": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "description": (info.get("description") or "")[:2000],
        "transcript_lang": None,
        "transcript_is_auto": None,
        "transcript": None,
    }

    lang, track_url = pick_native_track(info.get("subtitles"), preferred_langs)
    is_auto = False
    if not track_url:
        lang, track_url = pick_native_track(info.get("automatic_captions"), preferred_langs)
        is_auto = True

    if not track_url:
        result["note"] = "No captions/subtitles available for this video (manual or auto)."
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(2)

    raw = fetch_url(track_url)
    text = json3_to_text(raw)

    result["transcript_lang"] = lang
    result["transcript_is_auto"] = is_auto
    result["transcript"] = text
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
