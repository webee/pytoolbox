# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

__all__ = ['CodeSender']


class CodeSender(object):
    def __init__(self, service_url, cdkey, password):
        self._service_url = service_url
        self._cdkey = cdkey
        self._password = password

    def send(self, business_type, phone_no):
        from .verification_code import send_code
        send_code(self._service_url, self._cdkey, self._password, business_type, phone_no)