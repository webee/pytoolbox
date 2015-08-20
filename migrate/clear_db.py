# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from ..util.dbs import from_db


def drop_all_tables(instance):
    from_db().execute(
        """
            SET FOREIGN_KEY_CHECKS = 0;
            SET @tables = NULL;
            SELECT GROUP_CONCAT(table_schema, '.', table_name) INTO @tables
	            FROM information_schema.`TABLES`
	            WHERE TABLE_SCHEMA = %(instance)s;

            SET @tables = CONCAT('DROP TABLE ', @tables);
            PREPARE stmt FROM @tables;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            SET FOREIGN_KEY_CHECKS = 1;
        """,
        instance=instance
    )