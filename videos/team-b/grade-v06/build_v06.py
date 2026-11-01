#!/usr/bin/env python3
"""
End-to-end reproducible build runner for MARK FIVE (grade-v06).
Author: grade <grade@agency.local>

Usage:
    python3 videos/team-b/grade-v06/build_v06.py
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

for step in ("generate_luts.py", "build_audio_v06.py", "render_v06.py"):
    print(f"=== Running {step} ===")
    subprocess.run([sys.executable, os.path.join(HERE, step)], check=True)
