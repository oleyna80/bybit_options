#!/bin/bash

# Путь к виртуальному окружению (предполагаем, что оно называется 'venv')
VENV_PATH="./venv"

# 1. Активация виртуального окружения
if [ -d "$VENV_PATH" ]; then
    echo "Активация виртуального окружения..."
    source "$VENV_PATH/bin/activate"
elif [ -d "$VENV_PATH/Scripts" ]; then
    # Для Windows/WSL
    echo "Активация виртуального окружения (Windows)..."
    source "$VENV_PATH/Scripts/activate"
else
    echo "Виртуальное окружение не найдено в '$VENV_PATH'. Пожалуйста, создайте его."
    exit 1
fi

# 2. Проверка и установка зависимостей
echo "Проверка и установка зависимостей..."
pip install -r requirements.txt

# 3. Запуск Uvicorn сервера
echo "Запуск Uvicorn сервера на http://127.0.0.1:8000..."
uvicorn api_example:app --reload --port 8000