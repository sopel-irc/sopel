# coding=utf-8
"""Tests for Job Scheduler"""
from __future__ import unicode_literals, absolute_import, print_function, division

import datetime
import time

from sopel.tools import jobs


TMP_CONFIG = """
[core]
owner = Bar
nick = Sopel
enable = coretasks
"""


def test_jobscheduler_stop(configfactory, botfactory):
    mockbot = botfactory(configfactory('config.cfg', TMP_CONFIG))
    scheduler = jobs.JobScheduler(mockbot)
    assert not scheduler.stopping.is_set(), 'Stopping must not be set at init'

    scheduler.stop()
    assert scheduler.stopping.is_set(), 'Stopping must have been set'


def test_job_is_ready_to_run():
    now = time.time()
    job = jobs.Job(5, None)

    assert job.is_ready_to_run(now + 20)
    assert not job.is_ready_to_run(now - 20)


def test_job_string_representation():
    timestamp = 523549800
    job = jobs.Job(5, None)
    job.next_time = timestamp
    test_date = str(datetime.datetime.fromtimestamp(timestamp))
    expected = '<Job(%s, 5s, None)>' % test_date

    assert str(job) == expected
