from zipfile import ZipFile
import os

ROOT_DIR_FILES = [
    '__init__.py',
    'icon.png',
    'import_hydx.py',
    'import_hydx_dialog.py',
    'import_hydx_dialog_base.ui',
    'metadata.txt',
    'resources.py',
    'resources.qrc',
]

DIRECTORIES = [
    'hydxlib',
    'threedi_result_aggregation'
]


def zipdir(path, ziph, path_in_zip):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            zip_file_path = os.path.join(path_in_zip, file_path )
            ziph.write(file_path, zip_file_path)


# create a ZipFile object
try:
    os.remove('import_hydx.zip')
except FileNotFoundError:
    pass
zip = ZipFile('import_hydx.zip', 'w')

# Files in root
for file in ROOT_DIR_FILES:
    zip.write(file, os.path.join('import_hydx', os.path.basename(file)))

# Folders in root
for directory in DIRECTORIES:
    zipdir(directory, zip, 'import_hydx')

# close the Zip File
zip.close()