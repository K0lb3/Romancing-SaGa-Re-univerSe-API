import os
import json
from settings import DUMP_PATH

master_cache = {}
skill_cache = {}


def get_master(name: str):
    data = master_cache.get(name, None)
    if data:
        return data

    with open(
        os.path.join(DUMP_PATH, "master", f"{name}.json"), "rt", encoding="utf8"
    ) as f:
        data = json.load(f)
        data = {item["id"]: item for item in data["objectArray"]}

    master_cache[name] = data
    return data


def get_skill_duration(skill_id: int):
    duration = skill_cache.get("skill_id", 0)
    if duration:
        return skill_cache[skill_id]

    skill = get_master("Skill")[skill_id]
    track = {}
    with open(
        os.path.join(
            DUMP_PATH, "animation", f"skill{skill['skill_effect']}", "Sprite Track.json"
        ),
        "rt",
        encoding="utf8",
    ) as f:
        track = json.load(f)
        clips = track.get("m_Clips", [])
        if len(clips) == 0:
            skill_cache[skill_id] = 2
            return 2
        entry = track["m_Clips"][-1]

    duration = entry["m_Start"] + entry["m_Duration"]
    skill_cache[skill_id] = duration
    return duration


def get_round_duration(skill_ids: list[int]) -> float:
    return (
        sum(get_skill_duration(skill_id) for skill_id in skill_ids)
        + len(skill_ids) / 10
    )


if __name__ == "__main__":
    print(110100000, get_skill_duration(125100017))
    print(110100001, get_skill_duration(110100001))
    print("+", get_round_duration([110100000, 110100001]))
