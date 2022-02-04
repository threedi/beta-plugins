import os
import sys
import shutil

PLUGIN_DIR_NAME = None

try:
    PLUGIN_DIR_NAME = sys.argv[1]
except IndexError:
    print("Please supply a plugin (module) name")

if PLUGIN_DIR_NAME:
    this_dir = os.path.dirname(os.path.realpath(__file__))
    home_dir = os.path.expanduser("~")
    dest_dir_plug = os.path.join(
        home_dir, "AppData", "Roaming", "QGIS", "QGIS3", "profiles", "default", "python", "plugins", PLUGIN_DIR_NAME
    )
    print(dest_dir_plug)
    src_dir_plug = os.path.join(this_dir, PLUGIN_DIR_NAME)
    try:
        shutil.rmtree(dest_dir_plug)
    except OSError:
        pass  # directory not present at all
    shutil.copytree(src_dir_plug, dest_dir_plug)
