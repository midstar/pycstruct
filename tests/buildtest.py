###############################################################################
# Get version specified in appveyor.yml file
appveyor_version = "appveyor?"
with open("appveyor.yml", "r") as f:
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
with open("setup.py", "r") as f:
    lines = f.readlines()
    for line in lines:
        if line.strip().startswith("version="):
            setup_version = line.split('"')[1]

###############################################################################
# Compare
if appveyor_version == setup_version:
    print("SUCCESS! Versions match")
else:
    print(
        f"ERROR! Appveyor version {appveyor_version} don't "
        f"match setup.py version {setup_version}"
    )
    exit(1)
