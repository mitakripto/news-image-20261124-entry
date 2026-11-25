#!/usr/bin/env python3
"""Copy the rendered front page to the grader's output folder.

The picture itself is produced by draw.py in this same directory.
This script only moves the finished PNG where the grader expects it:
an output directory given on the command line, in OUTPUT_DIR, or
"/output" by default.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")

if len(sys.argv) > 1:
    dest_dir = sys.argv[1]
else:
    dest_dir = os.environ.get("OUTPUT_DIR", "/output")

os.makedirs(dest_dir, exist_ok=True)
dest = os.path.join(dest_dir, "entry.png")
shutil.copyfile(SRC, dest)
print("wrote", dest)
