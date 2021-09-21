import re
import json

# format playerprefs into a readable json

with open("PlayerPrefs.txt", "rt", encoding="utf8") as f:
    text = f.read()


def parse_player_prefs(text):
    def parse_value(val, typ):
        if "Int" in typ:
            return int(val)
        elif "Boolean" in typ:
            return True if val == "True" else False
        elif len(val) and val[0] == "{":
            return json.loads(val.replace("\\:", ":"))
        else:
            return val

    return {
        # style_limit_designated : True : System.Boolean ;
        match[1]: parse_value(match[2], match[3])
        for match in re.finditer(r"([\w_-]+?) : (.*?) : (.+?) ;", text)
    }


prefs = parse_player_prefs(text)

headers = {
    # required for every request
    "X-Mikoto-Device-Secret": prefs["device_id"],
    # required for all logged in requests - can be generated via auth/signin
    "X-Mikoto-Token": prefs["token"],
    # time when the token expires, utc, check against server
    "token_expiration": prefs["token_expiration"],
}
# X-Mikoto-Device-Secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# Host: production-api.rs-eu.aktsk.com
# Accept-Encoding: gzip, identity
# Connection: Keep-Alive, TE
# TE: identity
# User-Agent: BestHTTP

with open("PlayerPrefs.json", "wt", encoding="utf8") as f:
    json.dump(prefs, f, indent=4, ensure_ascii=False)
