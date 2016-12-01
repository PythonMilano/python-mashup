# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
from datetime import datetime

from fabric.api import local, run, env, task, lcd, settings
from fabric.colors import green, cyan, red, yellow, white
from fabric.context_managers import prefix

# Configurazioni degli ambienti di produzione e collaudo
env.containers = {
    'cont1': 'user@IP',
}

env.forward_agent = True


###############################################################################
# DEPLOY TOOLS
###############################################################################

@task(alias='host')
def container(hostname='gs1'):
    """
    Specifica il nome del container su cui effettuare i task, definiti in `env.containers`
    Va usato per settare l'host su cui eseguire i task remoti
    :param hostname: nome del container definito in `env.containers`
    :return:
    """
    print(white("\nSet default host to {}\n".format(hostname), bold=True))
    env.hosts = [env.containers.get(hostname)]
    env['venv_name'] = hostname


@task
def deploy(branch='default'):
    """
    Deploy applicazione su container
    es: $ fab container:gs1dev2 deploy:feature/new-feature
    :param branch: nome del branch per il deploy
    :return:
    """
    with prefix("workon {}".format(env.venv_name)):
        print(white("\nPulling and updating from hg\n", bold=True))
        run("hg pull")
        run("hg up {}".format(branch))
        print(red("\nDeleting *.pyc files\n"))
        run("find . -name '*.pyc' -delete")
        print(green("\nInstall packages\n"))
        run("pip install -r requirements.txt -U")
        print(green("\nCollecting static files\n"))
        run("python manage.py collectstatic --noinput --clear")
        print(yellow("\nRunning migrations\n"))
        run("python manage.py migrate")
        print(red("\nRestarting vassal\n"))
        run("touch ~/vassals/{}.ini".format(env.venv_name))
        print(green("\nSuccessful deploy on {}\n".format(env.venv_name), bold=True))


###############################################################################
# TEST TOOLS
###############################################################################

def _update_pip_setuptools():
    """
    Update pip e setuptools, helper function
    :return:
    """
    print(white("Update pip and setuptools\n"))
    local("pip install pip -U")
    local("pip install setuptools -U")


@task
def wipeenv():
    """
    Porting della funzione `wipeenv` di `virtualenvwrapper.sh`
    Preserva fabric per lanciare i successivi task
    :return:
    """
    req_file = 'req_freeze.txt'
    print(red("\nWipe environment\n", bold=True))
    with settings(warn_only=True):
        result = local(
            "pip freeze | egrep -v -i '(distribute|wsgiref|fabric|paramiko|pycrypto|ecdsa)' > {}".format(req_file))
        if result.return_code == 0:
            print(yellow("\nUninstalling packages:\n"))
            local("cat {}".format(req_file))
            local("pip uninstall -y $(cat {} | grep -v '^-f' | sed 's/>/=/g' | cut -f1 -d=)".format(req_file))
        else:
            print(yellow("\nNothing to remove\n", bold=True))
    local("rm -f {}".format(req_file))


@task(alias='pip')
def requirements():
    """
    Installa i packages dal file `requirements.txt`
    :return:
    """
    print(white("\nRunning pip install\n", bold=True))
    local("pip install -r requirements.txt -U --allow-all-external --process-dependency-links "
          "--trusted-host bitbucket.org --trusted-host github.com --no-cache-dir")


@task()
def test():
    """
    Fa girare i test nel virtualenv attivo
    :return:
    """
    print(green("\nRunning test suite\n", bold=True))
	local("python manage.py test")


@task()
def release():
    """
    Fa girare tutti i test in un ambiente virtualenv pulito
    Utile da far girare prima del deploy
    :return:
    """
    wipeenv()
    _update_pip_setuptools()
    requirements()
    print(green("\nRunning test suite\n", bold=True))
	local("python manage.py test")


@task(alias='wb')
def whichbranch():
    """
    Verifica quale branch sia attivo nel container
    :return:
    """
    with prefix("workon {}".format(env.venv_name)):
        run('hg branch')
