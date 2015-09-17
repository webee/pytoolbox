# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from .error import *
from ..util.enum import enum

__all__ = ['BusinessType', 'CodeSender']


BusinessType = enum(LOGIN=1)


class CodeSender(object):
    def __init__(self, service_url, cdkey, password):
        self._service_url = service_url
        self._cdkey = cdkey
        self._password = password

    def send(self, business_type, phone_no):
        from .verification_code import send_code
        send_code(self._service_url, self._cdkey, self._password, business_type, phone_no)


class User(object):

    @classmethod
    def quick_login(cls, phone_no, verification_code):
        from .verification_code import verify_code
        if not verify_code(BusinessType.LOGIN, phone_no, verification_code):
            raise CodeVerificationFailedError(phone_no, verification_code)
