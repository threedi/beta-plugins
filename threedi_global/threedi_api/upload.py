
# Doel van dit script:
# - Schematisatie maken als die nog niet bestaat
# - Nieuwe revisie aanmaken
# - Data uploaden
# - 3Di model en simulation template genereren


import hashlib
import time
from typing import Union, Dict, List
from pathlib import Path
from zipfile import ZipFile

from threedi_api_client.api import ThreediApi
from threedi_api_client.openapi import Schematisation
from threedi_api_client.files import upload_file
from threedi_api_client.openapi import ApiException

from threedi_api.constants import *
from login import get_login_details

CONFIG = {
    "THREEDI_API_HOST": THREEDI_API_HOST,
    "THREEDI_API_USERNAME": get_login_details(option='username'),
    "THREEDI_API_PASSWORD": get_login_details(option='password')
}
THREEDI_API = ThreediApi(config=CONFIG, version='v3-beta')


def md5(fname):
    """stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file"""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_or_create_schematisation(
        schematisation_name: str,
        organisation_uuid=ORGANISATION_UUID,
        tags: List = None
) -> Schematisation:
    print(ORGANISATION_UUID)
    tags = [] if not tags else tags
    resp = THREEDI_API.schematisations_list(
        name=schematisation_name, owner__unique_id=organisation_uuid
    )
    if resp.count == 1:
        print(f"Schematisation '{schematisation_name}' already exists, skipping creation.")
        return resp.results[0]
    elif resp.count > 1:
        raise ValueError(f"Found > 1 schematisations named'{schematisation_name}!")

    # if not found -> create
    print(f"Creating schematisation '{schematisation_name}'...")
    schematisation = THREEDI_API.schematisations_create(data={
        "owner": organisation_uuid,
        "name": schematisation_name,
        "tags": tags,
    })
    return schematisation


def upload_sqlite(schematisation, revision, sqlite_path: Union[str, Path]):
    sqlite_path = Path(sqlite_path)
    sqlite_zip_path = sqlite_path.with_suffix('.zip')
    print(f'sqlite_zip_path = {sqlite_zip_path}')
    ZipFile(sqlite_zip_path, mode='w').write(str(sqlite_path), arcname=str(sqlite_path.name))
    upload = THREEDI_API.schematisations_revisions_sqlite_upload(
        id=revision.id,
        schematisation_pk=schematisation.id,
        data={"filename": str(sqlite_zip_path.name)}
    )
    if upload.put_url is None:
        print(f"Sqlite '{sqlite_path.name}' already existed, skipping upload.")
    else:
        print(f"Uploading '{str(sqlite_path.name)}'...")
        upload_file(url=upload.put_url, file_path=sqlite_zip_path, timeout=UPLOAD_TIMEOUT)


def upload_raster(
    rev_id: int, schema_id: int, raster_type: str, raster_path: Union[str, Path]
):
    print(f"Creating '{raster_type}' raster...")
    raster_path = Path(raster_path)
    md5sum = md5(str(raster_path))
    data = {"name": raster_path.name, "type": raster_type, "md5sum": md5sum}
    raster_create = THREEDI_API.schematisations_revisions_rasters_create(rev_id, schema_id, data)
    if raster_create.file:
        if raster_create.file.state == "uploaded":
            print(f"Raster '{raster_path}' already exists, skipping upload.")
            return

    print(f"Uploading '{raster_path}'...")
    data={"filename": raster_path.name}
    upload = THREEDI_API.schematisations_revisions_rasters_upload(
        raster_create.id, rev_id, schema_id, data
    )

    upload_file(
        upload.put_url,
        raster_path,
        timeout=UPLOAD_TIMEOUT
    )


def commit_revision(
    rev_id: int,
    schema_id: int,
    commit_message
):
    # First wait for all files to have turned to 'uploaded'
    for wait_time in [0.5, 1.0, 2.0, 10.0, 30.0, 60.0, 120.0, 300.0]:
        revision = THREEDI_API.schematisations_revisions_read(rev_id, schema_id)
        states = [revision.sqlite.file.state]
        states.extend([raster.file.state for raster in revision.rasters])

        if all(state == "uploaded" for state in states):
            break
        elif any(state == "created" for state in states):
            print(
                f"Sleeping {wait_time} seconds to wait for the files to become 'uploaded'..."
            )
            time.sleep(wait_time)
            continue
        else:
            raise RuntimeError("One or more rasters have an unexpected state")
    else:
        raise RuntimeError("Some files are still in 'created' state")

    schematisation_revision = THREEDI_API.schematisations_revisions_commit(rev_id, schema_id, {"commit_message": commit_message})

    print(f"Committed revision {revision.number}.")
    return schematisation_revision


