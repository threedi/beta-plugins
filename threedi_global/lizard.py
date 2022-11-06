import math
from pathlib import Path
import time
from typing import List, Union
import requests

from osgeo import gdal

def get_headers(api_key: str):
    return {
        "username": "__key__",
        "password": api_key,
        "Content-Type": "application/json",
    }


def download_raster(
        api_key: str,
        raster_uuid: str,
        bounding_box: List[float],
        epsg_code: int,
        pixel_size: float,
        output_path: Union[Path, str],
        max_attempts=720,
        wait_time=5
):
    """

    :param api_key:
    :param raster_uuid:
    :param bounding_box: [minx, miny, maxx, maxy]
    :param epsg_code:
    :param pixel_size:
    :param output_path:
    :return:
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = get_headers(api_key)
    raster_url = "https://nens.lizard.net/api/v4/rasters/"
    get_url = f"{raster_url}{raster_uuid}/data/"
    maxx = max([bounding_box[0], bounding_box[2]])
    minx = min([bounding_box[0], bounding_box[2]])
    maxy = max([bounding_box[1], bounding_box[3]])
    miny = min([bounding_box[1], bounding_box[3]])
    width = int(math.ceil((maxx - minx) / pixel_size))
    height = int(math.ceil((maxy - miny) / pixel_size))
    use_async = width * height > 4194304
    bbox = ",".join([str(i) for i in bounding_box])
    params = {
        "bbox": bbox,
        "format": 'geotiff',
        "projection": f"EPSG:{epsg_code}",
        "width": width,
        "height": height,
        "async": use_async
    }
    r = requests.get(url=get_url, headers=headers, params=params)
    if r.status_code != 200:
        raise Exception(f"Downloading raster failed. API response: {r.text}")
    if use_async:
        print("Waiting while Lizard is preparing the requested raster file...")
        task_url = r.json()["url"]
        task_status = ""
        attempts = 0
        while task_status != "SUCCESS" and attempts < max_attempts:
            task = requests.get(task_url, headers=headers).json()
            task_status = task["status"]
            if task_status == "SUCCESS":
                task_result = task["result"]
                break
            elif attempts == max_attempts:
                raise Exception('Connection timed out')
            attempts += 1
            time.sleep(wait_time)
        r = requests.get(url=task_result, headers=headers)

    with output_path.open("wb") as file:
        if r.headers.get('content-length'):
            for chunk in r.iter_content(chunk_size=4096):
                file.write(chunk)
        else:  # no content length header
            file.write(r.content)

    # Set the pixel size exactly to the requested pixel size, because with the calculation of width and height this is
    # really impossible
    dataset = gdal.Open(str(output_path), gdal.GA_Update)
    gt = list(dataset.GetGeoTransform())
    gt[1] = pixel_size
    gt[5] = -pixel_size
    dataset.SetGeoTransform(tuple(gt))

