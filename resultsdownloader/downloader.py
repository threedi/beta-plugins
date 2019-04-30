# -*- coding: utf-8 -*-
"""The downloader part of the threedi_scenario_downloader supplies the user with often used functionality to look up and export 3Di results using the Lizard API"""
from datetime import datetime
from urllib.parse import urlparse
from time import sleep
import logging
import os
import requests

LIZARD_URL = "https://demo.lizard.net/api/v3/"
RESULT_LIMIT = 10
REQUESTS_HEADERS = {}

log = logging.getLogger()

SCENARIO_FILTERS = {
    "name": "name__icontains",
    "uuid": "uuid",
    "id": "id",
    "model_revision": "model_revision",
    "model_name": "model_name__icontains",
    "organisation": "organisation__icontains",
    "username": "username__icontains",
}


def set_logging_level(level):
    """set logging level to the supplied level"""

    log.level(level)


def get_headers():
    """return headers"""

    return REQUESTS_HEADERS


def set_headers(username, password):
    """set Lizard login credentials"""

    REQUESTS_HEADERS["username"] = username
    REQUESTS_HEADERS["password"] = password
    REQUESTS_HEADERS["Content-Type"] = "application/json"


def find_scenarios(limit=RESULT_LIMIT, **kwargs):
    """return json containing scenarios based on supplied filters"""
    url = "{}scenarios/".format(LIZARD_URL)

    payload = {"limit": limit}
    for key, value in kwargs.items():
        api_filter = SCENARIO_FILTERS[key]
        payload[api_filter] = value

    r = requests.get(url=url, headers=get_headers(), params=payload)
    r.raise_for_status()
    return r.json()["results"]


def find_scenarios_by_model_slug(model_uuid, limit=RESULT_LIMIT):
    """return json containing scenarios based on model slug"""

    url = "{}scenarios/".format(LIZARD_URL)
    payload = {"model_name__icontains": model_uuid, "limit": limit}
    r = requests.get(url=url, headers=get_headers(), params=payload)
    r.raise_for_status()
    return r.json()["results"]


def find_scenarios_by_name(name, limit=RESULT_LIMIT):
    """return json containing scenarios based on name"""
    url = "{}scenarios/".format(LIZARD_URL)
    payload = {"name__icontains": name, "limit": limit}
    r = requests.get(url=url, headers=get_headers(), params=payload)
    r.raise_for_status()
    return r.json()["results"]


def get_netcdf_link(scenario_uuid):
    """return url to raw 3Di results"""
    r = requests.get(
        url="{}scenarios/{}".format(LIZARD_URL, scenario_uuid), headers=get_headers()
    )
    r.raise_for_status()
    for result in r.json()["result_set"]:
        if result["result_type"]["code"] == "results-3di":
            url = result["attachment_url"]
            return url


def get_aggregation_netcdf_link(scenario_uuid):
    """return url to raw 3Di results"""
    r = requests.get(
        url="{}scenarios/{}".format(LIZARD_URL, scenario_uuid), headers=get_headers()
    )
    r.raise_for_status()
    for result in r.json()["result_set"]:
        if result["result_type"]["code"] == "aggregate-results-3di":
            url = result["attachment_url"]
            return url


def get_gridadmin_link(scenario_uuid):
    """return url to gridadministration"""
    r = requests.get(
        url="{}scenarios/{}".format(LIZARD_URL, scenario_uuid), headers=get_headers()
    )
    r.raise_for_status()
    for result in r.json()["result_set"]:
        if result["result_type"]["code"] == "grid-admin":
            url = result["attachment_url"]
            return url


def get_logging_link(scenario_uuid):
    """return url to zipped logging"""
    r = requests.get(
        url="{}scenarios/{}".format(LIZARD_URL, scenario_uuid), headers=get_headers()
    )
    r.raise_for_status()
    for result in r.json()["result_set"]:
        if result["result_type"]["code"] == "logfiles":
            url = result["attachment_url"]
            return url


def get_raster(scenario_uuid, raster_code):
    """return json of raster based on scenario uuid and raster type"""

    r = requests.get(
        url="{}scenarios/{}".format(LIZARD_URL, scenario_uuid), headers=get_headers()
    )
    r.raise_for_status()
    for result in r.json()["result_set"]:
        if result["result_type"]["code"] == raster_code:
            return result["raster"]


