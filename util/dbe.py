from __future__ import unicode_literals, print_function, division

from functools import wraps
from contextlib import contextmanager

import os
import sqlalchemy
from sqlalchemy import create_engine
from log import get_logger

_logger = get_logger(__name__, level=os.getenv('LOG_LEVEL', 'INFO'))

_engine = None


@contextmanager
def require_transaction_context():
    with _engine.begin():
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


class DatabaseInterface(object):
    def sleep(self, duration):
        sql = "select SLEEP(%s)"
        self._execute(sql, (duration,))

    def has_rows(self, sql, **kwargs):
        return self.get_scalar('SELECT EXISTS ({})'.format(sql), **kwargs)

    def _execute(self, *args, **kwargs):
        return _engine.execute(*args, **kwargs)

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
                column_names = values[0].keys()
                fields = [tuple(value[n] for n in column_names) for value in values]
            elif isinstance(values, dict):
                column_names = values.keys()
                fields = tuple(values[n] for n in column_names)
            else:
                raise ValueError("values should be list or dict, but get: {0}".format(type(values)))
        else:
            column_names = list(value_fields.keys())
            fields = tuple(value_fields[n] for n in column_names)

        fragments = ['INSERT INTO ', table,
                     ' (', ','.join(column_names), ' ) VALUES ',
                     '( ', ','.join(['%s'] * len(column_names)), ' )']
        sql = ''.join(fragments)

        try:
            res = self._execute(sql, fields)
        except:
            _logger.exception('failed to execute query: sql is %(sql)s and args are %(args)s', {
                'sql': sql,
                'args': fields
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


def create_db_engine(db_host, db_port, db_instance, username, password):
    _logger.info('connecting to database {}@{}:{}'.format(db_instance, db_host, db_port))
    global _engine
    url = sqlalchemy.engine.url.URL('mysql', username, password, db_host, db_port, db_instance, {'charset': 'utf8'})
    _engine = create_engine(url, pool_size=30, max_overflow=60, pool_recycle=3600, pool_timeout=60, strategy='threadlocal')


def from_db():
    return DatabaseInterface()
