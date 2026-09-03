import requests
import time
import hmac
import hashlib
import os
import sys
from datetime import datetime, timezone, timedelta
import json
from typing import Any, Dict, List, Set
from dotenv import load_dotenv

# ==========================================
# ⚙️ CONFIGURATION & ENV LOADING
# ==========================================

# 1. Загружаем переменные из .env файла
load_dotenv()

# 2. Получаем ключи (используем имена переменных как в .env)
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
# Читаем настройку Testnet, если не задана - считаем False
IS_TESTNET = os.getenv("BYBIT_TESTNET", "False").lower() in ("true", "1", "yes")

BASE_COIN = "BTC"

# 3. Валидация: Проверяем, что ключи действительно загрузились
if not API_KEY or not API_SECRET:
    print("❌ ОШИБКА: API ключи не найдены!")
    print("Убедитесь, что у вас создан файл .env с переменными:")
    print("BYBIT_API_KEY=...")
    print("BYBIT_API_SECRET=...")
    sys.exit(1)

# ==========================================
# 🛠️ HELPERS
# ==========================================


def get_base_url():
    return "https://api-testnet.bybit.com" if IS_TESTNET else "https://api.bybit.com"


def sign_request(param_str):
    """Подпись запроса для Bybit V5"""
    timestamp = str(int(time.time() * 1000))
    recv_window = str(5000)

    payload = timestamp + API_KEY + recv_window + param_str

    # Подписываем, используя секретный ключ из env
    signature = hmac.new(
        bytes(API_SECRET, "utf-8"), bytes(payload, "utf-8"), hashlib.sha256
    ).hexdigest()

    return {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-SIGN-TYPE": "2",
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window,
        "Content-Type": "application/json",
    }


def fetch_executions_window(start_ms: int, end_ms: int) -> List[Dict[str, Any]]:
    """Загрузить все трейды в окне [start_ms, end_ms] с пагинацией."""
    endpoint = "/v5/execution/list"
    cursor = None
    all_trades: List[Dict[str, Any]] = []

    while True:
        params = {
            "category": "option",
            "baseCoin": BASE_COIN,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
            "orderBy": "execTime",
            "direction": "desc",
        }
        if cursor:
            params["cursor"] = cursor

        url = f"{get_base_url()}{endpoint}"
        prepared = requests.Request("GET", url, params=params).prepare()
        param_str = prepared.url.split("?", 1)[1] if "?" in prepared.url else ""
        headers = sign_request(param_str)

        try:
            response = requests.get(url, params=params, headers=headers).json()
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            break

        if response.get("retCode") != 0:
            print(f"❌ API Error ({response.get('retCode')}): {response.get('retMsg')}")
            break

        page = response["result"].get("list", []) or []
        all_trades.extend(page)
        cursor = response["result"].get("nextPageCursor")
        if not cursor or not page:
            break
        time.sleep(0.2)  # чуть медленнее, чтобы не упереться в rate limit

    return all_trades


def fetch_year_history(window_days: int = 6) -> List[Dict[str, Any]]:
    """Получить историю за последние 7 дней."""
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)  # ← Только последние 7 дней

    all_trades: List[Dict[str, Any]] = []
    current_end = now
    while current_end > one_week_ago:  # ← Тут тоже
        current_start = max(
            one_week_ago, current_end - timedelta(days=window_days)
        )  # ← И тут
        start_ms = int(current_start.timestamp() * 1000)
        end_ms = int(current_end.timestamp() * 1000)
        print(f"⏳ Окно {current_start.date()} — {current_end.date()}")
        trades = fetch_executions_window(start_ms, end_ms)
        all_trades.extend(trades)
        current_end = current_start
    return all_trades


def save_json(path: str, data: Any):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранили {len(data)} записей в {path}")
    except Exception as e:
        print(f"❌ Не удалось сохранить {path}: {e}")


def print_sample(trades: List[Dict[str, Any]]):
    if not trades:
        print("📭 Сделок не найдено.")
        return
    print("🧾 Пример полного объекта сделки (первый элемент list):")
    print(json.dumps(trades[0], ensure_ascii=False, indent=2))


def print_table(trades: List[Dict[str, Any]]):
    header = (
        f"{'ВРЕМЯ (UTC)':<19} | {'РЫНОК':<24} | {'ИНСТР':<6} | "
        f"{'ТИП ОРД.':<9} | {'SIDE':<5} | {'EXEC VALUE':<11} | "
        f"{'EXEC PRICE':<10} | {'EXEC QTY':<9} | {'EXEC TYPE':<9} | "
        f"{'FEE':<8} | {'EXEC ID':<18} | {'IV':<7} | {'IDX PRICE':<10}"
    )
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    for t in trades:
        dt_object = datetime.fromtimestamp(int(t["execTime"]) / 1000, tz=timezone.utc)
        time_str = dt_object.strftime("%Y-%m-%d %H:%M:%S")

        symbol = t.get("symbol", "")
        category = t.get("category", "")
        order_type = t.get("orderType", "")
        side = t.get("side", "").upper()
        exec_value = t.get("execValue", "0")
        price = float(t["execPrice"])
        qty = float(t["execQty"])
        iv_raw = t.get("markIv", "0")
        iv = float(iv_raw) * 100 if iv_raw else 0.0
        idx_price = float(t["indexPrice"])
        exec_type = t.get("execType", "")
        exec_fee = t.get("execFee", "0")
        exec_id = t.get("execId", "")

        color = "\033[92m" if side == "BUY" else "\033[91m"
        reset = "\033[0m"

        row = (
            f"{time_str:<19} | {symbol:<24} | {category:<6} | "
            f"{order_type:<9} | {color}{side:<5}{reset} | {exec_value:<11} | "
            f"{price:<10.4f} | {qty:<9.4f} | {exec_type:<9} | "
            f"{exec_fee:<8} | {exec_id:<18} | {iv:<6.2f}% | {idx_price:<10.2f}"
        )
        print(row)

    print("-" * len(header))
    print(f"✅ Всего сделок: {len(trades)}")


# ==========================================
# 🖥️ MAIN
# ==========================================


def main():
    print(f"\n🔎 История сделок по {BASE_COIN} Options (последний год)...")
    print(f"   Mode: {'TESTNET' if IS_TESTNET else 'MAINNET'}\n")

    # 1) Первичная загрузка за год
    trades = fetch_year_history(
        window_days=6
    )  # Bybit лимит 7 дней, ставим 6 для запаса
    print_sample(trades)
    print(f"✅ Всего сделок за год: {len(trades)}")
    save_json("bybit_option_fills_year.json", trades)

    seen: Set[str] = {t.get("execId") for t in trades if t.get("execId")}

    # 2) Поллинг каждые 60 секунд (последние 5 минут)
    poll_window_minutes = 5
    while True:
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=poll_window_minutes)
        print(f"\n⏳ Поллинг: {start.isoformat()} — {end.isoformat()}")
        new_trades = fetch_executions_window(
            int(start.timestamp() * 1000), int(end.timestamp() * 1000)
        )
        fresh = [t for t in new_trades if t.get("execId") and t["execId"] not in seen]
        if fresh:
            print(f"🆕 Найдено новых сделок: {len(fresh)}")
            trades.extend(fresh)
            for t in fresh:
                seen.add(t["execId"])
            save_json("bybit_option_fills_year.json", trades)
        else:
            print("ℹ️ Новых сделок нет.")

        time.sleep(60)


if __name__ == "__main__":
    main()
