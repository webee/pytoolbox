# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division


class AuthenticationError(Exception):
    def __init__(self, message):
        super(AuthenticationError, self).__init__(message)


class CodeVerificationFailedError(AuthenticationError):
    def __init__(self, phone_no, verification_code):
        msg = "Code verification was failed [phone_no = {0}, verification_code = {1}]".format(phone_no,
                                                                                              verification_code)
        super(CodeVerificationFailedError, self).__init__(msg)