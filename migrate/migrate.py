#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import glob
import os
from ..util.dbe import from_db


def migrate(script_path):
    migrate_table = 'migrate_command_center'
    print('Begin to migrate ...')
    print("Migrate table is '%s'" % migrate_table)

    try:
        from_db().execute(
            """
            CREATE TABLE %s(
                script_name VARCHAR(150) NOT NULL,
                success BOOLEAN NOT NULL DEFAULT TRUE,
                executed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """ % migrate_table)
    except Exception as err:
        if 'already exists' not in str(err):
            raise

    error_script = from_db().get_scalar('SELECT script_name FROM %s WHERE success = FALSE' % migrate_table)
    if error_script:
        print("There is a failed script in last run: %s \nPlease make sure it is fixed." % error_script)
        from_db().execute('delete from ' + migrate_table + ' where success = False')

    executed = [rec.script_name for rec in from_db().list('SELECT script_name FROM %s' % migrate_table)]
    scripts = [script for script in glob.glob(os.path.join(script_path, '*.*'))]
    scripts.sort()
    for script in scripts:
        script_name = script[script.rfind('/') + 1:]
        if script_name not in executed:
            try:
                print('[MIGRATE] - execute: %s' % script_name)
                if script_name.endswith('.sql'):
                    from_db().execute(open(script, 'r').read())
                else:
                    raise Exception('Unsupported migrate script: %s' % script_name)
            except Exception:
                print('Error to execute script %s' % script_name)
                from_db().execute('INSERT INTO ' + migrate_table + '(script_name, success) VALUES(%s, FALSE)',
                                  (script_name,))
                raise
            from_db().execute('INSERT INTO ' + migrate_table + '(script_name) VALUES(%s)', (script_name,))

    print('System is up to date')


if __name__ == '__main__':
    migrate('migrate/schema')

