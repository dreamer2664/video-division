# Voice engine and voice selection — measured research (2026-11-01)

## Decision, with an explicit gate

**Provisional house test default:** `edge-tts --voice en-US-AndrewMultilingualNeural --rate=+0% --pitch=+0Hz`. **Runner-up:** `en-US-BrianMultilingualNeural --rate=+0% --pitch=+0Hz`. These are selected **for the next listening test**, not declared perceptual winners and not permission to resume production. The Director's robot verdict is valid; no human has rated any of these new samples, so **which sounds most human remains unproven**. Fundamental-frequency, pace and spectral measurements cannot prove perceived humanity or naturalness on their own. A systematic review distinguishes acoustic tests from human naturalness tests [3](https://journals-sol.sbc.org.br/index.php/jbcs/article/download/5468/3317), and recent prosody work explains the weaknesses of both simple objective and coarse perceptual scores [1](https://arxiv.org/pdf/2511.02104).

The reason for this shortlist is operational and falsifiable: on the **same passage**, Andrew neutral measured **120.10 Hz F0 mean / 34.35 Hz SD**, **165.92 WPM**, and six detected pauses with **0.285 s median / 0.315 s p90**. Brian neutral measured **125.35 / 19.13 Hz**, **160.52 WPM**, and six pauses with **0.315 / 0.345 s**. They offer two US voices with similar pace/pauses but contrasting pitch spread. This is not a claim that a larger spread is automatically better. The samples include the prior Christopher setting, offline Piper and the paid reference: `ab-reel/five-voices-under-10s.mp3` is **9.216 seconds**. Individual clips, timing and level caveats are in `ab-reel/README.md`.

