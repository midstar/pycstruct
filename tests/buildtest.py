import urllib.request
import json

appveyor_name = "appveyor.yml"
setup_name = "setup.py"

###############################################################################
# Get version specified in appveyor.yml file
appveyor_version = "appveyor?"
with open(appveyor_name, "r") as f:
    lines = f.readlines()
    for line in lines:
        if line.startswith("version:"):
            v_long = line.split()[1]
            v_parts = v_long.split(".")
            appveyor_version = f"{v_parts[0]}.{v_parts[1]}.{v_parts[2]}"
            break

###############################################################################
# Get version specified in setup.py file
setup_version = "setup?"
with open(setup_name, "r") as f:
    lines = f.readlines()
    for line in lines:
        if line.strip().startswith("version="):
            setup_version = line.split('"')[1]

###############################################################################
# Compare
if appveyor_version == setup_version:
    print(f"PASS: Version {setup_version} match in {appveyor_name} and {setup_name}")
else:
    print(
        f"FAIL: {appveyor_name} version {appveyor_version} don't "
        f"match {setup_name} version {setup_version}"
    )
    exit(1)

###############################################################################
# Fetch versions from PyPI and check if it already exists
with urllib.request.urlopen("https://pypi.python.org/pypi/pycstruct/json") as url:
    package_data = json.loads(url.read().decode("utf-8"))
    if setup_version in package_data["releases"]:
        print(
            f"FAIL: Version {setup_version} is already "
            "available in PyPI. Please update version "
            f"in {appveyor_name} and {setup_name}"
        )
        exit(1)
    print(f"PASS: Version {setup_version} is not available in PyPi")
