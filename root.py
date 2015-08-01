# -*- coding: utf-8 -*-
import os


def project_root():
    return _parent(_parent(_parent(os.path.realpath(__file__))))


def _parent(path):
    return os.path.dirname(path)
