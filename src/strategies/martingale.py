from typing import Any, Dict

class MartingaleStrategy:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.cfg = config
    def signal(self, df, state, symbol) -> Dict[str, Any]:
        hist = state.get("history",[])
        last_sell = next((e for e in reversed(hist) if e.get("action")=="sell"), None)
        if not last_sell: return {"side": None, "weight": 0.0, "reason":"no_sell_history"}
        pnl = float(last_sell.get("pnl",0.0))
        if pnl >= 0: return {"side": None, "weight": 0.0, "reason":"last_sell_profitable"}
        pos = state.get("positions",{}).get(symbol)
        cur = float(pos.get("qty_usdt",0.0)) if pos else 0.0
        risk = self.cfg.get("risk",{})
        max_pos = float(risk.get("max_position_usdt",0.0))
        min_order = float(risk.get("min_usdt_order",0.0))
        avail = max(0.0, max_pos-cur)
        if avail < min_order: return {"side": None, "weight": 0.0, "reason":"max_position_reached"}
        factor = float(self.cfg["strategy"].get("martingale_factor",1.0))
        factor = min(factor, 1.5)
        base = 0.5
        weight = min(1.0, base*factor)
        return {"side":"buy","weight":round(weight,2),"reason":"martingale_after_loss"}
