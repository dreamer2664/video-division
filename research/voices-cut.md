# Voice-quality research — division narration

**Run date:** 2026-11-01 · **Branch:** `cut/voice-imaging` · **Analyzer:** [`tools/voice_quality.py`](../tools/voice_quality.py)

## What this does (and does not) measure

The script is file-in/numbers-out: it decodes through FFmpeg to mono 22.05 kHz and never opens a microphone or playback device. For every 40 ms frame (10 ms hop) it estimates F0 by a windowed autocorrelation peak search over 65–500 Hz; it reports mean/SD, the SD of the smoothed voiced-frame derivative in Hz/s and semitones/s, and a CSV track on request. Speech activity uses a simple adaptive RMS gate. “Syllables” are smoothed RMS-envelope peaks, not ASR or phonetic syllabification; approximate words/minute divides by an assumed 1.55 English syllables/word. Pause runs are inactive-gate intervals ≥120 ms. Other outputs include active RMS-dB variation, spectral centroid and 85% rolloff, plus an autocorrelation periodicity/HNR-like proxy.

The 0–100 **monotone score is a transparent heuristic**: a weighted inverse of F0 spread, F0-slope spread, energy spread, centroid spread, and rolloff spread (weights 0.40 / 0.25 / 0.18 / 0.085 / 0.085). Higher means flatter by this feature recipe; it is not trained, calibrated to listeners, or an estimate of beauty, acting, intelligibility, or human naturalness. Speech content, voice, room, compression, noise and background music all affect these features. The HNR field is explicitly a rough autocorrelation periodicity proxy, **not** Praat's HNR calculation and not a clinical voice-quality score.

The pitch method is intentionally a small, inspectable baseline, not Praat's preferred filtered-autocorrelation workflow. Raw/autocorrelation methods can make octave errors and need sensible voicing/pitch bounds; the Praat manual explains these tradeoffs [1]. Speech-rate estimation from acoustics is also imperfect: a published spontaneous-speech estimator reports correlation rather than perfect agreement with manual syllable segmentation [3].

## Baseline table

Analyzed the available narration assets for the named divisions. All isolated files were decoded/downmixed by the same analyzer settings; figures are estimates, not precision phonetics. “Derivative SD” is smoothed voiced F0 derivative in Hz/s. “Centroid / rolloff” are active-frame means in Hz. Pause count means detected internal inactive runs ≥120 ms; rates are per estimated active speech second.

| Division / source | Asset status | F0 mean ± SD (Hz) | F0 derivative SD (Hz/s) | Syll/s | Pauses | Energy SD (dB) | Centroid / rolloff85 (Hz) | Monotone /100 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `reel-v07` | isolated `assets/narration.flac` | 121.5 ± 58.4 | 313.8 | 4.26 | 29 | 9.21 | 2,029 / 3,454 | 15.1 |
| `reel-v08` | isolated `assets/narration.flac` | 119.9 ± 55.6 | 307.0 | 4.56 | 26 | 7.82 | 2,166 / 3,587 | 17.4 |
| `cut-v08` | isolated `assets/narration.wav` | 127.5 ± 64.1 | 447.8 | 4.75 | 26 | 8.70 | 2,305 / 3,820 | 13.1 |
| `pixel-v06` | **no committed isolated voice stem found**; measured mono downmix of embedded full-mix audio only as a non-comparable proxy | 291.2 ± 187.3 | 563.2 | 8.88* | 25* | 2.44* | 4,066 / 6,513* | 17.8* |
| Grade `MARK FOUR` (`grade-v05`) | isolated `audio/narration_stem_48k.flac` | 119.7 ± 52.5 | 335.4 | 4.14 | 22 | 8.90 | 2,162 / 3,679 | 17.8 |

`*` Pixel-v06 figures are **not narration-only measures**; music, effects and mixed audio contaminate activity, F0, speech-rate, pause, energy and spectral outputs. Do not compare that row to stems. Its source is the branch's `video.mp4` audio stream. The branch includes `assets/voice.py` (Edge TTS, `en-US-ChristopherNeural`, −12% rate, −4 Hz pitch) and narration text, but no standalone rendered stem in the committed tree. We did not pretend the full mix is a voice stem.

HNR proxy means for the four isolated stems were 1.2–1.5 dB; because this is not a calibrated HNR implementation, those values are retained in [`voice_ab/legacy_stem_baseline.json`](voice_ab/legacy_stem_baseline.json) for reproducibility, **not interpreted as voice quality**. The accompanying F0/energy/spectral CSV tracks are in [`voice_ab/`](voice_ab/).

### Numerical comparison and reading

The built-in A/B verdict was tested on `reel-v07` versus `reel-v08`: it reports a 2.3-point heuristic difference (15.1 vs. 17.4; lower = more measured variation), explicitly as a *prosody proxy*. Among accessible isolated sources, `cut-v08` has the most movement by this score (13.1) and `grade MARK FOUR` the least (17.8), but these small differences are easily confounded by content and production. **This cannot establish which voice sounds better or more human.**

