# Upload package to PyPi.org

## Install prereqs

    python3 -m pip install --user --upgrade setuptools wheel

## Create package

Run in pycstruct root folder:

    python3 setup.py sdist bdist_wheel

## Upload package to PyPi.org

    python3 -m twine upload dist/*

Ender username and password.

