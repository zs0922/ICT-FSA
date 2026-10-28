#!/usr/bin/env python3
"""Unified ICT-FSA workflow; see this commit's README.md."""
import subprocess
import sys
from ict_cli import main

if __name__ == '__main__':
    try: main()
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(2)
