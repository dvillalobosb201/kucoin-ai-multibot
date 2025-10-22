import json
from pathlib import Path
from typing import Any, Dict, List
from .utils import now_ts

STATE_FILE = Path("data/.state.json")
DEFAULT: Dict[str, Any] = {"positions": {}, "open_trades": 0, "history": []}

def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            if isinstance(data, dict):
                for k in ("positions","open_trades","history"):
                    data.setdefault(k, DEFAULT[k])
                return data
        except json.JSONDecodeError:
            pass
    return DEFAULT.copy()

def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True, parents=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))

def record_buy(state, symbol, usdt, price):
    if usdt<=0 or price<=0: return state
    pos = state["positions"].get(symbol, {"qty_usdt":0.0,"avg_price":0.0,"last_buy_price":0.0})
    cur_usdt = float(pos["qty_usdt"])
    avg = float(pos["avg_price"]) or price
    cur_qty = cur_usdt/avg if avg>0 else 0.0
    add_qty = usdt/price
    new_qty = cur_qty + add_qty
    new_cost = cur_usdt + usdt
    new_avg = new_cost / new_qty if new_qty>0 else price
    pos.update({"qty_usdt": round(new_cost,2), "avg_price": round(new_avg,4), "last_buy_price": price})
    state["positions"][symbol] = pos
    state["history"].append({"ts": now_ts(), "symbol": symbol, "action":"buy", "usdt": usdt, "price": price, "pnl": 0.0})
    state["open_trades"] = sum(1 for p in state["positions"].values() if p["qty_usdt"]>0)
    return state

def record_sell(state, symbol, usdt, price):
    pos = state["positions"].get(symbol)
    if not pos or usdt<=0 or price<=0: return state
    cur_usdt = float(pos["qty_usdt"])
    if cur_usdt<=0: return state
    sell = min(cur_usdt, usdt)
    proportion = sell/cur_usdt
    avg = float(pos["avg_price"]) or price
    total_qty = cur_usdt/avg if avg>0 else 0.0
    qty_sold = total_qty * proportion
    pnl = (price - avg) * qty_sold
    remaining = cur_usdt - sell
    if remaining<=0: state["positions"].pop(symbol, None)
    else:
        pos["qty_usdt"] = round(remaining,2)
        state["positions"][symbol] = pos
    state["history"].append({"ts": now_ts(), "symbol": symbol, "action":"sell", "usdt": sell, "price": price, "pnl": round(pnl,4)})
    state["open_trades"] = sum(1 for p in state["positions"].values() if p["qty_usdt"]>0)
    return state
