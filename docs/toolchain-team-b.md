# Team B sandbox toolchain: what works, what doesn't, how to proceed

This map records observed results from the `cut/v03` production sandbox and gives the next worker a repeatable decision path. It distinguishes an unavailable tool from a tool that was actually launched and crashed. **No GUI editor crash is claimed:** the GUI prerequisites were absent, so the applications were not launched.

## Decision in one sentence

Use the repository's Python/OpenCV/Pillow frame generator and FFmpeg CLI as Team B's default when the sandbox matches this test environment. It produced the required 1920×1080, 30 fps H.264 picture with 48 kHz stereo AAC and completed the 60-second render in about 94 seconds. Try a conventional editor only if its executable, display, and usable memory are actually present; don't assume a browser/editor can export just because its website responds.

## Observed capability table

| Path | What was checked or run | Observed result | What that result means |
|---|---|---|---|
| Kdenlive | `command -v kdenlive` | No executable path | Not installed; no launch, crash, or edit/export test. |
| Shotcut | `command -v shotcut` | No executable path | Not installed; no launch, crash, or edit/export test. |
| Virtual X / VNC | `command -v Xvfb x11vnc`; inspect `DISPLAY`/`WAYLAND_DISPLAY` | Neither executable found; display variables unset | Could not run either editor under Xvfb+VNC. This is an environment limitation, not a demonstrated editor failure. |
| Browser editors | `command -v chromium google-chrome`; HTTP HEAD probes only | No browser executable. Kapwing `200`; Clipchamp `302` redirect to `/en/`; Canva `403` | These are just HTTP reachability responses. No real browser session, editing, upload, or export was attempted. Do not call these editors tested. |
| Python composition | Python 3, NumPy, OpenCV (`cv2`), Pillow (`PIL`) imports; actual render | Imports worked; 1,800 generated frames piped to FFmpeg successfully | Tested working for procedural motion graphics, not a conventional footage timeline editor. |
| FFmpeg CLI | `command -v ffmpeg ffprobe` initially | No system executable found | The first `render.sh` attempt stopped with the exact message `Install FFmpeg with libx264 support first.` No package installation was attempted. |
| Standalone FFmpeg | Downloaded FFmpeg 7.0.2 static build outside the repo; used its `ffmpeg` and `ffprobe` | Worked: libx264 H.264/yuv420p render and AAC mux; faststart MP4 | Successful fallback. It was installed in the sandbox's external tools directory, not committed. A fresh worker must supply their own FFmpeg binary or install FFmpeg. |

### Memory and timing evidence

The pre-render `free -h` snapshot was: total **1.9 GiB**, used **488 MiB**, free **1.3 GiB**, available **1.5 GiB**, swap **0 B**. The 60-second 1080p frame-generation run took about **94 seconds** (about 0.64× real time). **Peak RSS was not recorded**; do not treat the baseline as peak usage or promise that other editors fit within a memory limit. If memory matters, measure the actual process (for example, `/usr/bin/time -v ./render.sh`) in the current sandbox and record its `Maximum resident set size`.

## First: inventory this sandbox (copy/paste)

Run this before choosing an editor. Empty command output means the executable was not on `PATH`; it does not prove the software cannot be installed.

```bash
for c in kdenlive shotcut Xvfb xvfb-run x11vnc chromium chromium-browser google-chrome ffmpeg ffprobe python3; do
  printf '%-18s' "$c"
  command -v "$c" || echo 'not found'
done
printf '\nDISPLAY=%s WAYLAND_DISPLAY=%s\n' "${DISPLAY-}" "${WAYLAND_DISPLAY-}"
free -h
python3 - <<'PY'
for name in ('numpy', 'cv2', 'PIL'):
    try:
        m = __import__(name)
        print(name, getattr(m, '__version__', 'available'))
    except Exception as e:
        print(name, 'unavailable:', type(e).__name__, str(e))
PY
```

