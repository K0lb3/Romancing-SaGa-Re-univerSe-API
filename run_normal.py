from api_high import APIHigh
from settings import *

api = APIHigh(
    host=HOST,
    client_version=CLIENT_VERSION,
    device_secret=DEVICE_SECRET,
    device_model=DEVICE_MODEL,
)
if False:
    api.continue_session(
        token="SESSION_TOKEN",
        master_version=20210901021034088,
        assets_version=20210903114720436,
        next_expire=0,  # expiration time of the token
    )
else:
    api.start()
api.quest(901127054, 30, 999)
# kami - 972004080
# api.conquest(2004, 27)
