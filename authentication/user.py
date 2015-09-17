# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from ..util.dbs import db_context


@db_context
def find_user(db, phone_no):
    return db.get("SELECT * FROM user WHERE phone_no = %(phone_no)s", phone_no=phone_no)


@db_context
def new_user(db, phone_no):
    fields = {
        'phone_no': phone_no
    }
    return db.insert('user', returns_id=True, **fields)
