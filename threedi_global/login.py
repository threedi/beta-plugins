import configparser
from pathlib import Path


def get_login_details(section: str = '3Di', option: str = None):
    """
    Read data from login_details.ini
    """
    login_details_ini_fn = str(Path(__file__).parent / "login_details.ini")
    config = configparser.RawConfigParser()
    config.read(login_details_ini_fn)
    return config.get(section=section, option=option)
