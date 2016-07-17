This folder contains a Sopel backport from Debian Sid. I've also packaged 2 required packages. 
Please note that the 3 debs are not signed. You can follow the copy&paste instruction in case you feel more confortable in creating your own:

```
# XMLTODICT
dget -x http://http.debian.net/debian/pool/main/p/python-xmltodict/python-xmltodict_0.9.2-3.dsc
cd python-xmltodict-0.9.2
sudo mk-build-deps --install --remove && dch --local ~bpo80+ --distribution jessie-backports "Rebuild for jessie-backports." && fakeroot debian/rules binary && dpkg-buildpackage -us -uc
sudo dpkg -i ../python3-praw_3.3.0-1~bpo80+1_all.deb
cd ..
# PRAW
dget -x http://http.debian.net/debian/pool/main/p/praw/praw_3.3.0-1.dsc
cd praw-3.3.0
# correct dependences for python3-decorator in Jessie
sed -i s/3.4.2/3.4.0/g debian/control
sudo mk-build-deps --install --remove && dch --local ~bpo80+ --distribution jessie-backports "Rebuild for jessie-backports." && fakeroot debian/rules binary && dpkg-buildpackage -us -uc
sudo dpkg -i ../python3-praw_3.3.0-1~bpo80+1_all.deb
cd ..
# SOPEL
dget -x http://http.debian.net/debian/pool/main/s/sopel/sopel_6.3.1-1.dsc
cd sopel-6.3.1
# correct dependences for python3-decorator in Jessie
sed -i s/3.4.2/3.4.0/g debian/control
sudo mk-build-deps --install --remove && dch --local ~bpo80+ --distribution jessie-backports "Rebuild for jessie-backports." && fakeroot debian/rules binary && dpkg-buildpackage -us -uc
```
