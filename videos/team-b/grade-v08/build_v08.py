#!/usr/bin/env python3
"""
End-to-end offline-reproducible build orchestrator for MARK SEVEN (videos/team-b/grade-v08).
Runs 100% offline from committed plates, .cube LUTs, and lossless 48 kHz FLAC stems by default.
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run_step(script: str, extra_args: list[str] | None = None) -> None:
    cmd = [sys.executable, "-B", os.path.join(HERE, script)] + (extra_args or [])
    subprocess.run(cmd, check=True)


def main() -> None:
    run_step("generate_luts.py")
    run_step("build_audio_v08.py", sys.argv[1:])
    run_step("render_v08.py")
    shutil.rmtree("/tmp/grade_v08_build", ignore_errors=True)


if __name__ == "__main__":
    main()
