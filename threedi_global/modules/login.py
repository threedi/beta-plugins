import configparser
import os


def get_login_details(section: str = '3Di', option: str = None):
    """
    Read data from login_details.ini
    """
    path = os.path.abspath(os.path.dirname(__file__))
    login_details_ini_fn = os.path.join(path, 'login_details.ini')
    config = configparser.RawConfigParser()
    config.read(login_details_ini_fn)
    return config.get(section=section, option=option)
