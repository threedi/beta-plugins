import urllib3

UPLOAD_TIMEOUT = urllib3.Timeout(connect=60, read=600)

THREEDI_API_HOST = "https://api.3di.live"
ORGANISATION_UUID = "61f5a464c35044c19bc7d4b42d7f58cb"  # Nelen & Schuurmans Consultancy
RADAR_ID = "d6c2347d-7bd1-4d9d-a1f6-b342c865516f"
SCHEMATISATIONS = [
    "Eygelshoven - Huidig-verbeterd",
    # "Eygelshoven - Verwacht",
    # "Eygelshoven - Maatregel A",
    # "Eygelshoven - Maatregel B",
    # "Eygelshoven - Maatregel C",
    # "Eygelshoven - Maatregel D",
    # "Eygelshoven - Maatregel E",
    # "Eygelshoven - Maatregel F"
]


BUIEN = {
    'T100': [  # s, m/s
        [0,          9.219 / (1000 * 24 * 60)],
        [24 * 60,    9.897 / (1000 * 24 * 60)],
        [48 * 60,   22.050 / (1000 * 24 * 60)],
        [72 * 60,   12.696 / (1000 * 24 * 60)],
        [96 * 60,    7.138 / (1000 * 24 * 60)],
        [120 * 60,   0]
    ]
}
