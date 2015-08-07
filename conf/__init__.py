# coding=utf-8

def load(config_package, env='dev'):
    from _config_loader import load as _load
    return _load(config_package, env=env)


def read_file(filepath):
    from _reader import read_file as _read_file
    return _read_file(filepath)
