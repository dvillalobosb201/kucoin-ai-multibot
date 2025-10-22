from __future__ import annotations
import logging
from typing import Any, Dict, List, Tuple, Optional
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange
from .risk import position_sizing, risk_ok
from .state import load_state, record_buy, record_sell, save_state
from .strategies.trend_follow import TrendFollowStrategy
from .strategies.dca import DollarCostAveragingStrategy
from .strategies.martingale import MartingaleStrategy
from .utils import now_ts, sleep_s

class Engine:
    def __init__(self, broker, config: Dict[str, Any], logger: logging.Logger, telegram_bot, chat_id: str, env: str) -> None:
        self.broker = broker
        self.config = config
        self.logger = logger
        self.telegram_bot = telegram_bot
        self.chat_id = chat_id
        self.env = env
        self.trend = TrendFollowStrategy(config)
        self.dca = DollarCostAveragingStrategy(config)
        self.martingale = MartingaleStrategy(config)

    @property
    def symbol(self) -> str:
        return f"{self.config['base_symbol']}-{self.config['quote_symbol']}"

    def smoke_test(self) -> None:
        df, ind = self._fetch_market_dataframe()
        server_time = self.broker.get_server_time().get("data")
        msg = (
            "✅ KuCoin Smoke Test\n"
            f"Symbol: {self.symbol}\n"
            f"Timeframe: {self.config['timeframe']}\n"
            f"Server time: {server_time}\n"
            f"Close: {ind['close']:.4f}\n"
            f"EMA(9): {ind['ema_fast']:.4f}\n"
            f"EMA(21): {ind['ema_slow']:.4f}\n"
            f"RSI(14): {ind['rsi']:.2f}\n"
            f"ATR(14): {ind['atr']:.6f}"
        )
        self._send_telegram(msg)
        self.logger.info({"event": "smoke_test", "status": "ok", "indicators": ind})

    def run_once(self) -> Dict[str, Any]:
        df, ind = self._fetch_market_dataframe()
        state = load_state()
        signals = self._collect_signals(df, state)
        agg = self._aggregate(signals)
        side = agg["side"]
        weight = agg["weight"]
        price = ind["close"]

        if side is None:
            self._send_telegram(self._fmt("no-trade", ind, "no-signal", 0.0, 0.0, price, {"reasons": agg["reasons"]}))
            self.logger.info({"event": "run_once", "side": None, "reasons": agg["reasons"]})
            return {"side": None, "reasons": agg["reasons"]}

        positions = state.get("positions", {})
        pos = positions.get(self.symbol, {})
        current_usdt = float(pos.get("qty_usdt", 0.0))

        if side != "sell" and not risk_ok(state.get("open_trades", 0), self.config):
            self._send_telegram("⚠️ Blocked by risk.")
            return {"side": side, "blocked": True}

        max_pos = float(self.config["risk"]["max_position_usdt"])
        balance_usdt = max(0.0, max_pos - current_usdt) if side == "buy" else current_usdt
        size_usdt = position_sizing(balance_usdt, weight, self.config, side)
        if size_usdt <= 0:
            self._send_telegram("⚠️ Size below min, skip.")
            return {"side": side, "size": 0.0}

        if side == "buy":
            record_buy(state, self.symbol, size_usdt, price)
        else:
            record_sell(state, self.symbol, size_usdt, price)
        save_state(state)

        self._send_telegram(self._fmt("trade", ind, side, weight, size_usdt, price, {"open_trades": state.get("open_trades",0)}))
        self.logger.info({"event":"trade","side":side,"size_usdt":size_usdt})
        return {"side": side, "size_usdt": size_usdt}

    def run_loop(self) -> None:
        while True:
            try:
                self.run_once()
            except Exception:
                self.logger.exception("Loop failure")
                sleep_s(5)
            else:
                sleep_s(self.config.get("loop_seconds", 60))

    # helpers
    def _fetch_market_dataframe(self) -> Tuple[pd.DataFrame, Dict[str, float]]:
        payload = self.broker.get_candles(self.symbol, self._map_tf(self.config["timeframe"]))
        data = payload.get("data")
        if not data:
            raise ValueError("No candle data")
        cols = ["open_time", "open", "close", "high", "low", "volume", "turnover"]
        df = pd.DataFrame(data, columns=cols)
        df["open_time"] = pd.to_datetime(df["open_time"].astype(float), unit="s", utc=True)
        for c in ["open","close","high","low","volume","turnover"]:
            df[c] = df[c].astype(float)
        df = df.sort_values("open_time").reset_index(drop=True)
        ema_fast = EMAIndicator(df["close"], window=self.config["strategy"]["ema_fast"]).ema_indicator()
        ema_slow = EMAIndicator(df["close"], window=self.config["strategy"]["ema_slow"]).ema_indicator()
        rsi = RSIIndicator(df["close"], window=self.config["strategy"]["rsi_period"]).rsi()
        atr = AverageTrueRange(df["high"], df["low"], df["close"], window=self.config["strategy"]["atr_period"]).average_true_range()
        df = df.assign(ema_fast=ema_fast, ema_slow=ema_slow, rsi=rsi, atr=atr).dropna().reset_index(drop=True)
        last = df.iloc[-1]
        ind = {"timestamp": now_ts(), "close": float(last["close"]), "ema_fast": float(last["ema_fast"]),
               "ema_slow": float(last["ema_slow"]), "rsi": float(last["rsi"]), "atr": float(last["atr"]),
               "volume": float(last["volume"]), "open_time": last["open_time"].isoformat()}
        return df, ind

    def _collect_signals(self, df, state):
        sigs = []
        if self.config["strategy"].get("use_trend"): sigs.append({"name":"trend", **self.trend.signal(df, state, self.symbol)})
        if self.config["strategy"].get("use_dca"): sigs.append({"name":"dca", **self.dca.signal(df, state, self.symbol)})
        if self.config["strategy"].get("use_martingale"): sigs.append({"name":"martingale", **self.martingale.signal(df, state, self.symbol)})
        return sigs

    def _aggregate(self, signals):
        votes = {"buy":0,"sell":0}
        reasons = {}
        weights = {"buy":[], "sell":[]}
        for s in signals:
            side = s.get("side")
            if s.get("name") and s.get("reason"): reasons[s["name"]] = s["reason"]
            if side in votes:
                votes[side]+=1
                if s.get("weight"): weights[side].append(float(s["weight"]))
        if votes["buy"] == votes["sell"]:
            return {"side": None, "weight": 0.0, "reasons": reasons}
        side = "buy" if votes["buy"] > votes["sell"] else "sell"
        w = sum(weights[side])/len(weights[side]) if weights[side] else 0.0
        return {"side": side, "weight": w, "reasons": reasons}

    def _send_telegram(self, text: str):
        if not self.telegram_bot or not self.chat_id: return
        try: self.telegram_bot.send_message(chat_id=self.chat_id, text=text)
        except Exception: self.logger.exception("Telegram send failed")

    def _map_tf(self, tf: str) -> str:
        m = {"1m":"1min","3m":"3min","5m":"5min","15m":"15min","30m":"30min","1h":"1hour","4h":"4hour","1d":"1day"}
        return m.get(tf, tf)

    def _fmt(self, event: str, ind, side, weight, size_usdt, price, extra):
        lines = [
            f"[{event}] {self.symbol}",
            f"Close: {ind['close']:.2f}",
            f"EMA(f/s): {ind['ema_fast']:.2f}/{ind['ema_slow']:.2f}",
            f"RSI: {ind['rsi']:.2f}",
            f"ATR: {ind['atr']:.6f}",
            f"Side: {side}",
            f"Weight: {weight:.2f}",
            f"Size: {size_usdt:.2f}",
            f"Price: {price:.2f}"
        ]
        for k,v in extra.items():
            lines.append(f"{k}: {v}")
        return "\n".join(lines)
