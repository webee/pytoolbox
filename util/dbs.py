from __future__ import unicode_literals, print_function, division

from functools import wraps
from contextlib import contextmanager
from flask.ext.sqlalchemy import SQLAlchemy
import os
import re
from log import get_logger

_logger = get_logger(__name__, level=os.getenv('LOG_LEVEL', 'INFO'))


_db = SQLAlchemy(session_options={'autocommit': True})


def init_db(app):
    _db.init_app(app)


@contextmanager
def require_transaction_context():
    with _db.session.begin(subtransactions=True):
        yield DatabaseInterface()


def transactional(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with require_transaction_context() as _:
            return func(*args, **kwargs)

    return wrapper


def db_transactional(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if '_db' in kwargs:
            db = kwargs.pop('_db')
            return func(db, *args, **kwargs)
        if len(args) > 1 and isinstance(args[0], DatabaseInterface):
            return func(*args, **kwargs)
        with require_transaction_context() as db:
            return func(db, *args, **kwargs)

    return wrapper


@contextmanager
def require_db_context():
    yield DatabaseInterface()


def db_context(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if '_db' in kwargs:
            db = kwargs.pop('_db')
            return func(db, *args, **kwargs)
        if len(args) > 1 and isinstance(args[0], DatabaseInterface):
            return func(*args, **kwargs)
        with require_db_context() as db:
            return func(db, *args, **kwargs)

    return wrapper


PY_FORMAT_PATTERN = re.compile(r'(%\(([a-zA-Z_][a-zA-Z_0-9]*?)\)s)')


def _pyformat_to_named_paramstyle(sql):
    return PY_FORMAT_PATTERN.sub(r':\2', sql)


class DatabaseInterface(object):
    def sleep(self, duration):
        sql = "select SLEEP(%s)"
        self._execute(sql, (duration,))

    def has_rows(self, sql, **kwargs):
        return self.get_scalar('SELECT EXISTS ({})'.format(sql), **kwargs)

    def _execute(self, sql, *args, **kwargs):
        return _db.session.execute(_pyformat_to_named_paramstyle(sql), *args, **kwargs)

    def executemany(self, sql, seq_of_parameters):
        try:
            res = self._execute(sql, seq_of_parameters)
        except:
            _logger.exception(
                'failed to executemany statement: sql is %(sql)s and seq_of_parameters are %(seq_of_parameters)s', {
                    'sql': sql,
                    'seq_of_parameters': seq_of_parameters
                })
            raise
        return res.rowcount

    def execute(self, sql, *args, **kwargs):
        try:
            res = self._execute(sql, args or kwargs)
        except:
            _logger.exception('failed to execute statement: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': args or kwargs
            })
            raise
        return res.rowcount

    def exists(self, sql, **kwargs):
        return self.get_scalar('SELECT EXISTS ({})'.format(sql), **kwargs)

    def list(self, sql, *args, **kwargs):
        return self._query(sql, *args, **kwargs)

    def list_scalar(self, sql, *args, **kwargs):
        rows = self._query(sql, *args, **kwargs)
        if rows and len(rows[0]) > 1:
            raise Exception('More than one columns returned: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': args or kwargs
            })
        return [row[0] for row in rows]

    def get(self, sql, *args, **kwargs):
        rows = self._query(sql, *args, **kwargs)
        if not rows:
            _logger.debug('No rows returned: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': args or kwargs
            })
            return None
        if len(rows) > 1:
            _logger.warning('More than one rows returned: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': args or kwargs
            })
        return rows[0]

    def get_scalar(self, sql, *args, **kwargs):
        rows = self._query(sql, *args, **kwargs)
        if not rows:
            _logger.debug('No rows returned: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': args or kwargs
            })
            return None
        if len(rows) > 1:
            _logger.warning('More than one rows returned: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': args or kwargs
            })
        if len(rows[0]) > 1:
            raise Exception('More than one columns returned: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': args or kwargs
            })
        return rows[0][0]

    def insert(self, table, values=None, returns_id=False, **value_fields):
        if values:
            if isinstance(values, list):
                params = values[0]
            elif isinstance(values, dict):
                params = values
            else:
                raise ValueError("values should be list or dict, but get: {0}".format(type(values)))
        else:
            params = value_fields
        column_names = params.keys()

        fragments = ['INSERT INTO ', table,
                     ' (', ','.join(column_names), ' ) VALUES ',
                     '( ', ','.join([':%s' % c for c in column_names]), ' )']
        sql = ''.join(fragments)

        try:
            res = self._execute(sql, params)
        except:
            _logger.exception('failed to execute query: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': params
            })
            raise
        if returns_id:
            return res.lastrowid
        else:
            return res.rowcount

    def _query(self, sql, *args, **kwargs):
        try:
            res = self._execute(sql, args or kwargs)
        except:
            _logger.exception('failed to execute query: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': args or kwargs
            })
            raise
        return res.fetchall()


def from_db():
    return DatabaseInterface()
