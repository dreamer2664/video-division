#!/usr/bin/env python3
"""
End-to-end offline-reproducible build runner for MARK SIX (videos/team-b/grade-v07).

Usage:
    python3 videos/team-b/grade-v07/build_v07.py
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

for step in ("generate_luts.py", "build_audio_v07.py", "render_v07.py"):
    print(f"=== Running {step} ===")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, "-B", os.path.join(HERE, step)], check=True, env=env)
