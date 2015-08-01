# -*- coding: utf-8 -*-
import os


_DEEPS = 4


def project_root():
    path = os.path.realpath(__file__)
    for i in range(0, _DEEPS - 1):
        path = _parent(path)
    return path


def _parent(path):
    return os.path.dirname(path)
