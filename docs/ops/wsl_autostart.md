# WSL Autostart (HIST-005)

Документ описывает автозапуск истории трейдов и snapshot’ов портфеля в WSL.

## Требуемые переменные окружения

Обязательно:

- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`
- `DATABASE_URL`

Опционально:

- `BYBIT_TESTNET` (default: `true`)

> Базовые переменные окружения и примеры `.env` см. в [`docs/ops/running.md`](docs/ops/running.md).

## Вариант 1 (рекомендованный): systemd ON

### 1) Включить systemd в WSL

Создать или обновить `/etc/wsl.conf`:

```ini
[boot]
systemd=true
```

Перезапустить WSL:

```bash
wsl --shutdown
```

### 2) Установить units

```bash
mkdir -p ~/.config/systemd/user
cp /home/dmitrii/projects/bybit_options/scripts/systemd/bybit-wsl-startup.service ~/.config/systemd/user/
cp /home/dmitrii/projects/bybit_options/scripts/systemd/bybit-portfolio-snapshot.service ~/.config/systemd/user/
cp /home/dmitrii/projects/bybit_options/scripts/systemd/bybit-portfolio-snapshot.timer ~/.config/systemd/user/

systemctl --user daemon-reload
```

> Units используют `EnvironmentFile=/home/dmitrii/projects/bybit_options/.env`.
> Если `.env` отсутствует, создайте его или добавьте переменные через `systemctl --user edit <unit>`.

### 3) Включить автозапуск

```bash
systemctl --user enable --now bybit-wsl-startup.service
systemctl --user enable --now bybit-portfolio-snapshot.timer
```

### 4) Логи

```bash
journalctl --user -u bybit-wsl-startup.service -f
journalctl --user -u bybit-portfolio-snapshot.service -f
```

## Вариант 2 (fallback): systemd OFF

Добавьте в `~/.profile` (или `~/.bashrc`, если нет login shell):

```bash
if [ -z "${BYBIT_WSL_AUTOSTART_DONE:-}" ] && [ -x /home/dmitrii/projects/bybit_options/scripts/wsl_startup.sh ]; then
  export BYBIT_WSL_AUTOSTART_DONE=1
  /home/dmitrii/projects/bybit_options/scripts/wsl_startup.sh >/tmp/bybit_options_wsl_startup.out 2>&1 &
fi
```

Логи fallback-режима:

- stdout/err: `/tmp/bybit_options_wsl_startup.out`
- portfolio snapshots: `/home/dmitrii/projects/bybit_options/logs/portfolio_syncer.log`

## Что делает startup

Скрипт [`scripts/wsl_startup.sh`](scripts/wsl_startup.sh) выполняет:

1. Проверку, что `trades` не пустая; при необходимости — backfill `--days 180`.
2. Инкрементальную синхронизацию истории трейдов.
3. Запуск snapshot’ов портфеля (через systemd timer или fallback loop).
