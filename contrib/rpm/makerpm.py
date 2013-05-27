#!/usr/bin/python

import git
import sys
import os
import os.path
import time
from subprocess import *
import shutil

repo = git.Repo(os.getcwd())
head_hash = repo.head.commit.hexsha[:7]
now = time.strftime('%a %b %d %Y')
version = '3.3'
build = '0'
if len(sys.argv)>1:
    build = sys.argv[1]
print 'Generating archive...'
f = open('willie-%s.tar' % version, 'w')
repo.archive(f, prefix='willie-%s/' % version)
f.close()

print 'Building spec file..'
spec_in = open('willie.spec.in', 'r')
spec_out = open('willie.spec', 'w')
for line in spec_in:
    newline = line.replace('#GITTAG#', head_hash)
    newline = newline.replace('#BUILD#', build)
    newline = newline.replace('#LONGDATE#', now)
    newline = newline.replace('#VERSION#', version)
    spec_out.write(newline)
spec_in.close()
spec_out.close()
print 'Starting rpmbuild...'
cmdline = 'rpmbuild --define="%_specdir @wd@" --define="%_rpmdir @wd@" --define="%_srcrpmdir @wd@" --define="%_sourcedir @wd@" -ba willie.spec'.replace('@wd@', os.getcwd())
p = call(cmdline, shell=True)
for item in os.listdir('noarch'):
    os.rename(os.path.join('noarch', item), item)
print 'Cleaning...'
os.removedirs('noarch')
os.remove('willie.spec')
os.remove('willie-%s.tar' % version)
print 'Done'
