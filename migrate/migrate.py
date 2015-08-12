#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import glob
import os
from ..util.dbe import from_db

MIGRATION_RECORD_TABLE = 'migrate_command_center'

def migrate(script_path):
    try_create_migration_table()

    clear_previous_failed_script_record()

    executed = [rec.script_name for rec in from_db().list('SELECT script_name FROM %s' % migrate_table)]
    scripts = [script for script in glob.glob(os.path.join(script_path, '*.*'))]
    scripts.sort()
    for script in scripts:
        script_name = script[script.rfind('/') + 1:]
        if is_valid_migration_script(script_name) and script_name not in executed:
            try:
                print('[MIGRATE] - execute: %s' % script_name)
                from_db().execute(open(script, 'r').read())
            except Exception:
                print('Error to execute script %s' % script_name)
                from_db().execute('INSERT INTO ' + migrate_table + '(script_name, success) VALUES(%s, FALSE)', (script_name,))
                raise
            from_db().execute('INSERT INTO ' + migrate_table + '(script_name) VALUES(%s)', (script_name,))

    print('Database is up to date')


def is_valid_migration_script(script_name):
    return script_name[0:3].isdigit() and script_name.endswith('.sql')


def clear_previous_failed_script_record():
    error_script = from_db().get_scalar('SELECT script_name FROM %s WHERE success = FALSE' % migrate_table)
    if error_script:
        print("There is a failed script in last run: %s \nPlease make sure it is fixed." % error_script)
        from_db().execute('delete from ' + migrate_table + ' where success = False')


def try_create_migration_table():
    migrate_table_in_db = from_db().get("show tables like '{}' ".format(migrate_table))
    if not migrate_table_in_db:
        from_db().execute(
            """
            CREATE TABLE %s(
                script_name VARCHAR(150) NOT NULL,
                success BOOLEAN NOT NULL DEFAULT TRUE,
                executed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """ % migrate_table)


if __name__ == '__main__':
    migrate('migration')

