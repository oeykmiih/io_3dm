import os
import platform
import sys

match platform.system():
    case 'Windows':
        DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "win64"))
    case 'Darwin':
        match platform.processor():
            case 'arm':
                DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "mac_arm"))
            case 'i386':
                DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "mac_intel"))
            case _:
                print("DEBUG :: Platform not supported by cityhash.")
    case _:
        print("DEBUG :: Platform not supported by cityhash.")

try:
    if os.path.isdir(DIR) and DIR not in sys.path:
        sys.path.insert(0, DIR)

    import cityhash
    import farmhash
finally:
    if DIR in sys.path:
        sys.path.remove(DIR)