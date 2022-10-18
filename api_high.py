from select import select
from api import API
from time import sleep
from database import get_master, get_round_duration


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
        quest = self.quest_resume()
        if quest.get('resumable_quest_id') is not None:
            self.quest_retire()
        # self.player_login()
        # self.home_guest()
        # self.home_info()
        # self.player_info()
        # quest
        # dojo
        # party

    def player_summary(self):
        res = super().player_summary()
        data = res
        # pots
        stam_pots = get_master("StaminaPotion")
        for item in data["items"]:
            if item["item_type"] == 12 and item["quantity"]:
                self.stamina_potions.append([stam_pots[item["item_id"]], item["quantity"]])
        # player
        self.stamina = data["player"]["stamina"]
        self.stamina_max = data["player"]["max_stamina"]+600
        return data

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

    def stamina_refill(self, min_stam:int=0):
        pots = sorted(self.stamina_potions, key=lambda x: x[0]["expired_at"])
        sel = 3 if len(pots) > 3 else 0
        pot, count = self.stamina_potions[sel]
        use = min(count, (self.stamina_max - self.stamina) //pot["value"])
        self.shop_stamina_item(pot["id"], use)
        print(f"use {use} of {pot['name']}({pot['id']})")
        if count - use == 0:
            self.stamina_potions.pop(sel)
        else:
            self.stamina_potions[sel][1] -= use

    def conquest_cleanup(self, area_id: int = None, party_number: int = 1, mode = "multi|solo"):
        field_map_quests = get_master("FieldMapQuest")
        field_map_quests_by_node_id = {
            quest["field_map_node_id"]: quest_id
            for quest_id, quest in field_map_quests.items()
        }
        while True:
            print("fetching conquest info")
            res = self.quest_field_map_list()
            for area in res["areas"]:
                if area["area_id"] == area_id or not area_id:
                    area_id = area["area_id"]
                    break
            else:
                print("Couldn't find the requested area")
                return 1

            print("fetching conquest nodes")
            field_map_group_id = area[mode]["field_map_group_id"]
            field_map_group = self.quest_field_map_info(field_map_group_id)

            for node in field_map_group["field_map_data"]["nodes"]:
                if node["is_accessible"]:
                    quest_id = field_map_quests_by_node_id.get(
                        node["field_map_node_id"], None
                    )
                    if not quest_id:
                        continue
                    self.quest(quest_id, party_number)

    def conquest(self, area_id: int = None, party_number: int = 1, mode: str = "multi|solo"):
        field_map_quests = get_master("FieldMapQuest")
        field_map_quests_by_node_id = {
            quest["field_map_node_id"]: quest_id
            for quest_id, quest in field_map_quests.items()
        }
        faillist = []
        while True:
            print("fetching conquest info")
            res = self.quest_field_map_list()
            for area in res["areas"]:
                if area["area_id"] == area_id or not area_id:
                    area_id = area["area_id"]
                    break
            else:
                print("Couldn't find the requested area")
                return 1

            print("fetching conquest nodes")
            field_map_group_id = area[mode]["field_map_group_id"]
            field_map_group = self.quest_field_map_info(field_map_group_id)

            print("Looking for current bonus nodes")
            quest_id = None
            for node in field_map_group["field_map_data"]["nodes"]:
                if (
                    node["is_accessible"]
                    and node["domination_rate"]
                    not in [
                        None,
                        100,
                    ]
                    and node["field_map_node_id"] not in faillist
                ):
                    quest_id = field_map_quests_by_node_id.get(
                        node["field_map_node_id"], None
                    )
                    if quest_id:
                        print("Found", quest_id)
                        break
            else:
                print("No bonus node found")
                return

            fails = 0
            while True:
                quest_result = self.quest(quest_id, party_number)

                if quest_result["field_map_result"]:
                    print(quest_result["field_map_result"]["domination_rate"])
                    if quest_result["field_map_result"]["domination_rate"] == 100:
                        break
                if quest_result["battle"]["latest_turn_result"] in ["loss", "lost"]:
                    fails += 1
                    if fails == 5:
                        faillist.append("field_map_node_id")
                        break


    def quest(self, quest_id: int = 0, party_number: int = 1, repeat: int = 0, min_stam: int = -1, battle_id: int = None):
        if min_stam == -1:
            event_quests = get_master("EventQuest")
            story_quests = get_master("MainQuest")
            field_quests = get_master("FieldMapQuest")
            if quest_id in event_quests:
                quest = event_quests[quest_id]
            elif quest_id in story_quests:
                quest = story_quests[quest_id]
            elif quest_id in field_quests:
                quest = field_quests[quest_id]
            else:
                raise Exception("Couldn't find the requested quest")
            min_stam = quest["stamina"]

            print("Create battle", quest_id, quest["name"])
        else:
            print("Create battle", quest_id, "with min stamina", min_stam)
        
        if self.stamina < min_stam*2:
            self.stamina_refill(min_stam)
            sleep(1)
        res = self.quest_create(quest_id, party_number, battle_id = battle_id)

        if res.get("code", 0) == 4021:
            self.quest_retire()
            return self.quest(quest_id, party_number, repeat, min_stam)
        
        if "changed_resources" in res:
            self.stamina = res['changed_resources']['player']['stamina']
        else:
            print(res)
        if self.real:
            sleep(1)

        r = 1
        t = 1
        while True:
            print("Round", r, "Turn", t, end="\t")
            res_atk = self.quest_attack(commands=[], auto_battle_type=3)
            self.quest_status()
            t += 1
            # sleep some time according to res_atk
            if res_atk.get("code", 0) == 4022:
                self.stamina_refill(min_stam)
                return self.quest(quest_id, party_number, repeat)

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
        
        sleep(1)
        if repeat:
            return self.quest(quest_id, party_number, repeat - 1, min_stam, battle_id=battle_id)
        else:
            return res_atk
