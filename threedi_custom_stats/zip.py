from zipfile import ZipFile
import os

ROOT_DIR_FILES = [
    "__init__.py",
    "cross_sectional_discharge.py",
    "icon.png",
    "metadata.txt",
    "ogr2qgis.py",
    "presets.py",
    "resources.py",
    "resources.qrc",
    "style.py",
    "threedi_custom_stats.py",
    "threedi_custom_stats_dialog.py",
    "threedi_custom_stats_dialog_base.ui",
]

DIRECTORIES = ["processing", "style", "threedi_result_aggregation"]


def zipdir(path, ziph, path_in_zip):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            zip_file_path = os.path.join(path_in_zip, file_path)
            ziph.write(file_path, zip_file_path)


# create a ZipFile object
try:
    os.remove("threedi_custom_statistics.zip")
except FileNotFoundError:
    pass
zip = ZipFile("threedi_custom_statistics.zip", "w")

# Files in root
for file in ROOT_DIR_FILES:
    zip.write(file, os.path.join("threedi_custom_stats", os.path.basename(file)))

# Folders in root
for directory in DIRECTORIES:
    zipdir(directory, zip, "threedi_custom_stats")

# close the Zip File
zip.close()
