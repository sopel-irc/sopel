"""Tests for Job Scheduler"""
from __future__ import generator_stop

import time

import pytest

from sopel import loader, module, plugin
from sopel.tools import jobs


TMP_CONFIG = """
[core]
owner = Bar
nick = Sopel
enable = coretasks
"""


class WithJobMockException(Exception):
    pass


@pytest.fixture
def mockconfig(configfactory):
    return configfactory('config.cfg', TMP_CONFIG)


def test_jobscheduler_stop(mockconfig, botfactory):
    mockbot = botfactory(mockconfig)
    scheduler = jobs.Scheduler(mockbot)
    assert not scheduler.stopping.is_set(), 'Stopping must not be set at init'

    scheduler.stop()
    assert scheduler.stopping.is_set(), 'Stopping must have been set'


def test_job_is_ready_to_run():
    now = time.time()
    job = jobs.Job([5])

    assert job.is_ready_to_run(now + 20)
    assert not job.is_ready_to_run(now - 20)


def test_job_str():
    job = jobs.Job([5])
    expected = '<Job (unknown) [5s]>'

    assert str(job) == expected


def test_job_str_intervals():
    job = jobs.Job([5, 60, 30])
    expected = '<Job (unknown) [5s, 30s, 60s]>'

    assert str(job) == expected


def test_job_str_handler():
    def handler():
        pass

    job = jobs.Job([5], handler=handler)
    expected = '<Job handler [5s]>'

    assert str(job) == expected


def test_job_str_handler_plugin():
    def handler():
        pass

    job = jobs.Job([5], plugin='testplugin', handler=handler)
    expected = '<Job testplugin.handler [5s]>'

    assert str(job) == expected


def test_job_str_label():
    def handler():
        pass

    job = jobs.Job([5], label='testhandler', handler=handler)
    expected = '<Job testhandler [5s]>'

    assert str(job) == expected


def test_job_str_label_plugin():
    def handler():
        pass

    job = jobs.Job(
        [5],
        label='testhandler',
        plugin='testplugin',
        handler=handler,
    )
    expected = '<Job testplugin.testhandler [5s]>'

    assert str(job) == expected


def test_job_str_label_plugin_intervals():
    def handler():
        pass

    job = jobs.Job(
        [5, 3600, 60],
        label='testhandler',
        plugin='testplugin',
        handler=handler,
    )
    expected = '<Job testplugin.testhandler [5s, 60s, 3600s]>'

    assert str(job) == expected


def test_job_next():
    timestamp = 523549800
    job = jobs.Job([5])
    job.next_times[5] = timestamp

    job.next(timestamp)
    assert job.next_times == {
        5: timestamp,
    }

    # assert idempotency
    job.next(timestamp)
    assert job.next_times == {
        5: timestamp,
    }

    # now the "current time" is in the future compared to the last time
    # so the next time should be last time + interval
    job.next(timestamp + 1)
    assert job.next_times == {
        5: timestamp + 5,
    }

    # let's reset this
    job.next_times[5] = timestamp

    # now the "current time" is bigger than last time + interval
    # so the next time will be the "current time"
    job.next(timestamp + 6)
    assert job.next_times == {
        5: timestamp + 6,
    }


def test_job_next_many():
    timestamp = 523549800
    job = jobs.Job([5, 30])
    job.next_times[5] = timestamp + 5
    job.next_times[30] = timestamp + 30

    # let's move 6s in the future, so past the 5s and before the 30s
    job.next(timestamp + 6)

    # the 5s interval => from timestamp + to timestamp + 2 * 5
    # the 30s interval => untouched, still in the future
    assert job.next_times == {
        5: timestamp + 10,
        30: timestamp + 30,
    }

    # assert idempotency
    job.next(timestamp + 6)
    assert job.next_times == {
        5: timestamp + 10,
        30: timestamp + 30,
    }

    # let's reset
    job.next_times[5] = timestamp + 5
    job.next_times[30] = timestamp + 30

    # now, the next time is bigger than last + 5s,
    # but still lower than last + 30s
    job.next(timestamp + 15)
    assert job.next_times == {
        5: timestamp + 15,
        30: timestamp + 30,
    }

    # let's reset again
    job.next_times[5] = timestamp + 5
    job.next_times[30] = timestamp + 30

    # and now, this time is bigger than both 5s and 30s
    job.next(timestamp + 35)
    assert job.next_times == {
        5: timestamp + 35,  # catching up
        30: timestamp + 60,  # next iteration as intended
    }


def test_job_from_callable(mockconfig):
    @module.interval(5)
    @plugin.label('testjob')
    def handler(manager):
        """The job's docstring."""
        return 'tested'

    loader.clean_callable(handler, mockconfig)
    handler.plugin_name = 'testplugin'

    job = jobs.Job.from_callable(mockconfig, handler)

    assert len(job.next_times.items()) == 1
    assert 5 in job.next_times
    assert job.is_threaded()
    assert job.intervals == set([5])
    assert job.execute(None) == 'tested'
    assert job.get_job_label() == 'testjob'
    assert job.get_plugin_name() == 'testplugin'
    assert job.get_doc() == "The job's docstring."
    assert str(job) == '<Job testplugin.testjob [5s]>'


def test_job_with():
    job = jobs.Job([5])
    # play with time: move 1s back in the future
    last_time = job.next_times[5] = time.time() - 1

    assert last_time is not None

    with job:
        assert job.is_running.is_set()
        assert job.next_times[5] == last_time

    # now the job is not running anymore, and its next time is last_time + 5s
    assert not job.is_running.is_set()
    assert job.next_times[5] == last_time + 5


def test_job_with_exception():
    job = jobs.Job([5])
    # play with time: move 1s back in the future
    last_time = job.next_times[5] = time.time() - 1

    assert last_time is not None

    with pytest.raises(WithJobMockException):
        # the "with job" must not prevent the exception from being raised up
        with job:
            assert job.is_running.is_set()
            assert job.next_times[5] == last_time
            # fake an exception while the job is running
            raise WithJobMockException

    # now the job is not running anymore, and its next time is last_time + 5s
    # even though an exception was raised!
    assert not job.is_running.is_set()
    assert job.next_times[5] == last_time + 5
