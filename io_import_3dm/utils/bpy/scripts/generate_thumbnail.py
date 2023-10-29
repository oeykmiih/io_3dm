import sys
import math

import bpy

argv = sys.argv
argv = argv[argv.index("--") + 1:]
FILEPATH, OUTPATH = argv
SIZE_X = 500

image = bpy.data.images.load(FILEPATH)
ratio = image.size[1] / image.size[0]
image.scale(SIZE_X, math.floor(SIZE_X * ratio))
image.file_format = 'JPEG'
image.save(filepath=OUTPATH)