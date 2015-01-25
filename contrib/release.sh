#!/bin/sh
# Runs through the steps to release a Willie version. This is only useful to
# the people with permissions to do so, of course.
set -e
cd $(dirname $0)/..

version=$(python -c "import willie; print(willie.__version__)")
echo "Releasing Willie version $version."

echo "PyPI username:"
read pypi_user
echo "PyPI password:"
read pypi_pass
echo "willie.dftba.net username:"
read server_user

cat <<EOF > ~/.pypirc
[distutils]
index-servers =
    pypi

[pypi]
username:$pypi_user
password:$pypi_pass
EOF

echo "Building package and uploading to PyPI..."
./setup.py sdist upload --sign
rm ~/.pypirc

echo "Building docs..."
cd docs
make html

echo "Setting up folders on willie.dftba.net..."
ssh $server_user@willie.dftba.net "mkdir /var/www/willie/$version; rm /var/www/willie/docs; ln -s /var/www/willie/$version/docs /var/www/willie/docs"

echo "Uploading docs..."
scp -r build/html $server_user@willie.dftba.net:/var/www/willie/$version/docs

echo "Done!"