def create_raster_task(raster, target_srs, resolution, bounds=None, time=None):
    """create Lizard raster task"""

    if bounds == None:
        bounds = raster["spatial_bounds"]

    e = bounds["east"]
    w = bounds["west"]
    n = bounds["north"]
    s = bounds["south"]

    source_srs = "EPSG:4326"

    bbox = "POLYGON(({} {},{} {},{} {},{} {},{} {}))".format(
        w, n, e, n, e, s, w, s, w, n
    )

    url = "{}rasters/{}/data/".format(LIZARD_URL, raster["uuid"])
    if time is None:
        # non temporal raster
        payload = {
            "cellsize": resolution,
            "geom": bbox,
            "srs": source_srs,
            "target_srs": target_srs,
            "format": "geotiff",
            "async": "true",
        }
    else:
        # temporal rasters
        payload = {
            "cellsize": resolution,
            "geom": bbox,
            "srs": source_srs,
            "target_srs": target_srs,
            "time": time,
            "format": "geotiff",
            "async": "true",
        }
    r = requests.get(url=url, headers=get_headers(), params=payload)
    r.raise_for_status()
    return r.json()


# From here untested methods are added
def get_task_status(task_uuid):
    """return status of task"""
    url = "{}tasks/{}/".format(LIZARD_URL, task_uuid)
    r = requests.get(url=url, headers=get_headers())
    r.raise_for_status()
    return r.json()["task_status"]


def get_task_download_url(task_uuid):
    """return url of successful task"""
    if get_task_status(task_uuid) == "SUCCESS":
        url = "{}tasks/{}/".format(LIZARD_URL, task_uuid)
        r = requests.get(url=url, headers=get_headers())
        r.raise_for_status()
        return r.json()["result_url"]
    # What to do if task is not a success?


def download_file(url, path):
    """download url to specified path"""
    logging.debug("Start downloading file: {}".format(url))
    r = requests.get(url, auth=(get_headers()["username"], get_headers()["password"]))
    r.raise_for_status()
    with open(path, "wb") as file:
        for chunk in r.iter_content(100000):
            file.write(chunk)


def download_task(task_uuid, pathname=None):
    """download result of successful task"""
    if get_task_status(task_uuid) == "SUCCESS":
        download_url = get_task_download_url(task_uuid)
        if pathname is None:

            logging.debug("download_url: {}".format(download_url))
            logging.debug("urlparse(download_url): {}".format(urlparse(download_url)))
            pathname = os.path.basename(urlparse(download_url).path)
            logging.debug(pathname)
        download_file(download_url, pathname)


def download_raster(
    scenario, raster_code, target_srs, resolution, bounds=None, time=None, pathname=None
):
    """
    download raster
    """
    if type(scenario) is str:
        # assume uuid
        raster = get_raster(scenario, raster_code)
    elif type(scenario) is dict:
        # assume json object
        raster = get_raster_from_json(scenario, raster_code)
    else:
        log.debug("Invalid scenario: supply a json object or uuid string")

    task = create_raster_task(raster, target_srs, resolution, bounds, time)
    task_uuid = task["task_id"]

    log.debug("Start waiting for task {} to finish".format(task_uuid))
    while get_task_status(task_uuid) == "PENDING":
        sleep(5)
        log.debug("Still waiting for task {}".format(task_uuid))

    if get_task_status(task_uuid) == "SUCCESS":
        # task is a succes, return download url
        log.debug(
            "Task succeeded, start downloading url: {}".format(
                get_task_download_url(task_uuid)
            )
        )
        print(
            "Task succeeded, start downloading url: {}".format(
                get_task_download_url(task_uuid)
            )
        )
        download_task(task_uuid, pathname)
    else:
        log.debug("Task failed")


def download_maximum_waterdepth_raster(
    scenario_uuid, target_srs, resolution, bounds=None, pathname=None
):
    """download Maximum waterdepth raster"""
    download_raster(
        scenario_uuid, "depth-max-dtri", target_srs, resolution, bounds, None, pathname
    )


