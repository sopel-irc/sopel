This folder contains contributed files for use with Sopel.

## tox

`tox.ini` and `toxfile.py` provide support for running Sopel's QA automation
against multiple Python versions locally. To run QA for all configured versions
in parallel, run `tox --conf contrib/ -p` from the repository root. You may
also want to set `TOX_CONFIG_FILE=path/to/contrib` to shorten that invocation
to just `tox -p`.

## githooks

Git hooks for development use
