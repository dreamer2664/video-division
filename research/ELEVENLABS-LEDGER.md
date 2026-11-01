# ElevenLabs API ledger — reel voice research

Round limit: **1,200 text characters maximum**. Reserve characters before each POST and count every attempted synthesis against the limit, even if the server result is ambiguous. No credentials belong in this file. The benchmark passage is `ab-reel/benchmark.txt`.

| UTC | Request | Characters reserved | Status | Notes |
|---|---|---:|---|---|
| 2026-11-01T14:38:44+00:00 | GET `/v1/voices` | 0 | 200 | Discover an available premade reference voice. |

| 2026-11-01T14:39:18+00:00 | POST `/v1/text-to-speech/{voice_id}/with-timestamps` | 201 | 200 | One benchmark passage, model `eleven_multilingual_v2`, premade male Roger; the reservation is counted even if the outcome is unknown. |

**Total reserved this round: 201 / 1,200.** Account monthly usage is shared with others and is not assumed to be exclusively available to this experiment.