def download_maximum_waterlevel_raster(
    scenario_uuid, target_srs, resolution, bounds=None, pathname=None
):
    """download Maximum waterdepth raster"""
    download_raster(
        scenario_uuid, "s1-max-dtri", target_srs, resolution, bounds, None, pathname
    )


def download_total_damage_raster(
    scenario_uuid, target_srs, resolution, bounds=None, pathname=None
):
    """download Total Damage raster"""
    download_raster(
        scenario_uuid, "total-damage", target_srs, resolution, bounds, None, pathname
    )


def download_waterdepth_raster(
    scenario_uuid, target_srs, resolution, time, bounds=None, pathname=None
):
    """download snapshot of Waterdepth raster"""
    download_raster(
        scenario_uuid,
        "depth-dtri",
        target_srs,
        resolution,
        bounds=bounds,
        time=time,
        pathname=pathname,
    )


def download_waterlevel_raster(
    scenario_uuid, target_srs, resolution, time, bounds=None, pathname=None
):
    """download snapshot of Waterdepth raster"""
    download_raster(
        scenario_uuid,
        "s1-dtri",
        target_srs,
        resolution,
        bounds=bounds,
        time=time,
        pathname=pathname,
    )


def download_precipitation_raster(
    scenario_uuid, target_srs, resolution, time, bounds=None, pathname=None
):
    """download snapshot of Waterdepth raster"""
    download_raster(
        scenario_uuid,
        "rain-quad",
        target_srs,
        resolution,
        bounds=bounds,
        time=time,
        pathname=pathname,
    )


def download_raw_results(scenario_uuid, pathname=None):
    url = get_netcdf_link(scenario_uuid)
    logging.debug("Start downloading raw results: {}".format(url))
    download_file(url, pathname)


def download_grid_administration(scenario_uuid, pathname=None):
    url = get_gridadmin_link(scenario_uuid)
    logging.debug("Start downloading grid administration: {}".format(url))
    download_file(url, pathname)


def clear_inbox():
    """delete all messages from Lizard inbox"""
    url = "{}inbox/".format(LIZARD_URL)
    r = requests.get(
        url=url, headers=get_headers(), params={"limit": RESULT_LIMIT}, timeout=10
    )
    r.raise_for_status()
    messages = r.json()["results"]
    for msg in messages:
        msg_id = msg["id"]
        read_url = "{}inbox/{}/read/".format(LIZARD_URL, msg_id)
        r = requests.post(url=read_url, headers=get_headers(), timeout=10)
    return True


def get_attachment_links(scenario_json):
    """get links to static scenario results"""
    attachment_links = {}
    for result in scenario_json["result_set"]:
        if result["attachment_url"]:
            result_name = result["result_type"]["name"]
            attachment_links[result_name] = result["attachment_url"]
    if attachment_links:
        return attachment_links
    else:
        return None


def rasters_in_scenario(scenario_json):
    """return two lists of static and temporal rasters including 3di result name and code"""
    temporal_rasters = []
    static_rasters = []
    for result in scenario_json["result_set"]:
        result_type = result["result_type"]
        if result_type["has_raster"]:
            raster = result["raster"]
            name_3di = result_type["name"]
            code_3di = result_type["code"]
            raster["name_3di"] = name_3di
            raster["code_3di"] = code_3di
            if raster["temporal"]:
                temporal_rasters.append(raster)
            else:
                static_rasters.append(raster)
    return static_rasters, temporal_rasters


def get_raster_link(raster, target_srs, resolution, bounds=None, time=None):
    """get url to download raster"""
    task = create_raster_task(raster, target_srs, resolution, bounds, time)
    task_uuid = task["task_id"]

    log.debug("Start waiting for task {} to finish".format(task_uuid))
    task_status = get_task_status(task_uuid)
    while task_status == "PENDING":
        log.debug("Still waiting for task {}".format(task_uuid))
        sleep(5)
        task_status = get_task_status(task_uuid)

    if get_task_status(task_uuid) == "SUCCESS":
        # task is a succes, return download url
        download_url = get_task_download_url(task_uuid)
        return download_url
    else:
        log.debug("Task failed")
        return None


