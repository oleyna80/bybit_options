# Option Board Fetcher Tools

Инструменты для получения полной доски опционов BTC-2JAN26 со страйками от 75000 до 110000 с шагом 1000.

## 📊 Доступные скрипты

### 1. **`get_option_board.py`** - Табличный формат (рекомендуется для трейдеров)
Красиво отформатированная таблица для быстрого визуального анализа.

```bash
# Получить всю доску опционов BTC-2JAN26 (75000-110000)
python get_option_board.py

# Получить только коллы
python get_option_board.py --type call

# Получить только путы  
python get_option_board.py --type put

# Указать свой диапазон страйков
python get_option_board.py --min-strike 80000 --max-strike 90000 --step 500

# Сохранить в Markdown файл
python get_option_board.py --save option_board.md

# Сортировать по IV (подразумеваемой волатильности)
python get_option_board.py --sort-by iv --sort-order desc
```

### 2. **`get_option_board_json.py`** - JSON формат (для автоматизации)
Структурированный JSON вывод для программирования, логирования и интеграции.

```bash
# Получить JSON вывод
python get_option_board_json.py

# Сохранить в файл
python get_option_board_json.py --output option_board.json

# Получить только коллы с кастомным диапазоном
python get_option_board_json.py --type call --min-strike 80000 --max-strike 90000

# Указать отступ JSON
python get_option_board_json.py --indent 4
```

## 🎯 Использование

### Получение данных доски опционов
```bash
# Базовая команда (получить все опционы BTC-2JAN26)
python get_option_board.py

# Пример вывода:
# ====================================================================================
# BTC-2JAN26 OPTION BOARD
# Generated: 2025-12-18 17:30:00 UTC
# Underlying BTC Price: $88,285.00
# Options: 72 successful, 0 failed
# ====================================================================================
# | STRIKE | TYPE | MONEY | MARK | BID/ASK | SPREAD% | IV% | DELTA | GAMMA | VEGA | THETA | OI |
# |--------|------|-------|------|---------|---------|-----|-------|-------|------|-------|----|
# | 75,000 | CALL | ITM   | $1,234.56 | $1,230/$1,240 | 0.81% | 55.6% | +0.8234 | 0.00012 | +21.38 | -176.55 | 1,234 |
# | 75,000 | PUT  | OTM   | $456.78 | $455/$460 | 1.10% | 55.8% | -0.1754 | 0.00006 | +21.56 | -176.27 | 567 |
# ... и так далее для всех страйков
```

### Программное использование
```python
import asyncio
import json
from get_option_board_json import fetch_option_board_json
from bybit_connector import BybitConnector

async def analyze_option_board():
    # Инициализация коннектора
    connector = BybitConnector(api_key="...", api_secret="...")
    
    # Генерация символов
    from option_board_utils import generate_option_symbols
    symbols = generate_option_symbols(
        base_coin="BTC",
        expiry="2JAN26",
        min_strike=75000,
        max_strike=110000,
        step=1000
    )
    
    # Получение данных
    async with connector:
        board_data = await fetch_option_board_json(connector, symbols)
    
    # Анализ данных
    print(f"Underlying price: ${board_data['market_data']['underlying_price']:,.2f}")
    print(f"Total options: {board_data['results']['successful_count']}")
    
    # Найти опционы с наименьшим спредом
    options = board_data['options']
    sorted_by_spread = sorted(options, key=lambda x: x['spread']['percent'])
    print(f"Tightest spread: {sorted_by_spread[0]['symbol']} ({sorted_by_spread[0]['spread']['percent']:.2f}%)")

asyncio.run(analyze_option_board())
```

## 📋 Формат символов

Символы опционов следуют паттерну:
```
BTC-DDMMMYY-STRIKE-TYPE-USDT
```

Примеры:
- `BTC-2JAN26-75000-C` → Колл, страйк 75k, экспирация 2 января 2026
- `BTC-2JAN26-75000-P` → Пут, страйк 75k, экспирация 2 января 2026
- `BTC-19DEC25-82000-P` → Пут, страйк 82k, экспирация 19 декабря 2025

**Примечание:** Скрипты автоматически добавляют суффикс `-USDT` если он опущен.

## 🔑 Требования

1. **Настройка окружения** (одноразово)
   - Файл `.env` с `BYBIT_API_KEY` и `BYBIT_API_SECRET`
   - Или установить как переменные окружения

2. **Зависимости** (уже в проекте)
   - `bybit_connector.py` - клиент API Bybit
   - `option_board_utils.py` - утилиты для работы с опционами
   - `python 3.8+` с `asyncio`

## 📊 Структура данных

### Табличный вывод включает:
- **Цены**: Марк, бид, аск, последняя сделка
- **Спред**: Абсолютный и процентный
- **Подразумеваемая волатильность (IV)**: Бидовская, марковая, асковая
- **Греки**: Дельта, Гамма, Вега, Тета
- **Ликвидность**: Открытый интерес, объем 24ч, размер стакана
- **Денежность**: ITM (в деньгах), ATM (при деньгах), OTM (вне денег)

