import os
import platform
import sys

match platform.system():
    case 'Windows':
        DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "win64"))
    case 'Darwin':
        DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "macos"))
    case _:
        print("DEBUG :: Platform not supported by rhino3dm.")

try:
    if os.path.isdir(DIR) and DIR not in sys.path:
        sys.path.insert(0, DIR)

    import rhino3dm
finally:
    if DIR in sys.path:
        sys.path.remove(DIR)