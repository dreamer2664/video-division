#!/usr/bin/env python3
"""ElevenLabs voice generation for the 15 s counter proof (voice first).

Reads ELEVENLABS_API_KEY from the environment (NEVER committed, NEVER echoed).
Discovers voices (GET /v1/voices, 0 chars), picks a deep male documentary
voice, synthesises the 15 s proof script with per-word timestamps
(POST /v1/text-to-speech/{voice_id}/with-timestamps).

Saves: audio/15s_proof/voice.mp3  +  audio/15s_proof/word_timestamps.json
Logs every call to research/ELEVENLABS-LEDGER.md under the 'tally' section.
Character cost counted against this round's 1,500-char cap.
"""

import json, os, sys, base64, urllib.request, urllib.error, datetime as dt

KEY = os.environ.get("ELEVENLABS_API_KEY")
if not KEY:
    sys.exit("ELEVENLABS_API_KEY not set in environment")

BASE = "https://api.elevenlabs.io"
SCRIPT = "What if I never slept again? I stayed awake for you, hour by hour. One counter. One number that never stops."
MODEL = "eleven_multilingual_v2"
STABILITY = 0.35

LEDGER = "/home/user/video-division/research/ELEVENLABS-LEDGER.md"
ROUND_CAP = 1500

def now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

def ledger_append(rows):
    with open(LEDGER) as f:
        existing = f.read()
    marker = "## tally\n"
    if marker not in existing:
        existing += "\n---\n\n## tally\n"
    head, _, _ = existing.partition(marker)
    lines = [marker,
             "# ElevenLabs API ledger — tally voice generation\n",
             f"Round limit: **{ROUND_CAP} text characters maximum.** Reserve characters before each POST and count every attempted synthesis against the limit, even if the server result is ambiguous. No credentials belong in this file.\n",
             "\n| UTC | Request | Characters reserved | Status | Notes |",
             "|---|---|---:|---|---|"]
    lines += [f"| {r['utc']} | {r['request']} | {r['chars']} | {r['status']} | {r['notes']} |" for r in rows]
    lines += ["", f"**Total reserved this round (tally): {sum(r['chars'] for r in rows)} / {ROUND_CAP}.**", ""]
    with open(LEDGER, "w") as f:
        f.write(head + "\n".join(lines) + "\n")

def get(path):
    req = urllib.request.Request(BASE + path, headers={"xi-api-key": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()

def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"xi-api-key": KEY,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)

def words_from_alignment(alignment, script):
    """Rebuild per-word [start, end] seconds from character alignment."""
    chars = alignment["characters"]
    cstart = alignment["character_start_times_seconds"]
    cend = alignment["character_end_times_seconds"]
    # walk the script, matching non-space characters in order
    words = []
    i = 0  # index into chars
    for word in script.split(" "):
        # skip leading spaces in the alignment char stream
        while i < len(chars) and chars[i] == " ":
            i += 1
        if i >= len(chars):
            break
        start = cstart[i]
        last = i
        for ch in word:
            # advance to next non-space char
            while i < len(chars) and chars[i] == " ":
                i += 1
            if i >= len(chars):
                break
            last = i
            i += 1
        end = cend[last]
        words.append({"word": word, "start": start, "end": end})
    return words

def main():
    rows = []
    status, body = get("/v1/voices")
    voices = json.loads(body) if status == 200 else {}
    vs = voices.get("voices", [])
    print(f"[voices] {status} voices={len(vs)}")
    rows.append({"utc": now_utc(), "request": "GET /v1/voices", "chars": 0,
                 "status": str(status),
                 "notes": "Discover available voices with tally key"})

    preferred = ["Roger", "Brian", "Bill"]
    chosen = None
    for p in preferred:
        for v in vs:
            if v.get("name") == p:
                chosen = v; break
        if chosen: break
    if not chosen:
        for v in vs:
            if v.get("category") == "premade" and v.get("labels", {}).get("gender") == "male":
                chosen = v; break
    if not chosen and vs:
        chosen = vs[0]
    voice_id = chosen["voice_id"]
    voice_name = chosen.get("name")
    print(f"[voice] selected {voice_name} ({voice_id})")

    chars = len(SCRIPT)
    status, body, headers = post(
        f"/v1/text-to-speech/{voice_id}/with-timestamps",
        {"text": SCRIPT, "model_id": MODEL,
         "voice_settings": {"stability": STABILITY, "similarity_boost": 0.78},
         "seed": 20261101})
    print(f"[tts] {status} bytes={len(body)}")
    cost_header = headers.get("x-characters") or headers.get("character-cost")
    print(f"[tts] char cost header={cost_header}")
    rows.append({"utc": now_utc(),
                 "request": f"POST /v1/text-to-speech/{voice_id}/with-timestamps",
                 "chars": chars, "status": str(status),
                 "notes": f"15s proof script, model {MODEL}, stability {STABILITY}, voice {voice_name}"})

    ledger_append(rows)

    if status != 200:
        print("TTS failed:", body[:500])
        sys.exit(1)

    resp = json.loads(body)
    audio_b64 = resp.get("audio_base64")
    alignment = resp.get("alignment")
    if not audio_b64:
        sys.exit("No audio_base64 in response")

    out_dir = "/home/user/video-division/audio/15s_proof"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/voice.mp3", "wb") as f:
        f.write(base64.b64decode(audio_b64))
    print(f"[saved] {out_dir}/voice.mp3 ({len(base64.b64decode(audio_b64))} bytes)")

    words = words_from_alignment(alignment, SCRIPT)
    with open(f"{out_dir}/word_timestamps.json", "w") as f:
        json.dump({"script": SCRIPT, "words": words}, f, indent=2)
    print(f"[saved] {out_dir}/word_timestamps.json ({len(words)} words)")
    dur = words[-1]["end"] if words else 0
    print(f"[audio] duration ≈ {dur:.2f}s")
    for w in words:
        print(f"   {w['word']!r:14} {w['start']:6.3f} -> {w['end']:6.3f}")

if __name__ == "__main__":
    main()
