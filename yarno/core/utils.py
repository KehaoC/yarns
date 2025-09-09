import json, os

def dump_json(path: str, obj: dict):
    """简单 JSON 写入"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)

def load_json(path: str) -> dict:
    """简单 JSON 读取"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)