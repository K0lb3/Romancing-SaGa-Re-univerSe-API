# Europe:  rs-eu
# America: rs-us
# Asia:    rs-as
# Japan:   rs.aktsk.jp
HOST = "production-api.rs-eu.aktsk.com"

# check apk_monobehaviours/GameSettings-GameSettings.json, different for each APK version
CLIENT_VERSION = "1.17.10-71dabc6b444dc6be8c5ac1eb3049d5e6"

# device login data, both parts are likely required
# the secret can be found in PlayerPrefs.txt in /data/data/com.square_enix.android_googleplay.RSRSWW/...
DEVICE_SECRET = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" #uuid4
# to build up the model string,  download BuildPropEditor and check the value
# the model_number can be found in the android settings/about tablet/phone
# DEVICE_MODEL = f"{ro.product.manufacturer} {model_number} Android OS {ro.build_version.release} / API-{ro.build_version.sdk} ({ro.build.id}/{ro.nuild.version.incremental})
DEVICE_MODEL = "? ? Android OS ? / API-? (?/?)"

# path to your local version of the extracted data, required for duration and database
DUMP_PATH = r"D:\Datamine\Romancing Sage; re\github\assets\gl\extracted"

# stamina pot used for refreshes, check StaminaPotion.json
STAMINA_POT = 1000840015
STAMINA_POT_REFRESH_COUNT = 21