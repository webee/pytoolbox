# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from fabric import api as fab
from fabric.contrib.files import exists, upload_template
from os import path, environ
from ..util.attr_dict import AttrDict
from ..util.root import root_path


class Deployment(object):
    def __init__(self, git_repo, project_dir, server_name, site_name, supervisord_config_path, supervisord_remote_dir,
                 context=None):
        self._git_repo = git_repo
        self._project_dir = project_dir
        self._server_name = server_name
        self._site_name = site_name
        self._supervisord = AttrDict(config_path=supervisord_config_path,
                                     context=context if context else {},
                                     remote_dir=supervisord_remote_dir)

    def do(self, server_host, user, pip_install=False, bower_install=False, db_migration=False):
        fab.use_ssh_config = True
        fab.env.host_string = '{0}@{1}'.format(user, server_host)
        fab.env.user = user

        self._update_codes()
        self._update_supervisord_config(self._default_context(user))

        self._stop_api_server(self._server_name)
        if pip_install:
            self._pip_install()
        if bower_install:
            self._bower_install()
        if db_migration:
            self._migrate_db()
        self._start_api_server(self._server_name)

    def _default_context(self, user):
        return {
            'server_name': self._server_name,
            'site_dir': self._site_dir(),
            'project_dir': self._project_dir,
            'user': user
        }

    def _update_codes(self):
        repo_dir = self._project_dir

        if not exists(repo_dir):
            self._clone_codes(self._git_repo)
        else:
            self._pull_codes(repo_dir)

    def _clone_codes(self, git_repo):
        parent_dir = path.abspath(path.dirname(self._project_dir))
        with fab.cd(parent_dir):
            fab.run('git clone --recursive {0}'.format(git_repo))
        self._create_venv(self._site_dir())

    def _create_venv(self, base_dir):
        with fab.cd(base_dir):
            fab.run('virtualenv venv')

    def _pull_codes(self, base_dir):
        with fab.cd(base_dir):
            fab.run('git pull --ff-only origin master')
        with fab.cd(path.join(base_dir, 'libraries/pytoolbox')):
            fab.run('git pull --ff-only origin master')

    def _update_supervisord_config(self, default_context):
        context = default_context.copy()
        context.update(self._supervisord.context)
        self._upload_supervisord_conf(self._supervisord.config_path, context)

        fab.run('sudo /usr/local/bin/supervisorctl reread')
        fab.run('sudo /usr/local/bin/supervisorctl update')

    def _upload_supervisord_conf(self, template_relative_path, context):
        root = root_path(self._site_name)
        template_file_path = path.join(root, template_relative_path)
        template_file_name = path.basename(template_file_path)
        template_dir = path.dirname(template_file_path)
        remote_path = '{0}/{1}.conf'.format(self._supervisord.remote_dir, self._server_name)

        upload_template(template_file_name, remote_path, context=context, use_jinja=True, template_dir=template_dir,
                        use_sudo=True, backup=False)

    def _stop_api_server(self, name):
        fab.run('sudo /usr/local/bin/supervisorctl stop {}'.format(name))

    def _start_api_server(self, name):
        fab.run('sudo /usr/local/bin/supervisorctl start {}'.format(name))

    def _migrate_db(self):
        with fab.cd(self._site_dir()), fab.prefix('source venv/bin/activate'):
            fab.run('python src/manager.py -e {0} migrate'.format(environ['ENV']))

    def _pip_install(self):
        with fab.cd(self._site_dir()), fab.prefix('source venv/bin/activate'):
            fab.run('pip install -r requirements.txt')

    def _bower_install(self):
        with fab.cd(self._site_dir()):
            fab.run('bower install')

    def _site_dir(self):
        return path.join(self._project_dir, self._site_name)
