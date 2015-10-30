# coding=utf-8
import sys


def current_module(level=1):
    caller_filename = sys._getframe(1+level).f_code.co_filename
    cur_mod = None
    for m in sys.modules.values():
        if m and '__file__' in m.__dict__ and m.__file__.startswith(caller_filename):
            cur_mod = m
            break
    return cur_mod


def current_file(level=1):
    cur_mod = current_module(level)
    return cur_mod.__file__ if cur_mod else None
