# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import copy
import datetime
import sys
import threading
import time

if sys.version_info.major >= 3:
    unicode = str
    basestring = str
    py3 = True
else:
    py3 = False

try:
    import Queue
except ImportError:
    import queue as Queue


class released(object):
    """A context manager that releases a lock temporarily."""
    def __init__(self, lock):
        self.lock = lock

    def __enter__(self):
        self.lock.release()

    def __exit__(self, _type, _value, _traceback):
        self.lock.acquire()


class PriorityQueue(Queue.PriorityQueue):
    """A priority queue with a peek method."""
    def peek(self):
        """Return a copy of the first element without removing it."""
        self.not_empty.acquire()
        try:
            while not self._qsize():
                self.not_empty.wait()
            # Return a copy to avoid corrupting the heap. This is important
            # for thread safety if the object is mutable.
            return copy.deepcopy(self.queue[0])
        finally:
            self.not_empty.release()


class JobScheduler(threading.Thread):

    """Calls jobs assigned to it in steady intervals.

    JobScheduler is a thread that keeps track of Jobs and calls them every
    X seconds, where X is a property of the Job. It maintains jobs in a
    priority queue, where the next job to be called is always the first
    item.
    Thread safety is maintained with a mutex that is released during long
    operations, so methods add_job and clear_jobs can be safely called from
    the main thread.

    """

    min_reaction_time = 30.0  # seconds
    """How often should scheduler checks for changes in the job list."""

    def __init__(self, bot):
        """Requires bot as argument for logging."""
        threading.Thread.__init__(self)
        self.bot = bot
        self._jobs = PriorityQueue()
        # While PriorityQueue it self is thread safe, this mutex is needed
        # to stop old jobs being put into new queue after clearing the
        # queue.
        self._mutex = threading.Lock()
        # self.cleared is used for more fine grained locking.
        self._cleared = False

    def add_job(self, job):
        """Add a Job to the current job queue."""
        self._jobs.put(job)

    def clear_jobs(self):
        """Clear current Job queue and start fresh."""
        if self._jobs.empty():
            # Guards against getting stuck waiting for self._mutex when
            # thread is waiting for self._jobs to not be empty.
            return
        with self._mutex:
            self._cleared = True
            self._jobs = PriorityQueue()

    def run(self):
        """Run forever."""
        while True:
            try:
                self._do_next_job()
            except Exception:  # TODO: Be specific
                # Modules exceptions are caught earlier, so this is a bit
                # more serious. Options are to either stop the main thread
                # or continue this thread and hope that it won't happen
                # again.
                self.bot.error()
                # Sleep a bit to guard against busy-looping and filling
                # the log with useless error messages.
                time.sleep(10.0)  # seconds

    def _do_next_job(self):
        """Wait until there is a job and do it."""
        with self._mutex:
            # Wait until the next job should be executed.
            # This has to be a loop, because signals stop time.sleep().
            while True:
                job = self._jobs.peek()
                difference = job.next_time - time.time()
                duration = min(difference, self.min_reaction_time)
                if duration <= 0:
                    break
                with released(self._mutex):
                    time.sleep(duration)

            self._cleared = False
            job = self._jobs.get()
            with released(self._mutex):
                if job.func.thread:
                    t = threading.Thread(
                        target=self._call, args=(job.func,)
                    )
                    t.start()
                else:
                    self._call(job.func)
                job.next()
            # If jobs were cleared during the call, don't put an old job
            # into the new job queue.
            if not self._cleared:
                self._jobs.put(job)

    def _call(self, func):
        """Wrapper for collecting errors from modules."""
        # Sopel.bot.call is way too specialized to be used instead.
        try:
            func(self.bot)
        except Exception:  # TODO: Be specific
            self.bot.error()


class Job(object):

    """Hold information about when a function should be called next.

    Job is a simple structure that hold information about when a function
    should be called next.
    They can be put in a priority queue, in which case the Job that should
    be executed next is returned.

    Calling the method next modifies the Job object for the next time it
    should be executed. Current time is used to decide when the job should
    be executed next so it should only be called right after the function
    was called.

    """

    max_catchup = 5
    """
    This governs how much the scheduling of jobs is allowed
    to get behind before they are simply thrown out to avoid
    calling the same function too many times at once.
    """

    def __init__(self, interval, func):
        """Initialize Job.

        Args:
            interval: number of seconds between calls to func
            func: function to be called

        """
        self.next_time = time.time() + interval
        self.interval = interval
        self.func = func

    def next(self):
        """Update self.next_time with the assumption func was just called.

        Returns: A modified job object.

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

    def __cmp__(self, other):
        """Compare Job objects according to attribute next_time."""
        return self.next_time - other.next_time

    if py3:
        def __lt__(self, other):
            return self.next_time < other.next_time

        def __gt__(self, other):
            return self.next_time > other.next_time

    def __str__(self):
        """Return a string representation of the Job object.

        Example result:
            <Job(2013-06-14 11:01:36.884000, 20s, <function upper at 0x02386BF0>)>

        """
        iso_time = str(datetime.fromtimestamp(self.next_time))
        return "<Job(%s, %ss, %s)>" % \
            (iso_time, self.interval, self.func)

    def __iter__(self):
        """This is an iterator. Never stops though."""
        return self
