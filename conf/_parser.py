# -*- coding: utf-8 -*-
import os
import re

from util.root import project_root


def _parse_file(text):
    path = _try_to_extract_file_path(text)
    if not path:
        return None
    file_path = os.path.join(project_root(), path) if _is_relative_path(path) else path
    return _read_string(file_path)


def _try_to_extract_file_path(text):
    m = re.search('^<file:\s*(.+)>$', text)
    return m.group(1)


def _is_relative_path(path):
    return not path.startswith('/')


def _read_string(file_path):
    with open(file_path) as fin:
        return fin.read().strip('\n')


def _should_parse(text):
    result = re.match('^<.+>$', text)
    return result is not None


def parse(text):
    if not _should_parse(text):
        return text

    _parser_chain = [_parse_file]
    for do_parsing in _parser_chain:
        value = do_parsing(text)
        if value:
            return value
    return None