def create_threedimodel(
        schematisation,
        revision,
        max_retries_creation=60,
        wait_time_creation=5,
        max_retries_processing=60,
        wait_time_processing=60
):
    threedimodel = None
    for i in range(max_retries_creation):
        try:
            threedimodel = THREEDI_API.schematisations_revisions_create_threedimodel(revision.id, schematisation.id)
            print(f"Creating threedimodel with id {threedimodel.id}...")
            break
        except ApiException:
            time.sleep(wait_time_creation)
            continue
    if threedimodel:
        for i in range(max_retries_processing):
            threedimodel = THREEDI_API.threedimodels_read(threedimodel.id)
            if threedimodel.is_valid:
                print(f"Succesfully created threedimodel with id {threedimodel.id}")
                break
            else:
                time.sleep(wait_time_processing)
        if not threedimodel.is_valid:
            print(f"Failed to sucessfully process threedimodel with id {threedimodel.id}")
    else:
        print('Failed to create threedimodel')
    return threedimodel.id


def upload_and_process(
        schematisation_name: str,
        sqlite_path: Union[str, Path],
        raster_names: Dict[str, str],
        rasters_dir_name: str = "rasters",
        schematisation_create_tags: List[str] = None,
        commit_message: str = "auto-commit"

):
    # Schematisatie maken als die nog niet bestaat
    schematisation = get_or_create_schematisation(schematisation_name, tags=schematisation_create_tags)
    print(schematisation)
    # Nieuwe (lege) revisie aanmaken
    revision = THREEDI_API.schematisations_revisions_create(schematisation.id, data={"empty": True})

    # Data uploaden
    # # Spatialite
    sqlite_path = Path(sqlite_path)
    local_schematisation_dir = sqlite_path.parent
    upload_sqlite(schematisation=schematisation, revision=revision, sqlite_path=sqlite_path)

    # # Rasters
    for raster_type, raster_stem in raster_names.items():
        raster_path = local_schematisation_dir / rasters_dir_name / f"{raster_stem}.tif"
        upload_raster(rev_id=revision.id, schema_id=schematisation.id, raster_type=raster_type, raster_path=raster_path)

    # Commit revision
    commit_revision(rev_id=revision.id, schema_id=schematisation.id, commit_message=commit_message)

    # 3Di model en simulation template genereren
    threedimodel = create_threedimodel(schematisation, revision)
    return threedimodel, schematisation.id


# if __name__ == "__main__":
#     # raster_names = {'dem_file': 'dem', 'frict_coef_file': 'friction', 'infiltration_rate_file': 'infiltration'}
#     raster_names = {'dem_file': 'dem', 'initial_waterlevel_file': 'initial_waterlevel'}
#     # **** possible raster_names ****
#     # [ dem_file, equilibrium_infiltration_rate_file, frict_coef_file,
#     # initial_groundwater_level_file, initial_waterlevel_file, groundwater_hydro_connectivity_file,
#     # groundwater_impervious_layer_level_file, infiltration_decay_period_file, initial_infiltration_rate_file,
#     # leakage_file, phreatic_storage_capacity_file, hydraulic_conductivity_file, porosity_file, infiltration_rate_file,
#     # max_infiltration_capacity_file, interception_file ]
#     # ********************************

#     tags = ["W0273", "Provincie Utrecht", "Klimaatstresstest", "Infrastructuur"]
#     sqlite_path = "C:/Temp/utrecht/dummy_data/schematisation.sqlite"
#     schematisation_name = "Test voor 3Di goes global"

#     upload_and_process(
#         schematisation_name=schematisation_name,
#         sqlite_path=sqlite_path,
#         raster_names=raster_names,
#         schematisation_create_tags=tags
#     )


