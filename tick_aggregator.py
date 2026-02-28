import argparse
import json
import logging
from collections import defaultdict
from datetime import datetime

import redis


def minute_bucket(ts):
    dt = datetime.fromtimestamp(float(ts))
    return dt.strftime("%Y%m%d_%H%M")


def update_ohlcv(state, price, volume):
    if state["open"] is None:
        state["open"] = price
        state["high"] = price
        state["low"] = price
        state["close"] = price
        state["volume"] = volume
        return
    state["high"] = max(state["high"], price)
    state["low"] = min(state["low"], price)
    state["close"] = price
    state["volume"] += volume


def build_summary(symbol, minute_key, state):
    return {
        "symbol": symbol,
        "minute": minute_key,
        "open": state["open"],
        "high": state["high"],
        "low": state["low"],
        "close": state["close"],
        "volume": state["volume"],
    }


def parse_tick(raw_data):
    data = json.loads(raw_data)
    price = float(data["price"])
    volume = float(data["volume"])
    timestamp = float(data["timestamp"])
    symbol = data.get("symbol")
    return symbol, price, volume, timestamp


def main():
    parser = argparse.ArgumentParser(description="Real-time tick data aggregator")
    parser.add_argument("--redis-url", default="redis://localhost:8080/0")
    parser.add_argument("--channel", default="BTCUSDT")
    parser.add_argument("--symbol", default="BTCUSDT")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    r = redis.Redis.from_url(args.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe(args.channel)
    logging.info("Subscribed to channel: %s", args.channel)

    agg = defaultdict(
        lambda: {
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": 0.0,
        }
    )
    last_published_minute = None

    for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        try:
            tick_symbol, price, volume, ts = parse_tick(msg["data"])
            symbol = tick_symbol or args.symbol
            current_minute = minute_bucket(ts)

            if last_published_minute is None:
                last_published_minute = current_minute

            if current_minute != last_published_minute:
                summary = build_summary(symbol, last_published_minute, agg[last_published_minute])
                key = f"{symbol}:{last_published_minute}"
                payload = json.dumps(summary)
                r.set(key, payload)
                r.publish(key, payload)
                logging.info("Published summary: %s -> %s", key, payload)
                del agg[last_published_minute]
                last_published_minute = current_minute

            update_ohlcv(agg[current_minute], price, volume)
            logging.info(
                "Processed tick symbol=%s price=%s volume=%s minute=%s",
                symbol,
                price,
                volume,
                current_minute,
            )
        except Exception as exc:
            logging.exception("Failed processing message: %s", exc)


if __name__ == "__main__":
    main()
