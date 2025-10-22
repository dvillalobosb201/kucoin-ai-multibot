import argparse, logging, os
from telegram import Bot
from .utils import load_config, log_json
from . import broker as kb
from .engine import Engine

def make_logger():
    logger = logging.getLogger("kucoin-trader")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    return logger

def build_engine(env: str):
    cfg = load_config(env)
    logger = make_logger()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    bot = Bot(token=token) if token and chat_id else None
    eng = Engine(
        broker=type("Broker", (), {
            "get_server_time": staticmethod(kb.get_server_time),
            "get_candles": staticmethod(kb.get_candles)
        })(),
        config=cfg,
        logger=logger,
        telegram_bot=bot,
        chat_id=chat_id if bot else "",
        env=env
    )
    return eng

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    env = os.environ.get("ENV","paper")
    eng = build_engine(env)

    try:
        if args.smoke:
            eng.smoke_test()
        elif args.once:
            eng.run_once()
        else:
            eng.run_loop()
    except Exception as e:
        log_json({"event":"fatal","error":str(e)})
        raise

if __name__ == "__main__":
    main()
