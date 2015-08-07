# coding=utf-8
import os
from os.path import dirname, abspath, isdir


def project_root():
    src_path = _find_src_dir(__file__)
    return os.getenv('PROJ_ROOT', abspath(dirname(src_path)))


def _find_src_dir(filepath):
    dir_path = dirname(filepath)
    if dir_path == '/':
        raise OSError("Cannot find 'src' folder.")

    if isdir(dir_path) and _folder_name(dir_path) == 'src':
        return dir_path

    return _find_src_dir(dir_path)


def _folder_name(dir_path):
    index = dir_path.rfind('/')
    if index < 0:
        return ''
    return dir_path[index + 1:]