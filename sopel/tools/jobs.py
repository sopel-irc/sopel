# coding=utf-8
"""Sopel's Job Scheduler: internal tool for job management.

.. important::

    As of Sopel 5.3, this is an internal tool used by Sopel to manage internal
    jobs and should not be used by plugin authors. Its usage and documentation
    is for Sopel core development and advanced developers. It is subject to
    rapid changes between versions without much (or any) warning.

"""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import absolute_import, division, print_function, unicode_literals

import inspect
import logging
import threading
import time


LOGGER = logging.getLogger(__name__)


class Scheduler(threading.Thread):
    """Generic Job Scheduler.

    :param object manager: manager passed to jobs as argument

    Scheduler is a :class:`thread <threading.Thread>` that keeps track of
    :class:`Jobs <Job>` and periodically checks which ones are ready to
    execute. When ready, their :meth:`~Job.execute` method is called, either
    in a separate thread or in the scheduler's thread (it depends on the
    job's :meth:`~Job.is_threaded` method).

    It can be started as any other thread::

        # on bot's startup
        scheduler = jobs.Scheduler(bot)
        scheduler.start()  # run the thread forever

    Then it runs forever until the :meth:`stop` method is called, usually when
    the bot shuts down.

    .. note::

        Thread safety is ensured with threading's :class:`~threading.Lock`
        and :class:`~threading.Event` when:

        * a job is :meth:`registered <register>` or
          :meth:`removed <remove_callable_job>`
        * the scheduler is :meth:`cleared <clear_jobs>` or
          :meth:`stopped <stop>`
        * the scheduler gets jobs that are ready for execution

        These actions can be performed while the scheduler is running.

    .. important::

        This is an internal tool used by Sopel to manage internal jobs and
        should not be used by plugin authors. Its usage and documentation is
        for Sopel core development and advanced developers. It is subject to
        rapid changes between versions without much (or any) warning.

    """
    def __init__(self, manager):
        threading.Thread.__init__(self)
        self.manager = manager
        """Job manager, used as argument for jobs."""
        self.stopping = threading.Event()
        """Stopping flag. See :meth:`stop`."""
        self._jobs = []
        self._mutex = threading.Lock()

    def register(self, job):
        """Register a Job to the current job queue.

        :param job: job to register
        :type job: :class:`sopel.tools.jobs.Job`

        This method is thread safe.
        """
        with self._mutex:
            self._jobs.append(job)
        LOGGER.debug('Job registered: %s', str(job))

    def clear_jobs(self):
        """Clear current Job queue and start fresh.

        This method is thread safe. However, it won't cancel or stop any
        currently running jobs.
        """
        with self._mutex:
            self._jobs = []

    def stop(self):
        """Ask the job scheduler to stop.

        The scheduler thread will stop its loop over jobs to process, but it
        won't join the thread, or clear its queue—this has to be done
        separately by the calling thread::

            scheduler.stop()  # ask the scheduler to stop
            scheduler.join()  # wait for the scheduler to actually stop

        Note that this won't cancel or stop any currently running jobs.
        """
        self.stopping.set()

    def remove_callable_job(self, callable):
        """Remove ``callable`` from the job queue.

        :param callable callable: the callable to remove
        :type callable: :term:`function`

        This method is thread safe. However, it won't cancel or stop any
        currently running jobs.
        """
        with self._mutex:
            self._jobs = [
                job for job in self._jobs
                if job._handler != callable
            ]

    def run(self):
        """Run forever until :meth:`stop` is called.

        This method waits at most a second between each iteration. At each step
        it retrieves the jobs that are ready for execution, and executes them.
        See the :meth:`Job.execute` method for more information.

        Internally, it loops forever until its :attr:`stopping` event is set.

        .. note::

            This should not be called directly, as it will be done by the
            :meth:`threading.Thread.start` method.

        """
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
                # Plugins exceptions are caught earlier, so this is a bit
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
        if job.is_threaded():
            # make sure the job knows it's running, even though the thread
            # isn't started yet.
            job.is_running.set()
            t = threading.Thread(
                target=self._call, args=(job,)
            )
            t.start()
        else:
            self._call(job)

    def _call(self, job):
        """Wrap the job's execution to handle its state and errors."""
        try:
            with job:
                job.execute(self.manager)
        except Exception as error:  # TODO: Be specific
            LOGGER.error('Error while processing job: %s', error)
            self.manager.on_job_error(self, job, error)


