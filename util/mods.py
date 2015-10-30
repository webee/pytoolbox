# coding=utf-8
from __future__ import unicode_literals


def find_mod(p, name):
    while True:
        try:
            mod = __import__(p.__name__ + '.' + name, fromlist=[p.__name__])
            return mod
        except ImportError as _:
            try:
                p = __import__(p.__package__)
            except ImportError as _:
                return None
