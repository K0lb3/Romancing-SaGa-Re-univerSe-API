from api import API
from time import sleep
from database import get_master, get_round_duration
from settings import STAMINA_POT, STAMINA_POT_REFRESH_COUNT


class APIHigh(API):
    real = True  # simulate a real instance by trying to have the same intervals
    logging = False
    stamina: int
    stamina_potions: list

    def __init__(
        self,
        host: str,
        client_version: str,
        device_secret: str,
        device_model: str,
        nickname: str = "Polka",
    ) -> None:
        super().__init__(
            host,
            client_version,
            device_secret,
            device_model=device_model,
            nickname=nickname,
        )
        self.stamina = 0
        self.stamina_potions = []

    def start(self):
        self.auth_signin()
        self.title_info()
        self.status()
        self.player_create()
        self.player_summary()
        self.quest_resume()
        # self.player_login()
        # self.home_guest()
        # self.home_info()
        # self.player_info()
        # quest
        # dojo
        # party

    def continue_session(
        self, token: str, next_expire: int, master_version: str, assets_version: str
    ):
        self.session.headers.update(
            {
                # "X-Mikoto-Request-Id":
                "X-Mikoto-Master-Version": str(master_version),
                "X-Mikoto-Assets-Version": str(assets_version),
                "X-Mikoto-Token": token,
            }
        )
        self.next_expire = next_expire

    def log(self, name, data):
        pass

    def _setup_stamina_potions(self, items):
        potions = get_master("StaminaPotion")
        self.stamina_potions = []
        for item in items:
            potion = potions.get(item["id"], None)
            if not potion:
                continue
            if potion["expired_at"] == 0:
                potion["expired_at"] = 9999999999
            self.stamina_potions.append([potion, item["quantity"]])
        self.stamina_potions.sort(key=lambda pot, count: pot["expired_at"])

    def stamina_refill(self, refill_cap: int = 200):
        pot, count = self.stamina_potions[0]
        use = min((refill_cap - self.stamina) / pot["value"], count)
        self.shop_stamina_item(pot["id"], use)
        if count - use == 0:
            self.stamina_potions.pop(0)
        else:
            self.stamina_potions[0][1] -= use

    def conquest_single(self, area_id: int = None, party_number: int = 1):
        # TODO - other conquests without multi
        field_map_quests = get_master("FieldMapQuest")
        while True:
            print("fetching conquest info")
            res = self.quest_field_map_list()
            for area in res["areas"]:
                if area["area_id"] == area_id or not area_id:
                    break
            else:
                print("Couldn't find the requested area")
                return 1

            print("fetching conquest nodes")
            field_map_group_id = area["solo"]["field_map_group_id"]
            field_map_group = self.quest_field_map_info(field_map_group_id)

            print("Looking for uncleared nodes")
            quest_id = None
            for node in field_map_group["field_map_data"]["nodes"]:
                if node["is_accessible"] and node["domination_rate"] not in [
                    None,
                    100,
                ]:
                    for quest_id, quest in field_map_quests.items():
                        if quest["field_map_node_id"] == node["field_map_node_id"]:
                            print("Found", quest_id)
                            break
                    if quest_id:
                        break
            if quest_id == None:
                print("No bonus node found")
                return

            while True:
                quest_result = self.quest(quest_id, party_number)
                if quest_result["field_map_result"]:
                    print(quest_result["field_map_result"]["domination_rate"])
                    if quest_result["field_map_result"]["domination_rate"] == 100:
                        break
                try:
                    if quest_result["changed_resources"]["player"]["stamina"] < 10:
                        sleep(0.5)
                        # api.maintenance_status()
                        sleep(1)
                        self.shop_stamina_item(STAMINA_POT, STAMINA_POT_REFRESH_COUNT)
                        print("Stam Refreshed")
                except:
                    print()

    def conquest_multi(self, area_id: int = None, party_number: int = 1):
        # TODO - other conquests without multi
        field_map_quests = get_master("FieldMapQuest")
        faillist = []
        while True:
            print("fetching conquest info")
            res = self.quest_field_map_list()
            for area in res["areas"]:
                if area["area_id"] == area_id or not area_id:
                    break
            else:
                print("Couldn't find the requested area")
                return 1

            print("fetching conquest nodes")
            field_map_group_id = area["multi"]["field_map_group_id"]
            field_map_group = self.quest_field_map_info(field_map_group_id)

            print("Looking for current bonus nodes")
            quest_id = None
            for node in field_map_group["field_map_data"]["nodes"]:
                if node["is_accessible"] and node["domination_rate"] not in [
                    None,
                    0,
                    100,
                ] and node["field_map_node_id"] not in faillist:
                    for quest_id, quest in field_map_quests.items():
                        if quest["field_map_node_id"] == node["field_map_node_id"]:
                            print("Found", quest_id)
                            break
                    if quest_id:
                        break
            if quest_id == None:
                print("No bonus node found")
                return

            fails = 0
            while True:
                quest_result = self.quest(quest_id, party_number)
                
                try:
                    if quest_result["changed_resources"]["player"]["stamina"] < 10:
                        sleep(0.5)
                        # api.maintenance_status()
                        sleep(1)
                        self.shop_stamina_item(STAMINA_POT, STAMINA_POT_REFRESH_COUNT)
                        print("Stam Refreshed")
                except:
                    print()
                
                if quest_result["field_map_result"]:
                    print(quest_result["field_map_result"]["domination_rate"])
                    if quest_result["field_map_result"]["domination_rate"] == 100:
                        break
                if quest_result["battle"]["latest_turn_result"] in ["loss","lost"]:
                    fails +=1
                    if fails == 5:
                        faillist.append("field_map_node_id")
                        break


    def quest(self, quest_id: int = 0, party_number: int = 1, repeat: int = 0):
        print("Create battle", repeat)
        self.quest_create(quest_id, party_number)

        if self.real:
            sleep(1)
        # check if create worked,
        # if not, refill
        r = 1
        t = 1
        while True:
            print("Attack", end="\t")
            res_atk = self.quest_attack(commands=[], auto_battle_type=3)
            self.quest_status()
            t += 1
            # sleep some time according to res_atk
            if res_atk.get("code", 0) == 4022:
                input()
                break

            result = res_atk["battle"]["latest_turn_result"]
            print(result, end="\t")
            if self.real:
                commands = [
                    res["skill_id"] for res in res_atk["turn_result"]["action_results"]
                ]
                st = get_round_duration(commands) + len(commands)
                print(st)
                sleep(st)
            else:
                print()

            if result == "won":
                self.quest_status()
                r += 1
            elif result in ["completed", "retreated"]:
                break
            elif result == "continue":
                pass
            elif result in ["loss", "lost"]:
                break
            else:
                raise NotImplementedError(result)

        if repeat == 0:
            return res_atk
        else:
            try:
                if res_atk["changed_resources"]["player"]["stamina"] < 50:
                    sleep(0.5)
                    # api.maintenance_status()
                    sleep(1)
                    self.shop_stamina_item(STAMINA_POT, STAMINA_POT_REFRESH_COUNT)
                    print("Stam Refreshed")
            except:
                print()
            return self.quest(quest_id, party_number, repeat - 1)
