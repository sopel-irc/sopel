#!/bin/sh -x
# This script performs most of the same steps as the Travis build. The build
# doesn't actually run this script, since it uses Travis's ability to report
# the 2.7 and 3.x builds separately.

clean () {
    find . -name '*.pyc' -exec rm {} \;
    rm -rf build __pycache__ test/__pycache__
}
if test -z $VIRTUAL_ENV; then
    SUDO=sudo
fi

clean
$SUDO pip2 install -r dev-requirements.txt
python2.7 pytest_run.py
clean
$SUDO pip3 install -r dev-requirements.txt
python3 pytest_run.py
./checkstyle.sh
