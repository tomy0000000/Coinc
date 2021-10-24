#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-01
#

"""workflow-build [options] <workflow-dir>

Build Alfred Workflows.

Compile contents of <workflow-dir> to a ZIP file (with extension
`.alfredworkflow`).

The name of the output file is generated from the workflow name,
which is extracted from the workflow's `info.plist`. If a `version`
file is contained within the workflow directory, it's contents
will be appended to the compiled workflow's filename.

Usage:
    workflow-build [-v|-q|-d] [-f] [-o <outputdir>] <workflow-dir>...
    workflow-build (-h|--version)

Options:
    -o, --output=<outputdir>    directory to save workflow(s) to
                                default is current working directory
    -f, --force                 overwrite existing files
    -h, --help                  show this message and exit
    -V, --version               show version number and exit
    -q, --quiet                 only show errors and above
    -v, --verbose               show info messages and above
    -d, --debug                 show debug messages

"""

from __future__ import print_function

from contextlib import contextmanager
import logging
import os
import plistlib
import re
import shutil
import string
from subprocess import check_call, CalledProcessError
import sys
from tempfile import mkdtemp
from unicodedata import normalize

from docopt import docopt

__version__ = "0.6"
__author__ = "Dean Jackson <deanishe@deanishe.net>"

DEFAULT_LOG_LEVEL = logging.WARNING

# Characters permitted in workflow filenames
OK_CHARS = set(string.ascii_letters + string.digits + '-.')

EXCLUDE_PATTERNS = [
    '.*',
    '*.pyc',
    '*.log',
    '*.acorn',
    '*.swp',
    '*.bak',
    '*.sublime-project',
    '*.sublime-workflow',
    '*.git',
    '*.dist-info',
    '*.egg-info',
    '__pycache__',
]

log = logging.getLogger('[%(levelname)s] %(message)s')
logging.basicConfig(format='', level=logging.DEBUG)


@contextmanager
def chdir(dirpath):
    """Context-manager to change working directory."""
    startdir = os.path.abspath(os.curdir)
    os.chdir(dirpath)
    log.debug('cwd=%s', dirpath)

    yield

    os.chdir(startdir)
    log.debug('cwd=%s', startdir)


@contextmanager
def tempdir():
    """Context-manager to create and cd to a temporary directory."""
    startdir = os.path.abspath(os.curdir)
    dirpath = mkdtemp()
    try:
        yield dirpath
    finally:
        shutil.rmtree(dirpath)


def safename(name):
    # remove non-ASCII
    s = normalize('NFKD', name)
    b = s.encode('us-ascii', 'ignore')

    clean = []
    for c in b:
        char = chr(c)
        if char in OK_CHARS:
            clean.append(char)
        else:
            clean.append('-')

    return re.sub(r'-+', '-', ''.join(clean)).strip('-')


def build_workflow(workflow_dir, outputdir, overwrite=False, verbose=False):
    """Create an .alfredworkflow file from the contents of `workflow_dir`."""
    with tempdir() as dirpath:
        tmpdir = os.path.join(dirpath, 'workflow')
        shutil.copytree(workflow_dir, tmpdir,
                        ignore=shutil.ignore_patterns(*EXCLUDE_PATTERNS))

        with chdir(tmpdir):
            # ------------------------------------------------------------
            # Read workflow metadata from info.plist
            with open("info.plist", "rb") as fp:
                info = plistlib.load(fp)
            version = info.get('version')
            name = safename(info['name'])
            zippath = os.path.join(outputdir, name)
            if version:
                zippath = '{}-{}'.format(zippath, version)

            zippath += '.alfredworkflow'

            # ------------------------------------------------------------
            # Remove unexported vars from info.plist

            for k in info.get('variablesdontexport', {}):
                info['variables'][k] = ''

            with open("info.plist", "wb") as fp:
                plistlib.dump(info, fp)
            # ------------------------------------------------------------
            # Build workflow
            if os.path.exists(zippath):
                if overwrite:
                    log.info('overwriting existing workflow')
                    os.unlink(zippath)
                else:
                    log.error('File "%s" exists. Use -f to overwrite', zippath)
                    return False

            # build workflow
            command = ['zip', '-r']
            if not verbose:
                command.append(u'-q')

            command.extend([zippath, '.'])

            log.debug('command=%r', command)

            try:
                check_call(command)
            except CalledProcessError as err:
                log.error('zip exited with %d', err.returncode)
                return False

            log.info('wrote %s', zippath)

    return True


def main(args=None):
    """Run CLI."""
    # ------------------------------------------------------------
    # CLI flags
    args = docopt(__doc__, version=__version__)
    if args.get('--verbose'):
        log.setLevel(logging.INFO)
    elif args.get('--quiet'):
        log.setLevel(logging.ERROR)
    elif args.get('--debug'):
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(DEFAULT_LOG_LEVEL)

    log.debug('log level=%s', logging.getLevelName(log.level))
    log.debug('args=%r', args)

    # Build options
    force = args['--force']
    outputdir = os.path.abspath(args['--output'] or os.curdir)
    workflow_dirs = [os.path.abspath(p) for p in args['<workflow-dir>']]
    verbose = log.level == logging.DEBUG

    log.debug(u'outputdir=%r, workflow_dirs=%r', outputdir, workflow_dirs)

    # ------------------------------------------------------------
    # Build workflow(s)
    errors = False
    for path in workflow_dirs:
        ok = build_workflow(path, outputdir, force, verbose)
        if not ok:
            errors = True

    if errors:
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))