### JSON структура:
```json
{
  "metadata": {
    "timestamp": "2025-12-18T17:30:00Z",
    "generator": "bybit-options-risk-engine",
    "version": "1.0.0"
  },
  "market_data": {
    "underlying_price": 88285.00,
    "underlying_symbol": "BTCUSDT"
  },
  "results": {
    "successful_count": 72,
    "failed_count": 0,
    "success_rate": 1.0
  },
  "statistics": {
    "total_options": 72,
    "calls_count": 36,
    "puts_count": 36,
    "moneyness_distribution": {
      "ITM": 12,
      "ATM": 8,
      "OTM": 52
    },
    "averages": {
      "spread_percent": 1.23,
      "iv": 0.556
    }
  },
  "options": [
    {
      "symbol": "BTC-2JAN26-75000-C-USDT",
      "strike": 75000,
      "type": "call",
      "moneyness": "ITM",
      "prices": {
        "mark": 1234.56,
        "bid": 1230.0,
        "ask": 1240.0,
        "last": 1235.0,
        "underlying": 88285.0
      },
      "spread": {
        "absolute": 10.0,
        "percent": 0.81
      },
      "iv": {
        "bid": 0.555,
        "mark": 0.556,
        "ask": 0.557
      },
      "greeks": {
        "delta": 0.8234,
        "gamma": 0.00012,
        "vega": 21.38,
        "theta": -176.55
      },
      "liquidity": {
        "bid_size": 5.06,
        "ask_size": 8.0,
        "open_interest": 1234.0,
        "volume_24h": 216.2,
        "turnover_24h": 18920767.0
      }
    }
  ]
}
```

## 🚀 Примеры использования

### Анализ хеджирования
```bash
# Получить защитные путы (OTM puts)
python get_option_board.py --type put --min-strike 75000 --max-strike 80000

# Найти опционы с наименьшим спредом для торговли
python get_option_board.py --sort-by spread --sort-order asc
```

### Сравнение волатильности
```bash
# Сравнить IV коллов и путов
python get_option_board_json.py --type call > calls.json
python get_option_board_json.py --type put > puts.json

# Анализировать volatility smile
python get_option_board.py --save volatility_smile.md
```

### Автоматизация и мониторинг
```bash
# Ежедневный сбор данных
python get_option_board_json.py --output "data/option_board_$(date +%Y%m%d).json"

# Мониторинг спредов
python get_option_board.py | grep "SPREAD%" | sort -k6 -n
```

## 💡 Советы для трейдеров

1. **Сравнение спредов**: Более широкие спреды на менее ликвидных страйках = риск проскальзывания
2. **Уровни IV**: Высокая IV = дорого покупать опционы, выгодно продавать
3. **Греки**: Высокая гамма около ATM = большие дневные колебания теты
4. **Временной распад**: Тета ускоряется при приближении экспирации
5. **Актуальные данные**: Всегда получайте свежие котировки перед входом в позиции

## 🐛 Устранение неполадок

**"No data returned" ошибка:**
- Проверьте правильность формата символа
- Убедитесь, что срок экспирации опциона не истек
- Проверьте API ключи в `.env`

**Ошибка соединения:**
- Убедитесь в наличии интернет-соединения
- Проверьте валидность API ключей
- Проверьте лимиты запросов (Bybit: 50 запросов/секунду)

**Неожиданные цены:**
- Bybit обновляет марковые цены каждые 100мс
- Котировки обновляются при каждом запуске скрипта
- Для реального времени: создайте вариант с вебсокетом

## 📝 Интеграция с существующим проектом

Новые скрипты используют существующую инфраструктуру:

### Общие компоненты:
- **`BybitConnector`** - для API запросов
- **Конфигурация** из `.env` файла
- **Модели данных** Pydantic
- **Логирование** и обработка ошибок

### Утилиты:
- **`option_board_utils.py`** - общие функции для работы с опционами:
  - `generate_option_symbols()` - генерация символов
  - `parse_option_symbol()` - парсинг символов
  - `calculate_moneyness()` - расчет денежности
  - `format_option_display()` - форматирование данных
  - `calculate_board_statistics()` - статистика доски

## 🔄 Параметры командной строки

### `get_option_board.py`:
```
--type {all,call,put}    Тип опциона (по умолчанию: all)
--min-strike MIN         Минимальный страйк (по умолчанию: 75000)
--max-strike MAX         Максимальный страйк (по умолчанию: 110000)
--step STEP              Шаг страйка (по умолчанию: 1000)
--save FILE              Сохранить вывод в Markdown файл
--sort-by {strike,mark_price,delta,iv,spread}
                         Сортировать по полю (по умолчанию: strike)
--sort-order {asc,desc}  Порядок сортировки (по умолчанию: asc)
```

### `get_option_board_json.py`:
```
--type {all,call,put}    Тип опциона (по умолчанию: all)
--min-strike MIN         Минимальный страйк (по умолчанию: 75000)
--max-strike MAX         Максимальный страйк (по умолчанию: 110000)
--step STEP              Шаг страйка (по умолчанию: 1000)
--output FILE            Выходной файл (по умолчанию: stdout)
--indent INDENT          Отступ JSON (по умолчанию: 2)
--sort-by {strike,mark_price,delta,iv,spread}
                         Сортировать по полю (по умолчанию: strike)
--sort-order {asc,desc}  Порядок сортировки (по умолчанию: asc)
```

## 📈 Производительность

- **Пакетная обработка**: Запросы группами по 20 символов для оптимизации
- **Параллельные запросы**: Использование `asyncio.gather` для скорости
- **Кэширование**: Возможность кэширования для повторяющихся запросов
- **Типичное время выполнения**: 3-10 секунд для 72 опционов

## 📄 Лицензия и атрибуция

Часть проекта `bybit-options-risk-engine`.
Использует Bybit V5 Public API для данных рынка опционов.

---

**Готово для продакшена. Асинхронно с нуля. Интегрировано в существующую инфраструктуру.** 🚀