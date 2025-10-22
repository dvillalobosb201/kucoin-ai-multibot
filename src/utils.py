import json, sys, time, yaml
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
LOG = DATA / "logs.json"

def now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def sleep_s(n: int):
    time.sleep(n)

def load_config(env: str):
    cfg_file = ROOT / "config" / ("live.yaml" if env == "live" else "paper.yaml")
    with cfg_file.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def log_json(obj):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": now_ts(), **obj}) + "\n")
