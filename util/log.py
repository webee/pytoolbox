# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import logging


def get_logger(name='main', level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if len(logger.handlers) > 0:
        return logger

    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - [%(name)s.%(levelname)s] [%(threadName)s, %(module)s.%(funcName)s@%(lineno)d] %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    return logger
