from typing import Any, Dict

class DollarCostAveragingStrategy:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.cfg = config
    def signal(self, df, state, symbol) -> Dict[str, Any]:
        pos = state.get("positions",{}).get(symbol)
        if not pos or float(pos.get("qty_usdt",0.0))<=0:
            return {"side": None, "weight": 0.0, "reason":"no_position"}
        last_buy = float(pos.get("last_buy_price") or 0.0)
        if last_buy<=0: return {"side": None, "weight": 0.0, "reason":"no_reference"}
        price = float(df["close"].iloc[-1])
        drop = ((last_buy - price)/last_buy)*100 if last_buy else 0.0
        th = float(self.cfg["strategy"].get("dca_drop_pct",1.0))
        if drop < th: return {"side": None, "weight": 0.0, "reason":"drop_below_threshold"}
        risk = self.cfg.get("risk",{})
        max_pos = float(risk.get("max_position_usdt",0.0))
        min_order = float(risk.get("min_usdt_order",0.0))
        cur = float(pos.get("qty_usdt",0.0))
        available = max(0.0, max_pos-cur)
        if available < min_order: return {"side": None, "weight": 0.0, "reason":"max_position_reached"}
        ratio = available/max_pos if max_pos else 0.0
        weight = max(0.3, min(0.5, ratio if ratio>0 else 0.3))
        return {"side":"buy","weight":round(weight,2),"reason":f"dca_drop_{drop:.2f}%"}
