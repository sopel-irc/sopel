import pytest

# This file lists files which should be ignored by pytest
collect_ignore = ["setup.py", "sopel.py"]


def pytest_addoption(parser):
    parser.addoption('--offline', action='store_true', default=False)


def pytest_collection_modifyitems(config, items):
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
