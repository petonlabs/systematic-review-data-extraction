#!/usr/bin/env python3
"""
Convenience wrapper for the restart extraction script.
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    script_path = Path(__file__).parent / "src" / "scripts" / "restart_extraction.py"
    subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
