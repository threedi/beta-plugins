import urllib3

UPLOAD_TIMEOUT = urllib3.Timeout(connect=60, read=600)

THREEDI_API_HOST = "https://api.3di.live"
ORGANISATION_UUID = "93bcc95f40d34b77919dda9374ee866"  # 3Di Global
