# coding=utf-8
"""Sopel's plugin jobs management.

.. versionadded:: 7.1

.. important::

    This is all fresh and new. Its usage and documentation is for Sopel core
    development and advanced developers. It is subject to rapid changes
    between versions without much (or any) warning.

    Do **not** build your plugin based on what is here, you do **not** need to.

"""
# Copyright 2020, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import absolute_import, division, print_function, unicode_literals

import itertools
import logging

from sopel import tools
from sopel.tools import jobs

LOGGER = logging.getLogger(__name__)


class Scheduler(jobs.Scheduler):
    """Plugin job scheduler.

    :param manager: bot instance passed to jobs as argument
    :type manager: :class:`sopel.bot.Sopel`

    Scheduler that stores plugin jobs and behaves like its
    :class:`parent class <sopel.tools.jobs.Scheduler>`.

    .. versionadded:: 7.1

    .. note::

        This class is a specific implementation of the scheduler, made to store
        jobs by their plugins and be used by the bot (its ``manager``).
        It follows a similar interface as the
        :class:`plugin rules manager <sopel.plugins.rules.Manager>`.

    .. important::

        This is an internal tool used by Sopel to manage its jobs. To register
        a job, plugin authors should use :func:`sopel.plugin.interval`.

    """
    def __init__(self, manager):
        super(Scheduler, self).__init__(manager)
        self._jobs = tools.SopelMemoryWithDefault(list)

    def register(self, job):
        with self._mutex:
            self._jobs[job.get_plugin_name()].append(job)
        LOGGER.debug('Job registered: %s', str(job))

    def unregister_plugin(self, plugin_name):
        """Unregister all the jobs from a plugin.

        :param str plugin_name: the name of the plugin to remove
        :return: the number of jobs unregistered for this plugin
        :rtype: int

        All jobs of that plugin will be removed from the scheduler.

        This method is thread safe. However, it won't cancel or stop any
        currently running jobs.
        """
        unregistered_jobs = 0
        with self._mutex:
            jobs_count = len(self._jobs[plugin_name])
            del self._jobs[plugin_name]
            unregistered_jobs = unregistered_jobs + jobs_count

        LOGGER.debug(
            '[%s] Successfully unregistered %d jobs',
            plugin_name,
            unregistered_jobs)

        return unregistered_jobs

    def clear_jobs(self):
        with self._mutex:
            self._jobs = tools.SopelMemoryWithDefault(list)

        LOGGER.debug('Successfully unregistered all jobs')

    def remove_callable_job(self, callable):
        plugin_name = getattr(callable, 'plugin_name', None)
        if not self._jobs[plugin_name]:
            return

        with self._mutex:
            self._jobs[plugin_name] = [
                job for job in self._jobs[plugin_name]
                if job._handler != callable
            ]

    def _get_ready_jobs(self, now):
        with self._mutex:
            jobs = [
                job for job in itertools.chain(*self._jobs.values())
                if job.is_ready_to_run(now)
            ]

        return jobs
