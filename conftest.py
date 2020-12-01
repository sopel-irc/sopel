import os

import pytest

# This file lists files which should be ignored by pytest
collect_ignore = ["setup.py", "sopel.py"]


def pytest_addoption(parser):
    parser.addoption('--offline', action='store_true', default=False)


def pytest_collection_modifyitems(config, items):
    # first, make sure things run in order
    # needed to mitigate some weird quirk of vcrpy on Python 3.3, no idea why
    items.sort(key=lambda item: (item.fspath or '') + '::' + item.name)

    # rest of this is handling for "offline mode"
    if not config.getoption('--offline'):
        # nothing to skip
        return

    skip_online = pytest.mark.skip(reason='deactivated when --offline is used')
    for item in items:
        if 'online' in item.keywords:
            item.add_marker(skip_online)


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'online: for tests that require online access. '
        'Use --offline to skip them.')


@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Override VCR.py cassette save location, to keep them out of code folders
    parts = request.module.__name__.split('.')
    if parts[0] == 'sopel':
        # We know it's part of Sopel...
        parts = parts[1:]
    return os.path.join('test', 'vcr', *parts)


@pytest.fixture
def vcr_cassette_path(request, vcr_cassette_name):
    # pytest-vcr 0.3.0 looks for this fixture name
    # remove when killing off Python 3.3 support
    return os.path.join(vcr_cassette_dir(request), vcr_cassette_name)
