# AI Dialogue Bot

Telegram-бот с AI-диалогом, персонализацией и памятью.

## Возможности

- 🤖 Диалог с ИИ (OpenAI API / совместимый API)
- 👤 Память профиля: имя, возраст, цель
- 💬 История диалога (последние 10 сообщений)
- 🔄 Многосессионная память (помнит пользователя при повторных обращениях)
- ❓ Уточняющие вопросы при недостатке данных
- 🛡 Обработка ошибок AI API с retry
- 📝 Логирование действий и ошибок

## Технологический стек

- **Python**: 3.11+
- **Telegram фреймворк**: aiogram 3.x
- **AI API**: OpenAI API (совместимый, например Agnes AI)
- **База данных**: SQLite (через aiosqlite)
- **ORM**: SQLAlchemy (async)
- **Конфигурация**: python-dotenv / pydantic-settings
- **Логирование**: logging

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone git@github.com:your-username/ai-dialogue-bot.git
   cd ai-dialogue-bot
   ```

2. Создайте виртуальное окружение и активируйте:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Скопируйте `.env.example` в `.env` и заполните:
   ```bash
   cp .env.example .env
   ```

   Обязательные переменные:
   - `BOT_TOKEN` — получите у @BotFather в Telegram
   - `OPENAI_API_KEY` — ваш ключ от OpenAI или Agnes AI
   - `OPENAI_BASE_URL` — `https://api.openai.com/v1` (OpenAI) или `https://apihub.agnes-ai.com/v1` (Agnes AI)

5. Создайте папку для БД:
   ```bash
   mkdir data
   ```

6. Запустите бота:
   ```bash
   python main.py
   ```

## Команды бота

- `/start` — начать диалог / продолжить
- `/reset` — сбросить профиль и историю
- `/help` — справка

## Структура проекта

```
ai-dialogue-bot/
├── .env.example          # Шаблон переменных окружения
├── .gitignore            # Исключения для Git
├── requirements.txt      # Зависимости
├── README.md             # Эта инструкция
├── main.py               # Точка входа
├── bot/
│   ├── config.py         # Конфигурация
│   ├── main.py           # (опционально) запуск из пакета
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py     # Модели SQLAlchemy (User, Message)
│   │   ├── session.py    # Подключение к БД, сессии
│   │   └── queries.py    # Запросы к БД
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py     # Клиент для OpenAI API
│   │   └── prompts.py    # Промпты для AI
│   ├── handlers/
│   │   └── __init__.py   # Хендлеры команд и сообщений
│   ├── middlewares/
│   │   └── __init__.py   # Middleware (если нужны)
│   └── utils/
│       ├── __init__.py
│       ├── logger.py     # Настройка логирования
│       └── keyboards.py  # Клавиатуры
```

## Переменные окружения (.env.example)

```env
# Telegram Bot Token (required)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# OpenAI API (required)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Bot settings
BOT_NAME=AI Dialogue Bot
MAX_HISTORY_MESSAGES=20
```

## Логика работы

1. **Первый запуск (/start)** — бот приветствует и спрашивает имя
2. **Получение имени** — бот запоминает имя, спрашивает возраст
3. **Получение возраста** — бот запоминает возраст, спрашивает цель
4. **Получение цели** — бот запоминает цель, предлагает задать вопрос
5. **Диалог** — бот отвечает с учётом профиля и истории (последние 10 сообщений)
6. **Повторный /start** — бот узнает пользователя по имени, продолжает диалог
7. **/reset** — полный сброс профиля и истории

## Системный промпт

```
Ты — дружелюбный AI-помощник. Твоя задача — вести диалог с пользователем, учитывая его профиль и историю общения. Отвечай кратко, по делу, но с теплотой. Если не знаешь ответа — честно скажи, что не знаешь. Не выдумывай факты. Если данных недостаточно — задай уточняющий вопрос. Подстраивай тон под пользователя: если он новичок — объясняй простыми словами, если опытный — давай больше деталей.
```

## Промпт персонализации

```
Информация о пользователе:
- Имя: {first_name}
- Возраст: {age}
- Цель: {goal}

История диалога (последние 10 сообщений):
{history}

Ответь пользователю на его последнее сообщение с учётом его профиля и контекста диалога. Будь вежливым, дружелюбным и полезным.
```

## Тестовые сценарии

1. Пользователь пишет `/start` → бот приветствует и спрашивает имя
2. Пользователь пишет имя → бот запоминает и спрашивает возраст
3. Пользователь пишет возраст → бот запоминает и спрашивает цель
4. Пользователь пишет цель → бот запоминает и предлагает задать вопрос
5. Пользователь задаёт вопрос → бот отвечает с учётом профиля
6. Пользователь пишет `/reset` → бот сбрасывает всё и прощается
7. Пользователь снова пишет `/start` → бот снова спрашивает имя (как нового пользователя)

## Деплой на VPS

1. Установите Python 3.11+, Git
2. Клонируйте репозиторий
3. Настройте `.env`
4. Установите зависимости: `pip install -r requirements.txt`
5. Запустите через systemd / supervisor / Docker

### systemd service пример

```ini
[Unit]
Description=AI Dialogue Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ai-dialogue-bot
ExecStart=/home/ubuntu/ai-dialogue-bot/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Лицензия

MIT