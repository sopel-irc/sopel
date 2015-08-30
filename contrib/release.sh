#!/bin/sh
# Runs through the steps to release a Sopel version. This is only useful to
# the people with permissions to do so, of course.
set -e
cd $(dirname $0)/..

version=$(python -c "import sopel; print(sopel.__version__)")
echo "Releasing Sopel version $version."

echo "PyPI username:"
read pypi_user
echo "PyPI password:"
read pypi_pass
echo "sopel.chat username:"
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

echo "Setting up folders on sopel.chat..."
ssh $server_user@sopel.chat "mkdir /var/www/sopel/$version; rm /var/www/sopel/docs; ln -s /var/www/sopel/$version/docs /var/www/sopel/docs"

echo "Uploading docs..."
scp -r build/html $server_user@sopel.chat:/var/www/sopel/$version/docs

echo "Done!"
