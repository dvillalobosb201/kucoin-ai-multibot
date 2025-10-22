from typing import Any, Dict

def risk_ok(open_trades: int, config: Dict[str, Any]) -> bool:
    return open_trades < int(config.get("risk",{}).get("max_open_trades", 0))

def position_sizing(balance_usdt: float, agg_weight: float, config: Dict[str, Any], side: str) -> float:
    risk = config.get("risk",{})
    max_pos = float(risk.get("max_position_usdt", 0.0))
    min_order = float(risk.get("min_usdt_order", 0.0))
    agg_weight = max(0.0, min(1.0, float(agg_weight)))
    base = min(max_pos, max(0.0, float(balance_usdt)))
    if side == "sell": base = max(0.0, float(balance_usdt))
    size = round(base * agg_weight, 2)
    return size if size >= min_order else 0.0
