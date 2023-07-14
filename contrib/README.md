This folder contains contributed files for use with Sopel.

## Service configuration

`sopel.service` and `sopel.cfg` are designed to be distributed by third parties
such as Fedora Project or Arch Linux.

`sopel.cfg` is a default configuration file for Sopel, that assumes the OS is
new enough to have `/run` and `/usr/lib/tmpfiles.d`

`sopel.service` is a systemd service file, and `sopel@.service` is a
multi-instance template. Both assume you are using a rather recent Sopel; that
the system has a special user named `sopel` designated for running the bot; and
that this user has access to `/run/sopel` (should be setup by `sopel.conf` in
`/usr/lib/tmpfiles.d`), `/var/log/sopel` and `/var/lib/sopel`

Default installation paths:

```
sopel.cfg	/etc
sopel.conf	/usr/lib/tmpfiles.d
sopel.service	/usr/lib/systemd/system
sopel@.service	/usr/lib/systemd/system
```

## tox

`tox.ini` and `toxfile.py` provide support for running Sopel's QA automation
against multiple Python versions locally. To run QA for all configured versions
in parallel, run `tox --conf contrib/ -p` from the repository root. You may
also want to set `TOX_CONFIG_FILE=path/to/contrib` to shorten that invocation
to just `tox -p`.

## githooks

Git hooks for development use
