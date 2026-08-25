# Telegram-бот сбора заявок

Пользователь оставляет имя и город — бот сохраняет заявку и отвечает, что с ним свяжется координатор.
Администраторы из `.env` могут посмотреть список всех, кто прошёл сценарий.

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Скопируйте `.env.example` в `.env` и заполните:

| Переменная     | Описание                                                        |
| -------------- | --------------------------------------------------------------- |
| `BOT_TOKEN`    | Токен от [@BotFather](https://t.me/BotFather)                     |
| `ADMIN_IDS`    | Telegram ID админов через запятую (свой узнать: @userinfobot)     |
| `DATABASE_URL` | По умолчанию `sqlite+aiosqlite:///bot_database.db`                |

Без `BOT_TOKEN` или `ADMIN_IDS` бот не стартует — падает сразу с понятной ошибкой,
а не в момент первого сообщения.

## Запуск

```bash
python bot.py
```

## Сценарий

1. `/start` → «Есть люди, которые готовы действовать. Кто-то должен навести порядок.» → «Как вас зовут?»
2. Пользователь пишет имя → «Из какого вы города?»
3. Пользователь пишет город → «Координатор свяжется с вами в ближайшее время.»

Тексты сообщений — константы `GREETING`, `ASK_NAME`, `ASK_CITY`, `DONE` в начале `handlers.py`.

Заявка сохраняется в таблицу `leads`. Повторное прохождение сценария тем же
пользователем обновляет его запись, а не плодит дубликаты.

## Админ-панель

`/leads` — список заявок, по 20 на страницу (`/leads 2`, `/leads 3`, …).
Алиас `/get_some_info` сохранён для совместимости со старой версией.
Не-админам команда не отвечает вовсе.

## Деплой на сервер (Ubuntu/Debian VPS)

Бот работает на long polling — белый IP, домен и HTTPS не нужны, достаточно любой
самой дешёвой VPS с исходящим доступом в интернет.

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
sudo useradd -r -m -d /opt/tgbot tgbot
sudo -u tgbot git clone <ваш-репозиторий> /opt/tgbot/app   # или scp -r локальную папку
cd /opt/tgbot/app
sudo -u tgbot python3 -m venv .venv
sudo -u tgbot .venv/bin/pip install -r requirements.txt
sudo -u tgbot cp .env.example .env && sudo -u tgbot nano .env   # вписать BOT_TOKEN и ADMIN_IDS
sudo chmod 600 .env
```

Автозапуск через systemd — `/etc/systemd/system/tgbot.service`:

```ini
[Unit]
Description=Telegram lead bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tgbot
WorkingDirectory=/opt/tgbot/app
ExecStart=/opt/tgbot/app/.venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tgbot
sudo systemctl status tgbot        # проверить, что запустился
sudo journalctl -u tgbot -f        # смотреть логи
```

Обновление после правок: `git pull && sudo systemctl restart tgbot`.

Важно: экземпляр бота с одним токеном должен быть ровно один — второй запущенный
процесс (например, локальный) вызовет ошибку `TelegramConflictError`.
Файл `bot_database.db` — это все заявки, включите его в бэкап.

## Структура

- `config.py` — конфигурация из `.env`, валидация на старте
- `database.py` — async SQLAlchemy 2.0 + aiosqlite, модель `Lead`
- `handlers.py` — FSM-сценарий и админская команда
- `bot.py` — точка входа, меню команд, корректное завершение
