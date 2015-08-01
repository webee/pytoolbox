# -*- coding: utf-8 -*-
import os
import re

from _root import project_root


def _parse_file(text):
    path = _extract_file_path(text)
    if not path:
        return None
    file_path = os.path.join(project_root(), path) if _is_relative_path(path) else path
    return _read_string(file_path)


def _parse_os_var(text):
    var_name = _extract_os_var_name(text)
    return os.environ[var_name] if var_name else None


def _extract_os_var_name(text):
    m = re.search('^<os:\s*(.+)>$', text)
    return m.group(1) if m else None


def _extract_file_path(text):
    m = re.search('^<file:\s*(.+)>$', text)
    return m.group(1) if m else None


def _is_relative_path(path):
    return not path.startswith('/')


def _read_string(file_path):
    with open(file_path) as fin:
        return fin.read().strip('\n')


def _should_parse(text):
    result = re.match('^<.+>$', text)
    return result is not None


class ParserNotFoundError(Exception):
    def __init__(self, value):
        message = "Cannot find parser for value[{0}].".format(value)
        super(ParserNotFoundError, self).__init__(message)



def parse(text):
    if not _should_parse(text):
        return text

    _parser_chain = [_parse_file, _parse_os_var]
    for do_parsing in _parser_chain:
        value = do_parsing(text)
        if value:
            return value
    raise ParserNotFoundError(text)
