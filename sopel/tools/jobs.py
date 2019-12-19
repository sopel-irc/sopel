# coding=utf-8
"""Sopel's Job Scheduler: internal tool for job management.

.. note::

    As of Sopel 5.3, :mod:`sopel.tools.jobs` is an internal tool. Therefore,
    it is not shown in the public documentation.

"""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import datetime
import logging
import threading
import time


LOGGER = logging.getLogger(__name__)


class JobScheduler(threading.Thread):
    """Calls jobs assigned to it in steady intervals.

    JobScheduler is a thread that keeps track of Jobs and calls them every
    X seconds, where X is a property of the Job.

    Thread safety is ensured with an internal mutex.

    It runs forever until the :attr:`stopping` event is set using the
    :meth:`stop` method.
    """
    def __init__(self, manager):
        threading.Thread.__init__(self)
        self.manager = manager
        self.stopping = threading.Event()
        self._jobs = []
        self._mutex = threading.Lock()

    def add_job(self, job):
        """Add a Job to the current job queue."""
        with self._mutex:
            self._jobs.append(job)

    def clear_jobs(self):
        """Clear current Job queue and start fresh."""
        with self._mutex:
            self._jobs = []

    def stop(self):
        """Ask the job scheduler to stop.

        The scheduler thread will stop its loop over jobs to process, but it
        won't join the thread, or clear its queue—this has to be done
        separately by the calling thread.
        """
        self.stopping.set()

    def remove_callable_job(self, callable):
        """Remove ``callable`` from the job queue."""
        with self._mutex:
            self._jobs = [
                job for job in self._jobs
                if job.func != callable
            ]

    def run(self):
        """Run forever until :attr:`stopping` event is set."""
        while not self.stopping.is_set():
            try:
                now = time.time()

                # Collect ready jobs by now
                for job in self._get_ready_jobs(now):
                    self._run_job(job)

                # Wait up to a second
                time_spent = time.time() - now
                wait_time = max(0, 1 - time_spent)
                if wait_time:
                    time.sleep(wait_time)
            except KeyboardInterrupt:
                # Do not block on KeyboardInterrupt
                LOGGER.debug('Job scheduler stopped by KeyboardInterrupt')
                raise
            except Exception as error:  # TODO: Be specific
                LOGGER.error('Error in job scheduler: %s', error)
                # Modules exceptions are caught earlier, so this is a bit
                # more serious. Options are to either stop the main thread
                # or continue this thread and hope that it won't happen
                # again.
                self.manager.on_scheduler_error(self, error)
                # Sleep a bit to guard against busy-looping and filling
                # the log with useless error messages.
                time.sleep(10.0)  # seconds

    def _get_ready_jobs(self, now):
        with self._mutex:
            jobs = [job for job in self._jobs if job.is_ready_to_run(now)]

        return jobs

    def _run_job(self, job):
        if job.func.thread:
            t = threading.Thread(
                target=self._call, args=(job,)
            )
            t.start()
        else:
            self._call(job)
        job.next()

    def _call(self, job):
        """Wrapper for collecting errors from modules."""
        try:
            job.func(self.manager)
        except KeyboardInterrupt:
            # Do not block on KeyboardInterrupt
            raise
        except Exception as error:  # TODO: Be specific
            LOGGER.error('Error while processing job: %s', error)
            self.manager.on_job_error(self, job, error)


class Job(object):
    """Holds information about when a function should be called next.

    :param int interval: number of seconds between calls to ``func``
    :param func: function to be called
    :type func: :term:`function`

    Job is a simple structure that holds information about when a function
    should be called next. They can be put in a priority queue, in which case
    the Job that should be executed next is returned.

    Calling :meth:`next` modifies the Job object with the next time it should
    execute. Current time is used to decide when the job should be executed
    next so it should only be called right after the function was called.
    """

    max_catchup = 5
    """How many seconds the job can get behind.

    This governs how much the scheduling of jobs is allowed to get behind
    before they are simply thrown out to avoid calling the same function too
    many times at once.
    """

    def __init__(self, interval, func):
        self.next_time = time.time() + interval
        self.interval = interval
        self.func = func

    def is_ready_to_run(self, at_time):
        """Check if this job is (or will be) ready to run at the given time.

        :param int at_time: Timestamp to check, in seconds
        :return: ``True`` if the job is (or will be) ready to run, ``False``
                 otherwise
        :rtype: boolean
        """
        return (self.next_time - at_time) <= 0

    def next(self):
        """Update ``self.next_time``, assuming ``func`` was just called.

        :return: a modified job object
        """
        last_time = self.next_time
        current_time = time.time()
        delta = last_time + self.interval - current_time

        if last_time > current_time + self.interval:
            # Clock appears to have moved backwards. Reset
            # the timer to avoid waiting for the clock to
            # catch up to whatever time it was previously.
            self.next_time = current_time + self.interval
        elif delta < 0 and abs(delta) > self.interval * self.max_catchup:
            # Execution of jobs is too far behind. Give up on
            # trying to catch up and reset the time, so that
            # will only be repeated a maximum of
            # self.max_catchup times.
            self.next_time = current_time - \
                self.interval * self.max_catchup
        else:
            self.next_time = last_time + self.interval

        return self

    def __str__(self):
        """Return a string representation of the Job object.

        Example result::

            <Job(2013-06-14 11:01:36.884000, 20s, <function upper at 0x02386BF0>)>

        """
        iso_time = str(datetime.datetime.fromtimestamp(self.next_time))
        return "<Job(%s, %ss, %s)>" % (iso_time, self.interval, self.func)