A website probe is **not** an editor test. If there is no browser GUI, at most record HTTP reachability, label it as such, and move on:

```bash
curl -sSIL --max-time 8 https://www.kapwing.com | head -3
curl -sSIL --max-time 8 https://clipchamp.com | head -3
curl -sSIL --max-time 8 https://www.canva.com | head -3
```

An HTTP response (including a redirect or 403) says nothing about whether interactive editing or exporting works.

## Recommended default: procedural visuals + FFmpeg

### 1. Install/verify prerequisites

On a Debian-like machine where package installation is permitted, a worker can try:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg python3 python3-venv python3-pip fonts-dejavu-core
```

This package install was **not attempted** in the v03 sandbox; `apt-cache policy ffmpeg` did show a Debian package candidate, but that is not evidence that installation succeeds or that a GUI editor is available. If `sudo` is unavailable, apt is blocked, or installation fails, capture the literal error and use a trusted standalone FFmpeg build where policy permits. Do not paste credentials into install commands or logs.

From the repo root, use the project's dependency file and check the font paths required by the renderer:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r videos/team-b/cut-v03/project/requirements.txt
command -v ffmpeg
ffmpeg -hide_banner -encoders | grep -E 'libx264| AAC'
test -r /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
```

If `python3 -m venv` reports that `ensurepip`/venv support is unavailable, install the OS `python3-venv` package if permitted. If OpenCV/Pillow cannot be installed, record the exact pip/build error; do not claim the render pipeline works in that environment.

### 2. Render and measure

```bash
cd videos/team-b/cut-v03
./render.sh
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 video.mp4
ffmpeg -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | grep -A11 'Input Integrated'
```

`render.sh` is the concrete working example: `project/sound.py` generates original audio, `project/render.py` produces moving visuals, and FFmpeg encodes/muxes. The `loudnorm` summary reports both Input (measured file) and Output (hypothetical normalized result) values; quote the **Input** values as file measurements. The spec's version with `ffmpeg -v error` can suppress the loudness summary on this build, so run a second measurement without that verbosity setting.

If 1080p render performance or memory is unacceptable, only then try lower resolution as an explicitly disclosed fallback; 720p is the spec's allowed fallback. A successful render at 720p must not be reported as 1080p.

### 3. Keep it reproducible

Commit the original scripts, generated assets needed by the render, `render.sh`, the timed script, and QA outputs. Don't depend on an uncommitted temporary binary path. A worker cloning the repo should install/provide FFmpeg plus the documented Python dependencies and fonts, then regenerate the output with `render.sh`.

## Optional conventional-editor route (only if inventory shows tools)

If Kdenlive or Shotcut is installed **and** an X display is available, try the installed editor in that actual environment and record launch/export outcome. If the editor exists but no display exists, first check whether the OS package manager and permissions allow installing `xvfb` and `x11vnc`; neither was installed or attempted in v03. A possible Xvfb-only smoke test (requires `xvfb-run`) is:

```bash
xvfb-run -a -s '-screen 0 1280x720x24' kdenlive
# or
xvfb-run -a -s '-screen 0 1280x720x24' shotcut
```

For a VNC-backed display, after installing tools with permission, start `Xvfb :99 -screen 0 1280x720x24`, then `DISPLAY=:99 x11vnc -display :99 -localhost -nopw`. Keep it local-only; do not expose an unauthenticated VNC port to the network. This is a suggested future test, **not** a v03 test result. If package installation is disallowed or an editor still does not launch/export, record the actual stderr/exit code and return to CLI compositing.

## Reporting rules for future workers

- Say **not installed / not attempted** when no executable or display exists; reserve **crashed/failed** for a real launch or export that returns an error.
- Record command, exact error, exit code, machine memory snapshot, and whether it was a baseline or peak.
- A browser HTTP status is not evidence of editor functionality.
- Default to the tested Python/OpenCV/Pillow + FFmpeg pipeline, but verify dependencies and measure the current sandbox rather than assuming the previous memory snapshot applies.
