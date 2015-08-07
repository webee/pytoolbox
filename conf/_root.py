# coding=utf-8
import os
from os.path import dirname, abspath


def project_root():
    return os.getenv('PROJ_ROOT', abspath(dirname((dirname(dirname(__file__))))))
