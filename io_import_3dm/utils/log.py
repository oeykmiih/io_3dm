# SPDX-License-Identifier: GPL-2.0-or-later
from .. import addon

def log(message):
    print(f"{addon.name} :: {message}")
    return None

def verb(message, *, verbose=False):
    if verbose:
        log(message)
    return None

def debug(message, *, debug=False):
    if debug:
        log(message)
    return None
