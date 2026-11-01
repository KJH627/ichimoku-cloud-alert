
import os
import json
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
STATE_FILE = "state.json"

def get_cloud_state(symbol):
    url = "https://api.bitget.com/api/v2/mix/market/candles"
    params = {
        "symbol": symbol,
        "productType": "USDT-FUTURES",
        "granularity": "1H",
        "limit": "100"
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "00000" or not result.get("data"):
        raise RuntimeError(f"{symbol}: Bitget 데이터 오류")

    candles = sorted(result["data"], key=lambda x: int(x[0]))
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]

    def midpoint(period, end):
        start = end - period + 1
        return (max(highs[start:end+1]) + min(lows[start:end+1])) / 2

    end = len(candles) - 1
    tenkan = midpoint(9, end)
    kijun = midpoint(26, end)
    span_a = (tenkan + kijun) / 2
    span_b = midpoint(52, end)

    return "BULL" if span_a > span_b else "BEAR"

def send_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20
    )
    response.raise_for_status()

def main():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            states = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        states = {}

    changed = False

    for symbol in SYMBOLS:
        current = get_cloud_state(symbol)
        previous = states.get(symbol)

        if previous is None:
            states[symbol] = current
            changed = True
            print(f"{symbol}: 최초 기준 상태 저장 ({current})")
            continue

        if current != previous:
            direction = "음운 → 양운 🟢" if current == "BULL" else "양운 → 음운 🔴"
            send_message(f"{symbol} 1시간봉 구름 전환 감지\n{direction}")
            states[symbol] = current
            changed = True
            print(f"{symbol}: {direction}")

    if changed:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(states, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
