# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from datetime import datetime, timedelta
import string
from ..util import strings
from ..util.dbs import db_context
from ..util.sms import SMS

_expiration_interval_in_minutes = 10


def send_code(service_url, cdkey, password, business_type, phone_no):
    _clear_expired_codes()
    code = _generate_code(business_type, phone_no)

    sms = SMS(service_url, cdkey, password)
    sms.send(phone_no, _build_message(code))


def verify_code(business_type, phone_no, code):
    return _is_unexpired_code(business_type, phone_no, code)


@db_context
def _clear_expired_codes(db):
    db.execute("DELETE FROM verification_code WHERE expiration <= %(now)s", now=datetime.now())


@db_context
def _find_unexpired_code(db, business_type, phone_no):
    return db.get_scalar("""
            SELECT code FROM verification_code
              WHERE business_type = %(type)s
                AND phone_no = %(phone_no)s
                AND expiration > %(now)s
          """, type=business_type, phone_no=phone_no, now=datetime.now())


@db_context
def _save_code(db, business_type, phone_no, code):
    expiration = datetime.now() + timedelta(minutes=_expiration_interval_in_minutes)
    fields = {
        'business_type': business_type,
        'phone_no': phone_no,
        'code': code,
        'expiration': expiration,
        'created_on': datetime.now()
    }
    db.insert('verification_code', **fields)


@db_context
def _is_unexpired_code(db, business_type, phone_no, code):
    return db.exists("""
            SELECT code FROM verification_code
              WHERE business_type = %(type)s
                AND phone_no = %(phone_no)s
                AND code = %(code)s
                AND expiration < %(now)s
          """, type=business_type, phone_no=phone_no, code=code, now=datetime.now())


def _generate_code(business_type, phone_no):
    code = _find_unexpired_code(business_type, phone_no)
    if code:
        return code

    code = strings.gen_rand_str(6, string.digits)
    _save_code(business_type, phone_no, code)

    return code


def _build_message(code):
    return "验证码%s，该验证码十分钟内有效。" % code