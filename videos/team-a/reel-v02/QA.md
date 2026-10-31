# QA — revised render, WIP checkpoint

The revised video and three updated stills are present. `./verify.sh` passed the full-file technical, audio, black/freeze and frame-count checks; a fresh-clone reproduction and final review notes are still pending. Do not treat this WIP checkpoint as completed QA.

The earlier committed original was **7,524,354 bytes**, video bitrate **787,644 bit/s**, and compared to the source drawings had an eight-sample average RGB PSNR of **38.08 dB** and half-size luma SSIM of **0.99927**. Its small size came from efficient encoding of an overly sparse picture, not simply a broken encode. We revised the motion itself, not just file size.

The current revised render is **20,687,910 bytes**, **2,542,766 bit/s video**, 60.000000 s, 1920×1080 at 30 fps, −16.0 LUFS and −4.4 dBTP. The encoder targets 4 Mb/s ABR but is not padded and undershoots on these simple flat graphics. This environment lacks both display and sound devices, so real-time subjective watch/listen remains unperformed; sampled frames and automated metrics are not a substitute.