As an additional listening-test reference, ElevenLabs `eleven_multilingual_v2` / premade **Roger**, stability 0.5, similarity 0.75, style 0, speaker boost on, seed 20261101 measured **104.16 ± 24.55 Hz**, **161.22 WPM**. Its naturalness is also unknown without listening; the shared quota and plan/usage rights must be checked before adopting it. The provider describes the model and nondeterminism [3](https://elevenlabs.io/docs/overview/capabilities/text-to-speech); a commercial licence is plan-dependent [2](https://elevenlabs.io/pricing). Piper `en_US-joe-medium` runs offline after download with no per-character API quota; on this host its native settings were **92.24 ± 14.97 Hz**, **196.29 WPM**. The runtime is GPL-3.0-or-later [1](https://github.com/OHF-Voice/piper1-gpl), and Joe's dataset card says CC0 but the model is fine-tuned from Lessac, so **review all underlying/model and redistribution terms before commercial use** [3](https://respawnstack.com/tools/piper).

## Controlled design and what this can/cannot prove

- **Text:** the identical 201-character, 37-token `ab-reel/benchmark.txt`, with sentence punctuation and no music, sound effects, TTS post-EQ or forced word gaps. Original full clips and service word/character events are retained in `voice-matrix/`.
- **Coverage:** `edge-tts --list-voices` returned **23 English voices labelled male** on this date; all 23 were actually synthesized at two settings, rather than pre-filtering by a subjective “deep” label. `en-AU-WilliamNeural`, explicitly requested but absent from that list, was also requested and accepted at both settings: 24 names × 2 = 48 clips. Christopher's exact v10 setting (−12% / −4 Hz) adds one: **49 Edge clips**. The two William IDs produced very similar but nonidentical decoded waveforms; do not assume two distinct underlying speakers from the names alone. Microsoft Edge's public Python client documents the voice-list and rate/pitch options [1](https://github.com/rany2/edge-tts).
- **Conditions:** neutral `+0% / +0Hz` vs house `−12% / −5Hz`; additional Christopher v10 `−12% / −4Hz`. Piper native length scales 1.0 and 1.12 are not direct Edge rate/pitch equivalents; Piper has no corresponding pitch control in this test. ElevenLabs is a single neutral reference, not a second speed/pitch condition. Its speaker-boost setting and different encoders also confound engine comparison. Only one synthesis per condition: no confidence interval, no ASR transcript/accuracy score, no evidence of test-retest stability.
- **Common path:** decode to mono 16 kHz; level-scale consistently for WebRTC VAD. Praat raw autocorrelation at 10 ms, 60–350 Hz reports mean and **standard deviation across voiced F0 frames**; unvoiced frames are excluded. The pitch ceiling/floor can cause octave errors or drop values [2](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html). We did not manually correct tracks.
- **Pace and pauses:** 37 written tokens divided by first-to-last VAD speech span × 60; not a word-recognition measurement. WebRTC mode 2, 30 ms frames; report interior non-speech runs ≥150 ms as `count / median / p90 / max` [1](https://github.com/wiseman/py-webrtcvad). VAD hangover, false positives and level normalisation can shift boundaries. Pauses include punctuation; they are not actor intent.
- **Spectrum:** mean amplitude-weighted centroid and 85%-amplitude rolloff on VAD-active 32 ms Hann STFT frames, 10 ms hop; all limited to 0–8 kHz. These describe spectral balance, not a quality ranking. Individual encoders and original sample rates differ.

The previous house habit **does change tempo**: Christopher falls from **146.83** to **128.92 WPM** on this passage; his F0 SD shifts **24.27 → 23.69 Hz**, while the actual v10 setting measures **23.77 Hz**. Across all 24 Edge name pairs, median measured WPM changes **−11.96%** and median F0-SD change is **−0.73 Hz**. The data support testing neutral pacing; they do **not** prove slowing or lowering pitch caused the robotic impression. Natural conversation has highly variable rate and different measurement definitions [3](https://languagelog.ldc.upenn.edu/myl/ldc/llog/icslp06_final.pdf); no one numeric WPM is a universal naturalness target.

## Measured comparison matrix

`F0` is mean ± SD in Hz; `pauses` is count / median / p90 / maximum seconds; `centroid` and `rolloff` are Hz. CSV and individual audio filenames/hashes: `voice-metrics.csv`. Full pause vectors and pitch quantiles: `voice-metrics.json`. No sample was graded by a human.

| Engine / voice | Condition | F0 mean ± SD (Hz) | WPM | Pauses n / median / p90 / max (s) | Centroid (Hz) | Rolloff 85% (Hz) |
|---|---|---:|---:|---:|---:|---:|
| en-AU-WilliamMultilingualNeural | +0% / +0Hz | 105.13 ± 28.05 | 173.30 | 6 / 0.360 / 0.390 / 0.390 | 1604.8 | 2981.1 |
| en-AU-WilliamMultilingualNeural | −12% / −5Hz | 101.56 ± 27.34 | 152.58 | 6 / 0.420 / 0.435 / 0.450 | 1557.7 | 2883.5 |
| en-AU-WilliamNeural | +0% / +0Hz | 105.12 ± 28.03 | 173.30 | 6 / 0.360 / 0.375 / 0.390 | 1606.4 | 2988.0 |
| en-AU-WilliamNeural | −12% / −5Hz | 101.55 ± 27.34 | 152.58 | 6 / 0.420 / 0.435 / 0.450 | 1556.3 | 2882.3 |
| en-CA-LiamNeural | +0% / +0Hz | 99.77 ± 31.83 | 157.78 | 4 / 0.780 / 0.780 / 0.780 | 1420.7 | 2604.0 |
| en-CA-LiamNeural | −12% / −5Hz | 98.06 ± 31.87 | 138.84 | 4 / 0.900 / 0.900 / 0.900 | 1382.1 | 2535.0 |
| en-GB-RyanNeural | +0% / +0Hz | 124.87 ± 45.78 | 155.46 | 4 / 0.855 / 0.870 / 0.870 | 1518.2 | 2835.5 |
| en-GB-RyanNeural | −12% / −5Hz | 120.27 ± 44.06 | 136.78 | 4 / 0.990 / 0.990 / 0.990 | 1498.4 | 2763.5 |
| en-GB-ThomasNeural | +0% / +0Hz | 122.87 ± 27.36 | 150.10 | 5 / 0.810 / 0.840 / 0.840 | 1643.3 | 2986.5 |
| en-GB-ThomasNeural | −12% / −5Hz | 118.01 ± 26.81 | 132.38 | 6 / 0.945 / 0.975 / 0.990 | 1603.5 | 2899.4 |
| en-HK-SamNeural | +0% / +0Hz | 177.63 ± 49.06 | 139.36 | 4 / 0.930 / 0.930 / 0.930 | 1865.1 | 3347.6 |
| en-HK-SamNeural | −12% / −5Hz | 170.90 ± 47.92 | 122.72 | 4 / 1.065 / 1.080 / 1.080 | 1812.9 | 3255.4 |
| en-IE-ConnorNeural | +0% / +0Hz | 158.05 ± 43.01 | 155.14 | 4 / 0.810 / 0.810 / 0.810 | 1793.6 | 3228.9 |
| en-IE-ConnorNeural | −12% / −5Hz | 152.32 ± 41.28 | 136.78 | 4 / 0.930 / 0.951 / 0.960 | 1724.8 | 3107.1 |
| en-IN-PrabhatNeural | +0% / +0Hz | 131.61 ± 36.96 | 134.79 | 5 / 0.750 / 0.780 / 0.780 | 1646.8 | 2898.2 |
| en-IN-PrabhatNeural | −12% / −5Hz | 126.96 ± 36.04 | 118.97 | 5 / 0.900 / 0.900 / 0.900 | 1618.8 | 2843.4 |
| en-KE-ChilembaNeural | +0% / +0Hz | 114.03 ± 20.92 | 157.11 | 4 / 0.840 / 0.861 / 0.870 | 1906.0 | 3411.9 |
| en-KE-ChilembaNeural | −12% / −5Hz | 109.12 ± 20.79 | 138.58 | 4 / 0.975 / 0.990 / 0.990 | 1882.3 | 3366.0 |
| en-NG-AbeoNeural | +0% / +0Hz | 116.29 ± 25.46 | 157.45 | 6 / 0.825 / 0.840 / 0.840 | 1949.5 | 3465.7 |
| en-NG-AbeoNeural | −12% / −5Hz | 111.67 ± 25.14 | 138.32 | 6 / 0.945 / 0.960 / 0.960 | 1934.1 | 3428.8 |
| en-NZ-MitchellNeural | +0% / +0Hz | 130.76 ± 29.70 | 146.25 | 6 / 0.885 / 0.915 / 0.930 | 1640.4 | 2957.3 |
| en-NZ-MitchellNeural | −12% / −5Hz | 125.28 ± 29.22 | 128.70 | 6 / 1.035 / 1.050 / 1.050 | 1606.5 | 2886.7 |
| en-PH-JamesNeural | +0% / +0Hz | 118.68 ± 28.51 | 151.33 | 5 / 0.810 / 0.828 / 0.840 | 1811.8 | 3146.6 |
| en-PH-JamesNeural | −12% / −5Hz | 114.20 ± 27.55 | 133.33 | 5 / 0.930 / 0.930 / 0.930 | 1781.1 | 3073.1 |
| en-SG-WayneNeural | +0% / +0Hz | 125.99 ± 29.56 | 132.14 | 4 / 0.825 / 0.861 / 0.870 | 1764.1 | 3130.1 |
| en-SG-WayneNeural | −12% / −5Hz | 121.25 ± 28.62 | 116.54 | 4 / 0.960 / 0.981 / 0.990 | 1731.1 | 3045.9 |
| en-TZ-ElimuNeural | +0% / +0Hz | 117.31 ± 26.60 | 154.49 | 4 / 0.840 / 0.840 / 0.840 | 1962.9 | 3446.7 |
| en-TZ-ElimuNeural | −12% / −5Hz | 113.64 ± 25.22 | 136.03 | 4 / 0.960 / 0.981 / 0.990 | 1937.5 | 3399.0 |
| en-US-AndrewMultilingualNeural | +0% / +0Hz | 120.10 ± 34.35 | 165.92 | 6 / 0.285 / 0.315 / 0.330 | 1772.7 | 3070.0 |
| en-US-AndrewMultilingualNeural | −12% / −5Hz | 116.07 ± 32.58 | 143.69 | 6 / 0.330 / 0.360 / 0.360 | 1731.7 | 3000.7 |
| en-US-AndrewNeural | +0% / +0Hz | 111.91 ± 35.12 | 177.03 | 6 / 0.285 / 0.315 / 0.330 | 1747.1 | 2967.1 |
| en-US-AndrewNeural | −12% / −5Hz | 108.41 ± 33.64 | 155.79 | 6 / 0.330 / 0.360 / 0.360 | 1691.6 | 2877.4 |
| en-US-BrianMultilingualNeural | +0% / +0Hz | 125.35 ± 19.13 | 160.52 | 6 / 0.315 / 0.345 / 0.360 | 1977.7 | 3421.3 |
| en-US-BrianMultilingualNeural | −12% / −5Hz | 121.00 ± 18.48 | 141.22 | 6 / 0.375 / 0.405 / 0.420 | 1914.4 | 3331.9 |
| en-US-BrianNeural | +0% / +0Hz | 125.35 ± 19.13 | 160.52 | 6 / 0.330 / 0.360 / 0.360 | 1957.6 | 3400.2 |
| en-US-BrianNeural | −12% / −5Hz | 120.99 ± 18.45 | 141.22 | 6 / 0.375 / 0.405 / 0.420 | 1915.9 | 3332.2 |
| en-US-ChristopherNeural | +0% / +0Hz | 115.10 ± 24.27 | 146.83 | 4 / 0.780 / 0.801 / 0.810 | 1655.2 | 2932.8 |
| en-US-ChristopherNeural | −12% / −5Hz | 110.65 ± 23.69 | 128.92 | 4 / 0.915 / 0.930 / 0.930 | 1642.3 | 2894.4 |
| en-US-ChristopherNeural | v10 −12% / −4Hz | 111.63 ± 23.77 | 128.92 | 4 / 0.900 / 0.921 / 0.930 | 1648.9 | 2914.0 |
| en-US-EricNeural | +0% / +0Hz | 110.32 ± 24.77 | 145.10 | 4 / 0.810 / 0.810 / 0.810 | 1608.6 | 2823.1 |
| en-US-EricNeural | −12% / −5Hz | 106.30 ± 23.84 | 127.81 | 4 / 0.930 / 0.951 / 0.960 | 1565.7 | 2734.2 |
| en-US-GuyNeural | +0% / +0Hz | 163.02 ± 43.74 | 155.14 | 4 / 0.810 / 0.831 / 0.840 | 1831.0 | 3276.8 |
| en-US-GuyNeural | −12% / −5Hz | 156.74 ± 42.99 | 136.53 | 4 / 0.945 / 0.960 / 0.960 | 1774.7 | 3192.0 |
| en-US-RogerNeural | +0% / +0Hz | 145.83 ± 39.39 | 145.10 | 4 / 0.600 / 0.621 / 0.630 | 1521.1 | 2884.7 |
| en-US-RogerNeural | −12% / −5Hz | 140.78 ± 38.03 | 127.81 | 5 / 0.690 / 0.720 / 0.720 | 1490.5 | 2817.0 |
| en-US-SteffanNeural | +0% / +0Hz | 127.07 ± 21.46 | 165.18 | 4 / 0.585 / 0.600 / 0.600 | 1649.9 | 2862.6 |
| en-US-SteffanNeural | −12% / −5Hz | 122.30 ± 21.13 | 145.10 | 5 / 0.660 / 0.690 / 0.690 | 1598.3 | 2761.9 |
| en-ZA-LukeNeural | +0% / +0Hz | 113.95 ± 20.02 | 170.11 | 4 / 0.810 / 0.831 / 0.840 | 1726.7 | 3145.5 |
| en-ZA-LukeNeural | −12% / −5Hz | 109.51 ± 19.36 | 149.80 | 5 / 0.930 / 0.960 / 0.960 | 1694.0 | 3067.1 |
| Piper Joe (offline) | length ×1.00 | 92.24 ± 14.97 | 196.29 | 2 / 0.195 / 0.231 / 0.240 | 1663.8 | 2846.4 |
| Piper Joe (offline) | length ×1.12 | 94.77 ± 25.89 | 181.37 | 2 / 0.165 / 0.177 / 0.180 | 1668.0 | 2837.2 |
| Eleven Roger / multilingual v2 | native / reference | 104.16 ± 24.55 | 161.22 | 4 / 0.705 / 0.813 / 0.840 | 1614.5 | 2917.6 |

## Listening validation needed before production

Use at least three new passages (questions, declaratives, numbers and emotional turns); gather independent blind, random-order pairwise preferences against the existing Christopher −12%/−4 Hz baseline. Match loudness with adequate-duration speech, verify words and pronunciation separately, rotate order, record the number of listeners and ties, and report preference proportion with a binomial/bootstrap confidence interval. Do not label an acoustic proxy or predicted score as a human MOS. The supplied 9-second five-way reel is a fast first screen, not that study. **Keep production stopped until a human listening decision and appropriate rights/quota approval.**

## Repeat and provenance

Install Python dependencies `edge-tts==7.3.1`, `praat-parselmouth==0.4.7`, `webrtcvad-wheels==2.0.14.post1`, NumPy/SciPy and FFmpeg; with the committed audio, run `python research/measure_voices.py` and `python research/make_ab.py`. The measured CSV/JSON and 9-second reel were separately regenerated byte-for-byte on the same host; this does not demonstrate that a fresh cloud synthesis will be identical. `synthesize_edge.py` will recontact Edge only if files are absent; catalog and service output may change. Piper 1.8.0 was run locally on CPU; its model URL, config and SHA-256 are in `voice-matrix/piper/model_manifest.json`; the 63.2 MB model is not committed. ElevenLabs's timestamp API was called once with the 201-character passage [1](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps); every API call and reservation is in `ELEVENLABS-LEDGER.md`, total **201 / 1,200 characters**, with no assumption about remaining shared monthly usage.
