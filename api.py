import requests
import uuid
import time


class API:
    host: str
    device_secret: str
    device_uuid: str
    device_model: str
    session: requests.Session
    next_expire = int
    nickname: str

    def __init__(
        self,
        host: str,
        client_version: str,
        device_secret: str,
        # device_uuid: str,
        device_model: str,
        nickname: str = "Polka",
    ) -> None:
        self.host = host
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Mikoto-Client-Version": client_version,
                "X-Mikoto-Platform": "android",
                "X-Mikoto-Device-Secret": device_secret,
                "Host": self.host,
                "Accept-Encoding": "gzip, identity",
                "Connection": "Keep-Alive, TE",
                "TE": "identity",
                "User-Agent": "BestHTTP",
            }
        )
        # self.device_uuid = device_uuid
        self.device_model = device_model
        self.nickname = nickname
        self.next_expire = 0

    def auth_signin(self):
        self.next_expire = 0
        self.session.headers["X-Mikoto-Device-Model"] = self.device_model
        res = self.request("/auth/signin")
        self.session.headers["X-Mikoto-Token"] = res["token"]
        self.next_expire = int(res["next_expire"])
        del self.session.headers["X-Mikoto-Device-Model"]
        print(res)
        return res

    def auth_google_signin(self, id_token: str):
        # TODO - how to fetch id_token from google?
        self.session.headers["X-Mikoto-Device-Model"] = self.device_model
        res = self.request("/auth/google_play/signin", {"id_token": id_token})
        self.session.headers["X-Mikoto-Token"] = res["token"]
        self.next_expire = int(res["next_expire"])
        del self.session.headers["X-Mikoto-Device-Model"]
        print(res)
        return res

    def title_info(self):
        return self.request("/title/info")["event_title"]

    def status(self):
        res = self.request("/status")
        self.session.headers.update(
            {
                "X-Mikoto-Master-Version": res["master_version"],
                "X-Mikoto-Assets-Version": res["assets_version"],
            }
        )
        return res

    def player_create(self):
        # already_created	Boolean	true
        # personal_profile	Object
        # birth_month	Null	null
        # birth_year	Null	null
        # is_16_years_old_or_over	Boolean	true
        # lives_in_eea	Boolean	true
        # player_id	Long
        return self.request(
            "/player/create",
            {
                "language": 1,
                "lives_in_eea": True,
                "is_16_years_old_or_over": True,
                "country": "US",
                "nick_name": self.nickname,
                "device_type": 2,
            },
        )

    def player_summary(self):
        return self.request("/player/summary")

    def quest_resume(self):
        return self.request("/quest/resume")

    def player_login(self):
        return self.request(
            "/player/login",
            {
                "device_uuid": self.device_uuid,
                "is_tracking_enabled": False,
                "advertising_id": "00000000-0000-0000-0000-000000000000",
            },
        )

    def quest_create(self, quest_id: int, party_number: int, battle_id: int = None):
        args = {"quest_id": quest_id, "party_number": party_number, "auto_rematch": False}
        if battle_id:
            args["battle_id"] = battle_id
        return self.request(
            "/quest/create", args
        )

    def quest_attack(self, commands: list = [], auto_battle_type: int = 0):
        return self.request(
            "/quest/attack",
            {"commands": commands, "auto_battle_type": auto_battle_type, "active_auto_rematch": False},
        )

    def quest_status(self):
        return self.request("/quest/status")

    def quest_retry(self):
        return self.request("/quest/retry")

    def quest_retire(self):
        return self.request("/quest/retire")

    def quest_field_map_list(self):
        return self.request("/quest/field_map/list")

    def quest_field_map_info(self, field_map_group_id: int):
        return self.request(
            "/quest/field_map/info", {"field_map_group_id": field_map_group_id}
        )

    def maintenance_status(self):
        return self.request("/maintenance/status")

    def shop_stamina_item(self, item_id, quantity):
        return self.request(
            "/shop/stamina/item", {"item_id": item_id, "quantity": quantity}
        )
    
    def gacha_list(self):
        return self.request(
            "/gacha/list"
        )
    
    def gacha_deck_list(self, gacha_id: int):
        return self.request(
            "/gacha/deck/list", {"gacha_id":gacha_id}
        )

    def request(self, path, data: dict = {}):
        # check if token is still valid
        if self.next_expire:
            if self.next_expire < time.time() + 10:
                # token outdated, request a new one
                self.auth_signin()

        self.session.headers["X-Mikoto-Request-Id"] = str(uuid.uuid4())
        if data:
            res = self.session.post(
                f"https://{self.host}/{path.lstrip('/')}", json=data
            )
        else:
            res = self.session.post(f"https://{self.host}/{path.lstrip('/')}")
        return res.json()
