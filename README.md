python tick_aggregator.py --redis-url redis://localhost:6379/0 --channel BTCUSDT --symbol BTCUSDT
```

## Test with 2 terminals

1. Terminal A: run aggregator

```bash
python tick_aggregator.py --redis-url redis://localhost:6379/0 --channel BTCUSDT --symbol BTCUSDT
```

2. Terminal B: publish valid ticks (from normal shell)

```bash
input: 
redis-cli PUBLISH BTCUSDT "{\"symbol\":\"BTCUSDT\",\"price\":100.0,\"volume\":1.2,\"timestamp\":$(date +%s)}"
redis-cli PUBLISH BTCUSDT "{\"symbol\":\"BTCUSDT\",\"price\":101.5,\"volume\":0.8,\"timestamp\":$(date +%s)}"
redis-cli PUBLISH BTCUSDT "{\"symbol\":\"OHCVL\",\"price\":101.0,\"volume\":1.5,\"timestamp\":$(date +%s)}"

testing: 
redis-cli --scan --pattern "*:*"
redis-cli GET OHCVL:YYYYMMDD_HHMM ... example: redis-cli GET OHCVL:20260228_0011

```

3. Wait for next minute, then publish one more tick to trigger summary publish

```bash
redis-cli PUBLISH BTCUSDT "{\"symbol\":\"BTCUSDT\",\"price\":102.0,\"volume\":0.3,\"timestamp\":$(date +%s)}"
```

4. Check generated key/value

```bash
redis-cli --scan --pattern "BTCUSDT:*"
redis-cli GET BTCUSDT:YYYYMMDD_HHMM
```

Notes:
- Replace `BTCUSDT:YYYYMMDD_HHMM` with the actual key from `--scan`.
- If you are inside interactive `redis-cli`, do not use `$(date +%s)` there (it will not expand).

## Tick format

Publish ticks to the subscribed channel as JSON:
```

`timestamp` should be Unix epoch seconds.