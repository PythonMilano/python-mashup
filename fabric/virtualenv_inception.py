# -*- coding: utf-8 -*-
from __future__ import print_function
from fabric.api import local, lcd
from fabric.colors import green, yellow, cyan, red

PWD = local('pwd', capture=True)
PYTHON = '/.tmp/bin/python'
PIP = u'/.tmp/bin/pip'

def freeze(reset=False):
    print(cyan("Storing VSC links"))
    vcs = "{}\n{}".format(local("grep 'github.com' requirements_dev.txt", capture=True),
                          local("grep 'bitbucket.org' requirements_dev.txt", capture=True))
    vcs_links = {x.split('=')[1]: x for x in vcs.split('\n')}

    if reset:
        print(red("Deleting environment"))
        local('rm -rf .tmp')

    print(cyan("Starting create virtualenv"))
    local('virtualenv .tmp')
    local(u'{}{} install -r requirements_dev.txt -U'.format(PWD, PIP))
    local(u'{}{} freeze > requirements.txt'.format(PWD, PIP))

    print(yellow('Delete VCS lines from requirements.txt'))
    local("sed -i '/bitbucket.org/d' requirements.txt")
    local("sed -i '/github.com/d' requirements.txt")

    print(yellow('Replace package with vcs link'))
    for package, link in vcs_links.iteritems():
        local("sed -i '/{}/c{}' requirements.txt".format(package, link))

    check_requirements()

def check_requirements():
    print(cyan("Check requirements file"))
    local('{}{} download -r requirements.txt -d .chk_pkg'.format(PWD, PIP))
    local('rm -rf .chk_pkg')

def runtests():
    print(green('Running test suite'))
    local('{}{} manage.py test'.format(PWD, PYTHON))

def cooler():
    freeze(True)
    runtests()