# Film-emulation research and v10 frame test

**Run date:** 2026-11-01 · **Branch:** `cut/voice-imaging` · **Tool:** [`tools/film_emulate.py`](../tools/film_emulate.py)

## Scope and method

This is a restrained, inspectable film-inspired pass, not a calibrated emulation of a named stock. It adds (1) luminance-dependent random grain in linear-light RGB, (2) a soft warm highlight-halation component, (3) small red/blue radial separation toward the edges, (4) subpixel deterministic gate weave, (5) mild radial lens distortion, (6) a gentle vignette, and (7) a small black-level lift. Parameters are fixed in the script, and an optional `--strength` scales the treatment. The tool takes a video and sample timestamps, writes before/after PNGs and a JSON measurement manifest; it does not re-encode or alter the video.

This simple RGB operation is intentionally different from photochemical simulation. Kodak's technical documentation describes film's exposure-dependent granularity and publishes diffuse RMS granularity and MTF data [1]. Real grain is statistical emulsion structure, not merely independent digital noise. Halation depends on exposure path, layer/spectral response and film base; adding a blurred luminance mask in display-linear RGB is only a stylized approximation [2]. Film-emulation literature emphasizes where grain and halation sit relative to negative/print response curves [2,3]. The output must not be represented as a verified Vision3 stock match.

## Three-frame v10 test

Source: `/home/user/TWO-LIGHTS-cut-v10.mp4` (previously verified SHA-256 `e093a55f941b72fc694b3f9c50bf3ce559307cc658c0f2161ed2ebfaad589403`). Samples at 8.5 s, 27.0 s and 46.0 s. Strength `0.85`; fixed per-sample seeds. The v10 video itself remains untouched. Before/after PNGs are in [`film_emulation/`](film_emulation/), with exact floating-point values in [`measurements.json`](film_emulation/measurements.json).

Metrics are reproducible *image proxies*, not ground-truth film measurements. Grain clumping is represented by adjacent-pixel correlation (mean of horizontal and vertical correlations of a 1.2 px Gaussian high-pass residual; lower means less locally correlated residual). Highlight width is a local radial 10%-above-background falloff proxy around the brightest connected cores; it is content-dependent, and the highlight mix may alter those cores. Edge acutance is mean Sobel gradient among the top 15% gradient pixels. Histogram spread is 8-bit luminance P95−P05.

| Sample | Grain residual SD (8-bit), before → after | Grain adjacent correlation X/Y, before → after | Highlight falloff width (px), before → after | Edge acutance, before → after | Luma P95−P05, before → after |
|---|---:|---:|---:|---:|---:|
| 8.5 s | 6.53 → 6.80 | 0.665 / 0.561 → 0.290 / 0.463 | 21 → 17 | 0.630 → 0.559 | 118 → 115 |
| 27.0 s | 6.69 → 8.30 | 0.725 / 0.580 → 0.394 / 0.131 | 24 → 27 | 0.730 → 0.650 | 199 → 197 |
| 46.0 s | 4.84 → 6.08 | 0.715 / 0.589 → 0.205 / 0.396 | 25 → 27 | 0.583 → 0.523 | 214 → 207 |

Interpretation: the high-pass residual grew on all three images, while its horizontal adjacent correlation fell in every sample (and vertical correlation fell on two of three), consistent with added finer, less clustered texture; the input footage already has significant high-frequency rain/texture, so this is not a pure grain-only measurement. Edge acutance decreased about 10% on these frames, consistent with the radial resampling/halation/softening cost. Luma range contracted modestly (3, 2, and 7 levels). The highlight-width proxy rose on two frames and fell on one; because natural shot structure and the top-highlight selection affect the proxy, interpret this as a rough diagnostic, not a claim that every highlight was broadened. The exported images are available for visual inspection; this is not an aesthetic or stock-fidelity rating.

## Implementation caveats

- Grain is independent seeded noise scaled by luminance, not clustered silver-halide or dye-cloud statistics; no frame-to-frame temporal grain model is evaluated.
- The halation mask is luminance-thresholded, so it ignores spectral layer differences and can create a halo where a particular stock would not.
- RGB radial channel shifts approximate lateral chromatic aberration only. Gate weave is a deterministic subpixel translation per input frame; to see motion, apply it to a time sequence with changing seeds rather than infer motion from three stills.
- The single radial warp is mild and centered; real lens distortion, vignetting and aberration depend on lens, focal length, focus, sensor and optical path.
- Histogram, edge and halo numbers depend on source content, compression, scaling and threshold rules. The listed measurements do not establish authenticity or audience preference.

## References

1. Kodak, [KODAK VISION3 250D Color Negative Film 5207/7207 Technical Data, H-1-5207](https://www.kodak.com/content/products-brochures/Film/VISION3-250D-Technical-Data-EN.pdf). Publishes sensitometric, MTF and diffuse RMS granularity curves; grain perception depends on image density/content.
2. [“True Film Emulation: Building a Photochemical Pipeline”](https://www.welcometoarc.com/post/true-film-emulation-building-a-photochemical-pipeline). Technical practitioner discussion of the ordering of grain/halation relative to negative/print response and limitations of LUT-only emulation; its Kodak references are cited in the article.
3. Peder Morgenthaler, [Film Print Emulation: A Deep Dive Into the Filmbox OFX Plugin](https://mixinglight.com/color-grading-tutorials/fpe-part-4-filmbox-ml1143/). Practitioner discussion of film-emulation properties including grain, halation and gate weave; not a stock measurement standard.
4. [“Spectral film simulations from scratch”](https://discuss.pixls.us/t/spectral-film-simulations-from-scratch/48209), Pixls.us technical discussion. Useful design notes on exposure-dependent grain and red-weighted halation; community source, treated as implementation context rather than primary film-science evidence.
