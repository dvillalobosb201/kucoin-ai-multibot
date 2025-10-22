import requests

BASE = "https://api.kucoin.com"

def get_server_time():
    r = requests.get(f"{BASE}/api/v1/timestamp", timeout=10)
    r.raise_for_status()
    return r.json()

def get_candles(symbol: str, kline: str):
    # KuCoin expects 'type' like '1min','3min','5min','1hour', etc.
    params = {"type": kline, "symbol": symbol, "startAt": None, "endAt": None}
    r = requests.get(f"{BASE}/api/v1/market/candles", params=params, timeout=10)
    r.raise_for_status()
    return r.json()
