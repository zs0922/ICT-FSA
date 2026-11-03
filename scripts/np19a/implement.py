#!/usr/bin/env python3
"""Build the board shell around the emitted original FSA AXI core."""
import argparse
from pathlib import Path
import subprocess
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2]
subprocess.run(['vivado','-mode','batch','-source',str(root/'scripts/np19a/implement.tcl'),'-tclargs',str(a.build.resolve()),str(root)],cwd=a.build,check=True)
