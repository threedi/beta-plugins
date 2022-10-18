from zipfile import ZipFile
import os

ROOT_DIR_FILES = [
    '__init__.py',
    'dem_sampling_algorithms.py',
    'leak_detector_algorithms.py',
    'leak_detector.py',
    'metadata.txt',
    'rasterize_channel.py',
    'rasterize_channel_algorithms.py',
    'rasterize_channel_utils.py',
    'threedibetaprocessing.py',
    'threedibetaprocessing_provider.py',
]

DIRECTORIES = [
    'linemerge',
    'raster_tools',
    'style',
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
    os.remove('threedi_beta_processing.zip')
except FileNotFoundError:
    pass
zip = ZipFile('threedi_beta_processing.zip', 'w')

# Files in root
for file in ROOT_DIR_FILES:
    zip.write(file, os.path.join('threedi_beta_processing', os.path.basename(file)))

# Folders in root
for directory in DIRECTORIES:
    zipdir(directory, zip, 'threedi_beta_processing')

# close the Zip File
zip.close()