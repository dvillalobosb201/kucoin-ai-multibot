from typing import Any, Dict

class TrendFollowStrategy:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.cfg = config
    def signal(self, df, state, symbol) -> Dict[str, Any]:
        if len(df)<3: return {"side": None, "weight": 0.0, "reason": "insufficient"}
        emaf_prev, emaf = float(df["ema_fast"].iloc[-2]), float(df["ema_fast"].iloc[-1])
        emas_prev, emas = float(df["ema_slow"].iloc[-2]), float(df["ema_slow"].iloc[-1])
        rsi = float(df["rsi"].iloc[-1])
        if emaf_prev <= emas_prev and emaf > emas and rsi > 50:
            return {"side":"buy","weight":1.0,"reason":"ema_cross_up"}
        if emaf_prev >= emas_prev and emaf < emas and rsi < 50:
            return {"side":"sell","weight":1.0,"reason":"ema_cross_down"}
        return {"side": None, "weight": 0.0, "reason": "no_cross"}
