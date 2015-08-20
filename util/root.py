# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import sys
from os.path import dirname, basename, abspath


class RootNotFoundError(Exception):
    def __init__(self, root_name):
        message = "Cannot find root named '%s'" % root_name
        super(RootNotFoundError, self).__init__(message)


def root_path(name):
    exec_path = abspath(sys.argv[0])
    dir_path = dirname(exec_path)

    while _folder_name(dir_path) != name and dir_path != '/':
        dir_path = dirname(dir_path)

    if dir_path == '/':
        raise RootNotFoundError(name)

    return dir_path


def _folder_name(dir_path):
    return basename(dir_path)
