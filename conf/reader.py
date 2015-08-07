# coding=utf-8
from ._root import project_root


def read_file(filepath, root=project_root()):
    from os import path

    with open(path.join(root, filepath)) as fin:
        return fin.read().strip('\n')
