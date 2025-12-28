# Options Risk Engine - Инструкция по запуску

## 📋 Описание проекта
Options Risk Engine - это система для анализа рисков опционов Bybit с доской опционов, real-time обновлениями и расчетом греков.

## 🚀 Автоматический запуск (VS Code)

### Настроенный автозапуск
При открытии проекта в VS Code backend автоматически запускается через задачу "Start Backend".

**Что происходит:**
1. Активируется виртуальное окружение `venv`
2. Устанавливаются зависимости из `requirements.txt`
3. Запускается Uvicorn сервер на порту 8000

**Файлы конфигурации:**
- [`startup.sh`](startup.sh) - скрипт запуска
- [`.vscode/tasks.json`](.vscode/tasks.json) - задача VS Code

## 🛠️ Ручной запуск

### 1. Запуск backend
```bash
# Способ 1: Использовать скрипт startup.sh
bash startup.sh

# Способ 2: Вручную
source venv/bin/activate  # Активация venv
pip install -r requirements.txt  # Установка зависимостей
uvicorn api_example:app --reload --port 8000  # Запуск сервера
```

### 2. Запуск frontend
```bash
cd frontend
npm install  # Установка зависимостей (первый раз)
npm run dev  # Запуск dev сервера
```

## ✅ Проверка работы

### Проверка backend
```bash
# Проверить, что сервер работает
curl http://localhost:8000/

# Проверить API доски опционов
curl "http://localhost:8000/api/v1/options-board?base_coin=BTC&limit=5"

# Проверить health endpoint
curl http://localhost:8000/health
```

**Ожидаемый ответ:**
```json
{
  "status": "ok",
  "message": "Options Risk Engine API is running"
}
```

### Проверка frontend
Откройте в браузере: http://localhost:5173

## 🔧 Устранение неполадок

### Проблема: "Виртуальное окружение не найдено"
**Решение:**
```bash
# Создать виртуальное окружение
python3 -m venv venv

# Активировать
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### Проблема: "Порт 8000 занят"
**Решение:**
```bash
# Изменить порт в startup.sh
# Или убить процесс на порту 8000
lsof -ti:8000 | xargs kill -9
```

### Проблема: "API ключи не найдены"
**Решение:**
1. Убедитесь, что файл [`.env`](.env) существует
2. Проверьте наличие переменных `BYBIT_API_KEY` и `BYBIT_API_SECRET`
3. Используйте `.env.example` как шаблон

## 📊 Полезные команды

### CLI утилиты
```bash
# Показать доску опционов в терминале
python get_option_board.py --base-coin BTC --limit 20

# Получить котировки опциона
python get_option_quotes.py --symbol BTC-27DEC24-90000-C

# Тестирование API
python test_api.py
```

### Управление сервером
```bash
# Остановить сервер
Ctrl+C в терминале с Uvicorn

# Перезапустить сервер
# Просто закройте и откройте проект заново в VS Code
# Или выполните bash startup.sh вручную
```

## 📁 Структура проекта
```
├── api_example.py          # Основной FastAPI сервер
├── bybit_connector.py      # Подключение к Bybit API
├── option_board_utils.py   # Утилиты для доски опционов
├── frontend/              # React/TypeScript frontend
├── .vscode/              # Конфигурация VS Code
│   └── tasks.json        # Задача автозапуска
├── startup.sh            # Скрипт запуска
└── README_START.md       # Эта инструкция
```

## 📞 Поддержка
При возникновении проблем:
1. Проверьте логи в терминале VS Code
2. Убедитесь, что API ключи Bybit корректны
3. Проверьте подключение к интернету
4. Убедитесь, что используется правильная сеть (mainnet/testnet)

---
*Последнее обновление: $(date)*