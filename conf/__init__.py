# coding=utf-8


def load(config_package, env):
    from config_loader import load as _load
    return _load(config_package, env=env)


def read_file(filepath):
    from reader import read_file as _read_file
    return _read_file(filepath)


def project_root():
    from _root import project_root as _project_root
    return _project_root()