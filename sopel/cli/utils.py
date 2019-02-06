# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import os


def enumerate_configs(config_dir, extension='.cfg'):
    """List configuration files from ``config_dir`` with ``extension``

    :param str config_dir: path to the configuration directory
    :param str extension: configuration file's extension (default to ``.cfg``)
    :return: a list of configuration filenames found in ``config_dir`` with
             the correct ``extension``
    :rtype: list

    Example::

        >>> from sopel import cli, config
        >>> os.listdir(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'extra.ini', 'module.cfg', 'README']
        >>> cli.enumerate_configs(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'module.cfg']
        >>> cli.enumerate_configs(config.DEFAULT_HOMEDIR, '.ini')
        ['extra.ini']

    """
    if not os.path.isdir(config_dir):
        return

    for item in os.listdir(config_dir):
        if item.endswith(extension):
            yield item