class Job(object):
    """Holds information about when a function should be called next.

    :param intervals: set of intervals; each is a number of seconds between
                      calls to ``handler``
    :type intervals: :term:`iterable`
    :param str plugin: optional plugin name to which the job belongs
    :param str label: optional label (name) for the job
    :param handler: function to be called when the job is ready to execute
    :type handler: :term:`function`
    :param str doc: optional documentation for the job

    Job is a simple structure that holds information about when a function
    should be called next. They are best used with a :class:`Scheduler`
    that will manage job execution when they are ready.

    The :term:`function` to execute is the ``handler``, which must be a
    callable with this signature::

        def handler(manager):
            # perform action periodically
            # return is optional

    The ``manager`` parameter can be any kind of object; usually it's an
    instance of :class:`sopel.bot.Sopel`.

    When a job is ready, you can execute it by calling its :meth:`execute`
    method (providing the appropriate ``manager`` argument)::

        if job.is_ready_to_run(time.time()):
            job.execute(manager)  # marked as running
            # "next times" have been updated; the job is not running

    In that case, ``execute`` takes care of the running state of the job.

    Alternatively, you can use a ``with`` statement to perform action before
    and/or after executing the job; in that case, the ``with`` statement takes
    precedence, and the :meth:`execute` method won't interfere::

        with job:
            # the job is now running, you can perform pre-execute action
            job.execute()  # execute the job's action, no state modification
            # the job is still marked as "running"
            # you can perform post-execute action

        # outside of the with statement, the job is not running anymore

    .. seealso::

        The :class:`sopel.plugins.jobs.Scheduler` class is specifically
        designed for plugins' jobs, expecting an instance of
        :class:`sopel.bot.Sopel` as a manager, and should be used to manipulate
        plugin jobs.

        In all other case, the :class:`sopel.tools.jobs.Scheduler` class is a
        generic job scheduler.

    """
    @classmethod
    def kwargs_from_callable(cls, handler):
        """Generate the keyword arguments to create a new instance.

        :param handler: callable used to generate keyword arguments
        :type handler: :term:`function`
        :return: a map of keyword arguments
        :rtype: dict

        This classmethod takes the ``handler``'s attributes to generate a map
        of keyword arguments for the class. This can be used by the
        :meth:`from_callable` classmethod to instantiate a new rule object.

        The expected attributes are the ones set by decorators from the
        :mod:`sopel.plugin` module.
        """

        return {
            'plugin': getattr(handler, 'plugin_name', None),
            'label': getattr(handler, 'rule_label', None),
            'threaded': getattr(handler, 'thread', True),
            'doc': inspect.getdoc(handler),
        }

    @classmethod
    def from_callable(cls, settings, handler):
        """Instantiate a Job from the bot's ``settings`` and a ``handler``.

        :param settings: bot's settings
        :type settings: :class:`sopel.config.Config`
        :param handler: callable used to instantiate a new job
        :type handler: :term:`function`
        """
        kwargs = cls.kwargs_from_callable(handler)
        return cls(
            set(handler.interval),
            handler=handler,
            **kwargs)

    def __init__(self,
                 intervals,
                 plugin=None,
                 label=None,
                 handler=None,
                 threaded=True,
                 doc=None):
        # scheduling
        now = time.time()
        self.intervals = set(intervals)
        """Set of intervals at which to execute the job."""
        self.next_times = dict(
            (interval, now + interval)
            for interval in self.intervals
        )
        """Tracking of when to execute the job next time."""

        # meta
        self._plugin_name = plugin
        self._label = label
        self._doc = doc

        # execution
        self._handler = handler
        self._threaded = bool(threaded)
        self.is_running = threading.Event()
        """Running flag: it tells if the job is running or not.

        This flag is set and cleared automatically by the :meth:`execute`
        method. It is also set and cleared when the job is used with the
        ``with`` statement::

            with job:
                # you do something before executing the job
                # this ensures that the job is marked as "running"

        .. note::

            When set manually or with the ``with`` statement, the
            :meth:`execute` method won't clear this attribute itself.

        """

    def __enter__(self):
        self.is_running.set()

    def __exit__(self, exc_type, exc_value, traceback):
        self.next(time.time())
        self.is_running.clear()

    def __str__(self):
        """Return a string representation of the Job object.

        Example result::

            <Job periodic_check [5s]>
            <Job periodic_check [60s, 3600s]>

        Example when the job is tied to a plugin::

            <Job reminder.remind_check [2s]>

        """
        try:
            label = self.get_job_label()
        except RuntimeError:
            label = '(unknown)'

        plugin_name = self.get_plugin_name()
        if plugin_name:
            label = '%s.%s' % (plugin_name, label)

        return "<Job %s [%s]>" % (
            label,
            ', '.join('%ss' % i for i in sorted(self.intervals)),
        )

    def get_plugin_name(self):
        """Get the job's plugin name.

        :rtype: str

        The job's plugin name will be used in various places to select,
        register, unregister, and manipulate the job based on its plugin, which
        is referenced by its name.
        """
        return self._plugin_name

    def get_job_label(self):
        """Get the job's label.

        :rtype: str

        A job can have a label, which can identify the job by string, the same
        way rules can be. This label can be used to manipulate or display the
        job's information in a more human-readable way. Note that the label has
        no effect on the job's execution.
        """
        if self._label:
            return self._label

        if self._handler is not None and self._handler.__name__:
            return self._handler.__name__

        raise RuntimeError('Undefined job label')

    def get_doc(self):
        """Get the job's documentation.

        :rtype: str

        A job's documentation is a short text that can be displayed to a user.
        """
        return self._doc

    def is_threaded(self):
        """Tell if the job's execution should be in a thread.

        :return: ``True`` if the execution should be in a thread,
                 ``False`` otherwise
        :rtype: bool
        """
        return self._threaded

    def is_ready_to_run(self, at_time):
        """Check if this job is (or will be) ready to run at the given time.

        :param int at_time: Timestamp to check, in seconds
        :return: ``True`` if the job is (or will be) ready to run, ``False``
                 otherwise
        :rtype: bool
        """
        return not self.is_running.is_set() and any(
            (next_time - at_time) <= 0
            for next_time in self.next_times.values()
        )

    def next(self, current_time):
        """Update :attr:`next_times`, assuming it executed at ``current_time``.

        :param int current_time: timestamp of the current time
        :return: a modified job object
        """
        for interval, last_time in list(self.next_times.items()):
            if last_time >= current_time:
                # no need to update this interval
                continue

            # if last time + interval is in the future, it's used
            # else, try to run it asap
            self.next_times[interval] = max(last_time + interval, current_time)

        return self

    def execute(self, manager):
        """Execute the job's handler and return its result.

        :param object manager: used as argument to the job's handler
        :return: the return value from the handler's execution

        This method executes the job's handler. It doesn't change its running
        state, as this must be done by the caller::

            with job:  # mark as running
                # before execution
                job.execute(manager)
                # after execution

        """
        return self._handler(manager)