def get_static_rasters_links(
    static_rasters, target_srs, resolution, bounds=None, time=None
):
    """return a dict of urls to geotiff files of static rasters in scenario
    the dict items are formatted as result_name: link.tif"""
    static_raster_urls = {}
    for static_raster in static_rasters:
        name = static_raster["name_3di"]
        static_raster_url = get_raster_link(
            static_raster, target_srs, resolution, bounds, time
        )
        static_raster_urls[name] = static_raster_url
    return static_raster_urls


def get_temporal_raster_links(
    temporal_raster, target_srs, resolution, bounds=None, interval_hours=None
):
    """return a dict of urls to geotiff files of a temporal raster
    the dict items are formatted as name_3di_datetime: link.tif"""
    temporal_raster_urls = {}
    name = temporal_raster["name_3di"]
    timesteps = get_raster_timesteps(temporal_raster, interval_hours)
    for timestep in timesteps:
        download_url = get_raster_link(
            temporal_raster, target_srs, resolution, bounds, timestep
        )
        url_timestep = os.path.splitext(download_url)[0].split("_")[-1]
        # Lizard returns the nearest timestep based on the time=timestep request
        timestep_url_format = "{}Z".format(timestep.split(".")[0].replace("-", ""))
        if timestep_url_format == url_timestep:
            # when requested and retrieved timesteps are equal, use the timestep
            name_timestep = "_".join([name, timestep])
        else:
            # if not equal, indicate the datetime discrepancy in file name
            name_timestep = "{}_get_{}_got_{}".format(
                name, timestep_url_format, url_timestep
            )
        temporal_raster_urls[name_timestep] = download_url
    return temporal_raster_urls


def get_temporal_rasters_links(
    temporal_rasters, target_srs, resolution, bounds=None, interval_hours=None
):
    """get links to all temporal rasters"""
    temporal_rasters_urls = {}
    for temporal_raster in temporal_rasters:
        temporal_raster_urls = get_temporal_raster_links(
            temporal_raster, target_srs, resolution, bounds, interval_hours
        )
        for name_timestep, download_url in temporal_raster_urls.items():
            temporal_rasters_urls.setdefault(name_timestep, download_url)
    return temporal_rasters_urls


def get_raster_timesteps(raster, interval_hours=None):
    """returns a list of 'YYYY-MM-DDTHH:MM:SS' formatted timesteps in temporal range of raster object
    Starts at first timestep and ends at last timestep.
    The intermediate timesteps are determined by the interval.
    When no interval is provided, the first, middle and last timesteps are returned
    """
    raster_uuid = raster["uuid"]
    if not raster["temporal"]:
        return [None]
    if not interval_hours:
        # assume interval of store (rounded minutes) and return first, middle and last raster
        url = "{}rasters/{}/timesteps/".format(LIZARD_URL, raster_uuid)
        timesteps_json = request_json_from_url(url)
        timesteps_ms = timesteps_json["steps"]
        # only return first, middle and last raster
        timesteps_ms = [
            timesteps_ms[0],
            timesteps_ms[round(len(timesteps_ms) / 2)],
            timesteps_ms[-1],
        ]
    else:
        # use interval from argument
        first_timestamp = int(raster["first_value_timestamp"])
        timesteps_ms = []
        last_timestamp = int(raster["last_value_timestamp"])
        interval_ms = interval_hours * 3600000
        while last_timestamp > first_timestamp:
            timesteps_ms.append(first_timestamp)
            first_timestamp += interval_ms
        if not last_timestamp in timesteps_ms:
            timesteps_ms.append(last_timestamp)
    timesteps = [datetime.fromtimestamp(i / 1000.0).isoformat() for i in timesteps_ms]
    return timesteps


def get_raster_from_json(scenario, raster_code):
    """return raster json object from scenario"""
    for result in scenario["result_set"]:
        if result["result_type"]["code"] == raster_code:
            return result["raster"]


def request_json_from_url(url, params=None):
    """retrieve json object from url"""
    r = requests.get(url=url, headers=get_headers(), params=params)
    r.raise_for_status()
    if r.status_code == requests.codes.ok:
        return r.json()
