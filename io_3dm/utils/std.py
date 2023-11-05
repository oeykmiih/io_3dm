# SPDX-License-Identifier: GPL-2.0-or-later
import functools
import itertools

# CREDIT : Scatter5
def import_modules(modules):
    import importlib
    import inspect
    import os
    import sys
    import pathlib
    _frame = inspect.currentframe()
    try:
        frame = _frame.f_back
        package = inspect.getmodule(frame).__package__
        depth = len(str(package).split("."))
        DIR = pathlib.Path(inspect.getfile(frame)).parents[depth]
        delete = False
        try:
            if DIR not in sys.path:
                sys.path.insert(0, DIR)
                delete = True
            for name, module in modules.items():
                modules[name] = importlib.import_module(f"{package}.{name}")
        finally:
            if delete:
                sys.path.remove(DIR)
        frame.f_locals.update(modules)
    finally:
        del _frame
    return modules

# CREDIT : Scatter5
def import_libraries(modules):
    import importlib
    import inspect
    import os
    import sys
    _frame = inspect.currentframe()
    try:
        frame = _frame.f_back
        package = inspect.getmodule(frame).__package__
        depth = len(str(package).split("."))
        DIR = os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(frame)), "libs"))
        delete = False
        try:
            if DIR not in sys.path:
                sys.path.insert(0, DIR)
                delete = True
            for name, module in modules.items():
                modules[name] = importlib.import_module(name)
        finally:
            if delete:
                sys.path.remove(DIR)
        frame.f_locals.update(modules)
    finally:
        del _frame
    return modules

# CREDIT: https://devtalk.blender.org/t/20040
def cleanse_globals(libraries=[]):
    import inspect
    import sys

    _frame = inspect.currentframe()
    try:
        frame = _frame.f_back
        package = inspect.getmodule(frame)

        modules = sys.modules
        modules = dict(sorted(modules.items(),key= lambda x:x[0])) #sort them

        for key in modules.keys():
            if key.startswith(package.__name__):
                del sys.modules[key]
            else:
                for lib in libraries:
                    if key.startswith(lib):
                        del sys.modules[key]
                        break
    finally:
        del _frame
    return None

# CREDIT: https://stackoverflow.com/questions/31174295/getattr-and-setattr-on-nested-subobjects-chained-properties/31174427
def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)

def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))

def traverse_tree(tree):
    yield tree
    for child in tree.children:
        yield from traverse_tree(child)

def pad_lists(*lists, padding=None):
    padded = [[] for _ in lists]
    for lst in itertools.zip_longest(*lists, fillvalue=padding):
        for i, elem in enumerate(lst):
            padded[i].append(elem)
    return padded
