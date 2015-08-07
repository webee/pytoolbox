# coding=utf-8
import os
from os.path import dirname, abspath, isdir


def project_root():
    srcpath = _find_src_dir(__file__)
    return os.getenv('PROJ_ROOT', abspath(dirname(srcpath)))


def _find_src_dir(filepath):
    dirpath = dirname(filepath)
    if dirpath == '/':
        raise OSError("Cannot find 'src' folder.")

    if isdir(dirpath) and _folder_name(dirpath) == 'src':
        return dirpath

    return _find_src_dir(dirpath)


def _folder_name(dirpath):
    index = dirpath.rfind('/')
    if index < 0:
        return ''
    return dirpath[index + 1:]