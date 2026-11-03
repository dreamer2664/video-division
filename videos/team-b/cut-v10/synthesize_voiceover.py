#!/usr/bin/env python3
"""Networked, one-time Edge-TTS synthesis. The rendered film consumes committed outputs offline."""
import asyncio, hashlib, json, os
from pathlib import Path
import edge_tts

HERE = Path(__file__).resolve().parent
TEXT = HERE / "audio/narration_text.txt"
MP3 = HERE / "audio/narration_source.mp3"
TELEMETRY = HERE / "timing/word_telemetry.json"
VTT = HERE / "timing/word_telemetry_source.vtt"
VOICE = "en-US-ChristopherNeural"
RATE = "-12%"
PITCH = "-4Hz"

async def main():
    text = TEXT.read_text(encoding="utf-8").strip()
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
    audio = bytearray()
    words = []
    async for item in comm.stream():
        if item["type"] == "audio":
            audio.extend(item["data"])
        elif item["type"] == "WordBoundary":
            words.append({
                "text": item["text"],
                "offset_100ns": int(item["offset"]),
                "duration_100ns": int(item["duration"]),
                "start_s": item["offset"] / 10_000_000.0,
                "end_s": (item["offset"] + item["duration"]) / 10_000_000.0,
            })
    if not audio or not words:
        raise RuntimeError("Edge-TTS returned no audio or no WordBoundary telemetry")
    MP3.write_bytes(audio)
    payload = {
        "voice": VOICE,
        "rate": RATE,
        "pitch": PITCH,
        "boundary_mode": "WordBoundary",
        "source_text": str(TEXT.relative_to(HERE)),
        "source_text_sha256": hashlib.sha256(TEXT.read_bytes()).hexdigest(),
        "source_mp3": str(MP3.relative_to(HERE)),
        "source_mp3_sha256": hashlib.sha256(MP3.read_bytes()).hexdigest(),
        "words": words,
    }
    TELEMETRY.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["WEBVTT", ""]
    for i, w in enumerate(words, 1):
        st, en = w["start_s"], w["end_s"]
        def stamp(t):
            ms = round(t * 1000)
            h, ms = divmod(ms, 3_600_000); m, ms = divmod(ms, 60_000); s, ms = divmod(ms, 1000)
            return f"{h:02}:{m:02}:{s:02}.{ms:03}"
        lines += [str(i), f"{stamp(st)} --> {stamp(en)}", w["text"], ""]
    VTT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {len(words)} WordBoundary events, {len(audio)} MP3 bytes, final event ends {words[-1]['end_s']:.3f}s")

if __name__ == "__main__":
    asyncio.run(main())
