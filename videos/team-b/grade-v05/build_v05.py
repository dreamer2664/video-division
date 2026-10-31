#!/usr/bin/env python3
"""
End-to-end reproducible build runner for MARK FOUR (grade-v05).
Author: grade <grade@agency.local>

Usage:
    python3 videos/team-b/grade-v05/build_v05.py
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

for step in ("generate_luts.py", "build_audio_v05.py", "render_v05.py"):
    print(f"=== Running {step} ===")
    subprocess.run([sys.executable, os.path.join(HERE, step)], check=True)
