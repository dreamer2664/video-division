# ELEVENLABS API LEDGER — all agents, shared 70,000-character monthly pool

Keys are never recorded here. One section per agent per round.

---

## reel

# ElevenLabs API ledger — reel voice research

Round limit: **1,200 text characters maximum**. Reserve characters before each POST and count every attempted synthesis against the limit, even if the server result is ambiguous. No credentials belong in this file. The benchmark passage is `ab-reel/benchmark.txt`.

| UTC | Request | Characters reserved | Status | Notes |
|---|---|---:|---|---|
| 2026-11-01T14:38:44+00:00 | GET `/v1/voices` | 0 | 200 | Discover an available premade reference voice. |
| 2026-11-01T14:39:18+00:00 | POST `/v1/text-to-speech/{voice_id}/with-timestamps` | 201 | 200 | One benchmark passage, model `eleven_multilingual_v2`, premade male Roger; the reservation is counted even if the outcome is unknown. |

**Total reserved this round: 201 / 1,200.** Account monthly usage is shared with others and is not assumed to be exclusively available to this experiment.

---

## grade

# ElevenLabs API Character Ledger

Shared accounting ledger for division ElevenLabs TTS synthesis calls (`70,000` characters/month division pool across 7 keys; `10,000` characters/month per key; `1,200`-character cap for the Wave-6 voice quality research order).

> **Security rule:** Never commit, log, or paste API keys (`sk_...`) anywhere in this repository, commit messages, or PR descriptions. All benchmark outputs are committed under `research/ab-grade/audio/` so `python3 research/build_ab_benchmark.py` runs **100% offline at `0` character cost**.

## Call Log

| Date (UTC) | Agent | Model | Characters | Voice (`voice_id`) | Request ID | Purpose |
| :--- | :--- | :--- | ---: | :--- | :--- | :--- |
| `2026-11-01` | `grade` | `n/a (GET /v1/user/subscription)` | `0` | `n/a` | `metadata` | Pre-experiment character quota check (`0 / 10,000` initial). |
| `2026-11-01` | `grade` | `n/a (GET /v1/voices)` | `0` | `n/a` | `metadata` | Enumerate premade deep male documentary voices (`Brian`, `Bill`, `Daniel`, `Roger`). |
| `2026-11-01` | `grade` | `eleven_multilingual_v2` | `191` | `Brian` (`nPczCjzI2devNBz1zQrb`) | `JOVRzJfD6WGGAzH8xogy` | High-stability A/B control (`stability=0.78, similarity_boost=0.75, style=0.00, speed=0.90, seed=20261101`) on exact 3 `v07` (*MARK SIX*) narration sentences (`Turn 06 + Turn 09 + Turn 12`). Saved to `research/ab-grade/audio/sources/el_v2_brian_highstab.mp3`. |
| `2026-11-01` | `grade` | `eleven_multilingual_v2` | `191` | `Brian` (`nPczCjzI2devNBz1zQrb`) | `EqSN1MlTZX2lENRQIykF` | Primary expressive baritone A/B test (`stability=0.35, similarity_boost=0.78, style=0.18, speed=0.89, seed=20261101`) on the identical 191-character 3-sentence `v07` script against local `edge-tts` + `vocal_chain.py`. Saved to `research/ab-grade/audio/sources/el_v2_brian_expressive.mp3`. |
| `2026-11-01` | `grade` | `eleven_multilingual_v2` | `194` | `Bill` (`pqHfZKP75CvOlQylNhV4`) | `4aNBHrVTgYzSLFKfRc7J` | Weathered documentary timbre + punctuation-directed pause test (`stability=0.38, similarity_boost=0.80, style=0.15, speed=0.88, seed=20261101`) on the same 3 `v07` sentences with ellipsis (`...`) and em-dash (`—`) clause cues. Saved to `research/ab-grade/audio/sources/el_v2_bill_documentary.mp3`. |
| `2026-11-01` | `grade` | `n/a (GET /v1/user/subscription)` | `0` | `n/a` | `metadata` | Post-experiment server verification (`576 / 10,000` cumulative billed). |

## Round Summary (`grade` · `grade/voice-imaging`)

- **Total paid TTS API calls:** `3` (plus `0`-character metadata checks to `GET /v1/voices` and `GET /v1/user/subscription`)
- **Total characters billed (verified via `character-cost` header & `/v1/user/subscription`):** **`576 / 1,200`** (`48.0%` of round cap; `624` characters unspent)
- **Remaining monthly balance on assigned key:** **`9,424 / 10,000`** characters

---

## tally

# ElevenLabs API ledger — tally voice generation

Round limit: **1500 text characters maximum.** Reserve characters before each POST and count every attempted synthesis against the limit, even if the server result is ambiguous. No credentials belong in this file.


| UTC | Request | Characters reserved | Status | Notes |
|---|---|---:|---|---|
| 2026-11-01T17:36:00+00:00 | GET /v1/voices | 0 | 200 | Discover available voices with tally key (21 voices) |
| 2026-11-01T17:37:00+00:00 | POST /v1/text-to-speech/CwhRBWXzGAHq8TQ4Fs17/with-timestamps | 108 | 200 | Exploratory synthesis to determine response format (superseded) |
| 2026-11-01T17:37:30+00:00 | POST /v1/text-to-speech/CwhRBWXzGAHq8TQ4Fs17/with-timestamps | 108 | 200 | Exploratory synthesis to determine response format (superseded) |
| 2026-11-01T17:37:33+00:00 | GET /v1/voices | 0 | 200 | Re-discover voices for clean generation |
| 2026-11-01T17:37:34+00:00 | POST /v1/text-to-speech/CwhRBWXzGAHq8TQ4Fs17/with-timestamps | 108 | 200 | 15s proof script; output used (`audio/15s_proof/voice.mp3` + `word_timestamps.json`), model eleven_multilingual_v2, stability 0.35, voice Roger |

**Total reserved this round (tally): 432 / 1,500.** Four synthesis calls at 108 chars each; every attempted synthesis counted per division rule. Remaining: 1,068 characters. No API key committed or logged.

