# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from ConfigParser import ConfigParser
import os

from .root import project_root


__all__ = ['get', 'config']


def get(section, option):
    return config.get(section, option)


class CustomizedConfig(ConfigParser):
    def get_duration(self, section, option):
        return self._get_duration(self.get(section, option))

    def _get_duration(self, duration_str):
        duration = 0
        for raw in duration_str.split():
            duration += self._parse(raw)
        return duration

    def _parse(self, raw):
        if raw.endswith('d'):
            return int(raw[:-1]) * 3600 * 24
        elif raw.endswith('h'):
            return int(raw[:-1]) * 3600
        elif raw.endswith('m'):
            return int(raw[:-1]) * 60
        elif raw.endswith('ms'):
            return float(raw[:-2]) / 1000
        elif raw.endswith('s'):
            return int(raw[:-1])
        else:
            return int(raw)


env = os.getenv('ENV')
config_path = os.path.join(project_root(), 'conf', '%s.cfg' % env)
if not os.path.exists(config_path):
    raise IOError("Cannot find config file at %s" % config_path)

config = CustomizedConfig()
config.read(config_path)