## Same-text A/B: current chain vs. ElevenLabs

Test text (106 characters; 3 sentences, also the current-chain payload): “It's two fourteen in the morning. There is one smart speaker in this flat. It has never been told my name.” The current chain is the committed v06 Edge TTS recipe from `assets/voice.py`; the same 106-character input was synthesized once at `en-US-ChristopherNeural`, rate −12%, pitch −4 Hz. It yielded a 9.41 s file. Measured: F0 115.1 ± 36.5 Hz, derivative SD 244.1 Hz/s, 4.08 estimated syllables/s, 2 pauses ≥120 ms, active energy SD 8.40 dB, centroid 2,180 Hz, rolloff85 3,609 Hz, monotone heuristic 22.0/100. See [`voice_ab/current-chain-edge.mp3`](voice_ab/current-chain-edge.mp3) and its F0 CSV.

**ElevenLabs was not called.** The API key is not available in this execution context after session condensation; no request was made and the character budget remains **0 / 1,200**. The ledger contains the same status and the exact planned text count, but no credential. To finish this row, expose `ELEVENLABS_API_KEY` as a runtime secret (do not paste it into a report or commit it) and rerun the single 106-character synthesis. Until then, there are no honest ElevenLabs numbers to publish.

## Caveats / interpretation

- Autocorrelation can choose octave errors, miss breathy/creaky frames, and is sensitive to voice pitch range and noise. Mean/SD across a whole mixed narration also collapses phrase-level intonation.
- RMS-gating can mistake music/noise for speech or omit quiet words; the “syllable” detector counts local amplitude peaks, so it may merge or split syllables.
- The automatic lexical-rate estimate assumes English's rough 1.55 syllables/word; treat syllables/s as the primary proxy and both as estimates.
- Pause values depend on gate and duration thresholds. A deliberate dramatic pause is not inherently a defect.
- Spectral centroid/rolloff describe timbre/phonetic content as well as recording chain; they are not monotony or voice-beauty measurements by themselves.
- Prosodic variation correlates with style, but variation is not always desirable: a controlled, restrained delivery may intentionally vary less. No listener study or blinded rating was run.

## Sources

1. Praat, [“How to choose a pitch analysis method”](https://www.fon.hum.uva.nl/praat/manual/how_to_choose_a_pitch_analysis_method.html). Recommends filtered autocorrelation for intonation and details octave and voicing errors; our simple estimator is not a drop-in Praat equivalent.
2. “Effects of Fundamental Frequency, Vocal Intensity, Sample Duration, and Vowel Context in Cepstral and Spectral Measures of Dysphonic Voices,” *Journal of Voice* (2020), [PubMed PMID 32348195](https://pubmed.ncbi.nlm.nih.gov/32348195/). Finds F0, intensity, duration and context can affect HNR/CPPS, so HNR should not be treated as a context-free grade.
3. D. Wang & S. Narayanan (2007), [“Robust Speech Rate Estimation for Spontaneous Speech,” IEEE TASLP 15(8), 2190–2201](https://pmc.ncbi.nlm.nih.gov/articles/PMC2860302/), DOI [10.1109/TASL.2007.905178](https://doi.org/10.1109/TASL.2007.905178). Estimates rate from acoustic/syllabic cues without transcription; its reported correlation with manual segmentation motivates treating the present envelope-peak rate as approximate.
4. T. Raitio, R. Rasipuram & D. Castellani (2020), [“Controllable Neural Text-to-Speech Synthesis Using Intuitive Prosodic Features,” Interspeech](https://arxiv.org/abs/2009.06775). Reports that generated prosody can regress toward the training database's average style; pitch range, phone duration, energy and spectral tilt provide useful control dimensions.
5. [“Speech Synthesis Techniques: A Survey”](https://www.researchgate.net/publication/252012637_Speech_synthesis_techniques_A_survey). Discusses concatenative systems' unit selection, prosodic modification and boundary discontinuity tradeoffs. Secondary survey; used for broad mechanism, not a claim that every concatenative system sounds flat.
6. T. Timoney et al., [“Locating Discontinuities in Synthetic Speech using a Perceptually Orientated Approach”](https://www.researchgate.net/publication/228781040_Locating_Discontinuities_in_Synthetic_Speech_using_a_Perceptually_Orientated_Approach). Covers audible discontinuities in synthetic/unit-selected speech. A join mismatch is one possible artifact; it is distinct from low pitch variation.
7. Li, Nayak & Coler (2026), [“What Makes Synthetic Speech Sound Sarcastic? A Prosody-Controlled Perception Study”](https://arxiv.org/abs/2606.09717). A recent controlled study illustrating that pitch, rate and intensity manipulations alter perceived delivery; it does not validate our score.
