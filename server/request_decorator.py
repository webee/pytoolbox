# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from functools import wraps
from flask import request
from . import response


def json_data(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.content_length == 0:
            return response.bad_request("No content.")

        if 'application/json' not in request.content_type:
            return response.bad_request("Request content type isn't JSON.")

        data = request.json
        kwargs['data'] = data
        return func(*args, **kwargs)

    return wrapper