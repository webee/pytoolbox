# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from flask import Response, json
import decimal
import datetime


def updated(ids):
    return ok(ids=ids)


def list_data(items):
    js = _dumps(items)
    return Response(js, status=200, mimetype='application/json')


def ok(*args, **kwargs):
    if len(args) > 0:
        return _response(200, args[0])
    return _response(200, kwargs)


def created(id, **kwargs):
    params = kwargs or {}
    params['id'] = id
    return _response(201, params)


def accepted(id):
    return _response(202, {'id': id})


def no_content():
    return _response(204)


def forbidden(message):
    return _response(403, {'error': message})


def not_found(params=None):
    return _response(404, {'error': 'not found', 'params': params})


def bad_request(message, **request_params):
    return _response(400, {'error': message, 'params': str(request_params)})


def gone():
    return _response(410)


def _response(status_code, obj=None):
    js = _dumps(obj if obj else {})
    return Response(js, status=status_code, mimetype='application/json')


def _dumps(obj):
    import json as native_json
    class JsonEncoderForNative(native_json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float(o)
            if isinstance(o, datetime.datetime):
                return o.isoformat()
            if isinstance(o, datetime.date):
                return o.strftime('%Y-%m-%d')
            return super(JsonEncoder, self).default(o)

    return native_json.dumps(obj, cls=JsonEncoderForNative)


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o, datetime.date):
            return o.strftime('%Y-%m-%d')
        return super(JsonEncoder, self).default(o)
