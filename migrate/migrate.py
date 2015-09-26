#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import glob
import os
from ..util.dbs import from_db


MIGRATION_RECORD_TABLE = 'migrate_command_center'


def migrate(script_path):
    _try_create_migration_table()

    _clear_previous_failed_script_record()

    executed = [rec.script_name for rec in from_db().list('SELECT script_name FROM %s' % MIGRATION_RECORD_TABLE)]
    scripts = [script for script in glob.glob(os.path.join(script_path, '*.*'))]
    scripts.sort()
    for script in scripts:
        script_name = script[script.rfind('/') + 1:]
        if _is_valid_migration_script(script_name) and script_name not in executed:
            try:
                print('[MIGRATE] - execute: %s' % script_name)
                if _is_sql_script(script_name):
                    from_db().execute(open(script, 'r').read())
                elif _is_python_script(script_name):
                    _python_execute(script_path, script_name)
            except Exception:
                print('Error to execute script %s' % script_name)
                from_db().insert(MIGRATION_RECORD_TABLE, script_name=script_name, success=False)
                raise
            from_db().insert(MIGRATION_RECORD_TABLE, script_name=script_name)

    print('Database is up to date')


def _is_sql_script(script_name):
    return script_name.endswith('.sql')


def _is_python_script(script_name):
    return script_name.endswith('.py')


def _is_valid_migration_script(script_name):
    return script_name[0:3].isdigit() and (_is_sql_script(script_name) or _is_python_script(script_name))


def _clear_previous_failed_script_record():
    error_script = from_db().get_scalar('SELECT script_name FROM %s WHERE success = FALSE' % MIGRATION_RECORD_TABLE)
    if error_script:
        print("There is a failed script in last run: %s \nPlease make sure it is fixed." % error_script)
        from_db().execute('delete from ' + MIGRATION_RECORD_TABLE + ' where success = False')


def _try_create_migration_table():
    migrate_table_in_db = from_db().get("show tables like '{}' ".format(MIGRATION_RECORD_TABLE))
    if not migrate_table_in_db:
        from_db().execute(
            """
            CREATE TABLE %s(
                script_name VARCHAR(150) NOT NULL,
                success BOOLEAN NOT NULL DEFAULT TRUE,
                executed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """ % MIGRATION_RECORD_TABLE)


def _python_execute(script_path, script_name):
    file_path = os.path.join(script_path, script_name)
    execfile(file_path)
