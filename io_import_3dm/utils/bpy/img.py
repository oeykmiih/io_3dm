# SPDX-License-Identifier: GPL-2.0-or-later
import os
import subprocess

import bpy

def generate_thumbnail(filepath, outpath):
    subprocess.run(
        [
            bpy.app.binary_path,
            "--background",
            "--factory-startup",
            "--python",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "generate_thumbnail.py"),
            "--",
            filepath,
            outpath,
        ]
        )
    return outpath