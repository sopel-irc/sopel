This folder contains sopel and sopel-default.cfg designed to be distributed by third parties such as FreeBSD.

`sopel-default.cfg` is a default configuration file for sopel. The -default prefix is mandatory and will be used as a 'profile'. The profiles may be changed with the variable `sopel_profiles` in `/etc/rc.conf`. For example:

```sh
sysrc sopel_profiles="profile1 profile2 profile3"
```

The configuration files should be `${sopel_confdir}/${sopel_prefix}profile1.cfg`, `${sopel_confdir}/${sopel_prefix}profile2.cfg` and `${sopel_confdir}/${sopel_prefix}profile3.cfg`. The variable `sopel_confdir` is the default configuration directory (by default `/usr/local/etc`). `sopel_prefix`is the prefix for all files (by default `sopel-`).

The service must be installed in `/usr/local/etc/rc.d`:

```sh
cp sopel /usr/local/etc/rc.d
chmod +x /usr/local/etc/rc.d/sopel
```

The default configuration file must be installed in ${sopel_confdir}. For example:

```sh
cp sopel-default.cfg /usr/local/etc
```

If you want to run sopel at startup, the variable `sopel_enable` must be set to `YES`:

```sh
sysrc sopel_enable="YES"
```

If you want to change the python version, the variable `sopel_interpreter` (by default `/usr/local/bin/python3.9`) must be changed.

Default values:

```sh
$ egrep -E '^: \$\{sopel_.+:=.+}' sopel
: ${sopel_enable:="NO"}
: ${sopel_piddir:="/var/run/sopel"}
: ${sopel_confdir:=/usr/local/etc}
: ${sopel_flags:=--config-dir "${sopel_confdir}"}
: ${sopel_program:="/usr/local/bin/sopel"}
: ${sopel_user:=${name}}
: ${sopel_interpreter:=/usr/local/bin/python3.9}
: ${sopel_profiles:=default}
: ${sopel_prefix:=sopel-}
: ${sopel_output:=/dev/null}
```
