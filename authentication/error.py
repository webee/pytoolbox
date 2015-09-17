# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division


class AuthenticationError(Exception):
    def __init__(self, message):
        super(AuthenticationError, self).__init__(message)
