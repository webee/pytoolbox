# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import json
import re
from functools import wraps
from flask import request
from . import response


def compatible(os, version_range, response_handler):
    def func_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            app_os = request.headers.get('OS')
            app_version = request.headers.get('AppVersion')

            resp = func(*args, **kwargs)

            if app_os is None or app_version is None:
                return resp

            processor = CompatibleResponseProcessor(app_os, app_version, resp)
            return processor.process(os, version_range, response_handler).response

        return wrapper

    return func_decorator


def deprecated(os, version_range):
    def func_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            app_os = request.headers.get('OS')
            app_version = request.headers.get('AppVersion')

            if app_os is not None and app_version is not None:
                version = Version(app_os, app_version)
                if version.in_range(os, version_range):
                    return response.gone()

            return func(*args, **kwargs)

        return wrapper

    return func_decorator


class CompatibleResponseProcessor(object):

    _version_pattern = re.compile('(\d+(\.\d+)?)', re.IGNORECASE | re.DOTALL)

    def __init__(self, app_os, app_version, response):
        self._app_os = app_os.lower()
        self._app_version = app_version
        self._origin_response = response

    def process(self, os, version_range, handler):
        version = Version(self._app_os, self._app_version)
        if not version.in_range(os, version_range):
            return self

        data = self._extract_response_data()
        new_data = handler(data, self._origin_response)
        if not new_data:
            return self

        self._origin_response.data = json.dumps(new_data)
        return self

    @property
    def response(self):
        return self._origin_response

    def _extract_response_data(self):
        return json.loads(self._origin_response.data)


class Version(object):

    _version_pattern = re.compile('(\d+(\.\d+)?)', re.IGNORECASE | re.DOTALL)

    def __init__(self, app_os, app_version):
        self._app_os = app_os.lower()
        self._app_version = app_version

    def in_range(self, os, version_range):
        if not self._is_matched_os(os):
            return False

        if not self._in_range(version_range):
            return False

        return True

    def _is_matched_os(self, os):
        os = os.lower()
        return os == 'all' or os == self._app_os

    def _in_range(self, version_range):
        version_range = Version._clear_all_whitespace(version_range)
        operator, version = self._parse_version(version_range)

        app_version = float(self._app_version)
        spec_version = float(version)
        return Version._compare(app_version, operator, spec_version)

    @staticmethod
    def _clear_all_whitespace(text):
        return re.sub(r"\s+", "",  text)

    def _parse_version(self, version_range):
        matched_items = self._version_pattern.findall(version_range)
        if not matched_items:
            raise ValueError("Cannot find any version in range('%s')" % version_range)

        version = matched_items[0][0]
        operator = version_range.replace(version, "")
        if operator == '':
            operator = '=='

        return operator, version

    @staticmethod
    def _compare(app_version, operator, spec_version):
        if operator == '>=':
            return app_version >= spec_version
        if operator == '>':
            return app_version > spec_version
        if operator == '==':
            return app_version == spec_version
        if operator == '<':
            return app_version < spec_version
        if operator == '<=':
            return app_version <= spec_version
        return False
