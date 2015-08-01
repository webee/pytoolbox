# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import os

from _config import CustomizedConfig
from _root import project_root


__all__ = ['get']


def get(section, option):
    return _conf.get(section, option)


class SectionReader(object):
    def __init__(self, _config, section_name):
        self._config = _config
        self._section_name = section_name

    def __getattr__(self, item):
        return self._config.get(self._section_name, item)



_env = os.getenv('ENV')
config_path = os.path.join(project_root(), 'conf', '%s.cfg' % _env)
if not os.path.exists(config_path):
    raise IOError("Cannot find config file at %s" % config_path)

_conf = CustomizedConfig()
_conf.read(config_path)
