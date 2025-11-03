# Деплой бота на сервер для постоянной работы

Чтобы бот работал 24/7 без вашего компьютера, разместите его на облачном хостинге.

## Вариант 1: Railway.app (Рекомендуется - самый простой)

Railway предлагает бесплатный тариф и простой деплой через GitHub.

### Шаг 1: Создайте аккаунт на Railway

1. Перейдите на https://railway.app
2. Зарегистрируйтесь через GitHub
3. Создайте новый проект

### Шаг 2: Подготовьте проект

1. Создайте репозиторий на GitHub и загрузите туда файлы:
   - `bot.py`
   - `requirements.txt`
   - `patch_telegram.py`
   - `Checklist_Dogovora_Yulia_Shnaptseva.pdf`
   - `post_image.jpg` (если используете)
   - `.gitignore`

2. В корне проекта создайте файл `Procfile` (без расширения):
   ```
   worker: python bot.py
   ```

### Шаг 3: Деплой на Railway

1. В Railway нажмите "New Project" → "Deploy from GitHub repo"
2. Выберите ваш репозиторий
3. Railway автоматически определит Python проект

### Шаг 4: Настройте переменные окружения

В Railway перейдите в Settings → Variables и добавьте:
- `BOT_TOKEN` = `8534379995:AAFO-66CK3tOk6p-fC0FqjoFdIqm8xM759I`
- `ADMIN_IDS` = `1498469510`

### Шаг 5: Запустите

Railway автоматически запустит бота. Проверьте логи в разделе "Deployments".

---

## Вариант 2: Render.com (Бесплатный, но с ограничениями)

### Шаг 1: Создайте аккаунт

1. Перейдите на https://render.com
2. Зарегистрируйтесь через GitHub

### Шаг 2: Создайте Web Service

1. Нажмите "New +" → "Web Service"
2. Подключите ваш GitHub репозиторий
3. Настройки:
   - **Name**: `telegram-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: Free

### Шаг 3: Настройте переменные окружения

В разделе "Environment":
- `BOT_TOKEN` = `8534379995:AAFO-66CK3tOk6p-fC0FqjoFdIqm8xM759I`
- `ADMIN_IDS` = `1498469510`

### Шаг 4: Запустите

Нажмите "Create Web Service". Бот запустится автоматически.

**Примечание:** На бесплатном тарифе Render бот "засыпает" после 15 минут бездействия. Это нормально для бота, так как он реагирует на события от Telegram.

---

## Вариант 3: VPS сервер (Linux)

Если у вас есть VPS сервер (например, от Timeweb, Beget, AWS и т.д.):

### Шаг 1: Подключитесь к серверу по SSH

```bash
ssh username@your-server-ip
```

### Шаг 2: Установите Python и зависимости

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

### Шаг 3: Загрузите файлы на сервер

Скопируйте файлы на сервер:
- `bot.py`
- `requirements.txt`
- `patch_telegram.py`
- `Checklist_Dogovora_Yulia_Shnaptseva.pdf`
- `post_image.jpg` (если используете)

### Шаг 4: Создайте виртуальное окружение и установите зависимости

```bash
cd /path/to/your/bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Шаг 5: Создайте systemd сервис

Создайте файл `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/your/bot
Environment="BOT_TOKEN=8534379995:AAFO-66CK3tOk6p-fC0FqjoFdIqm8xM759I"
Environment="ADMIN_IDS=1498469510"
ExecStart=/path/to/your/bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Замените:
- `your-username` на ваше имя пользователя
- `/path/to/your/bot` на путь к папке с ботом

### Шаг 6: Запустите сервис

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### Шаг 7: Проверьте статус

```bash
sudo systemctl status telegram-bot
```

Для просмотра логов:
```bash
sudo journalctl -u telegram-bot -f
```

---

## Проверка работы

После деплоя на любую платформу:

1. Откройте бота в Telegram
2. Напишите `/start` - бот должен ответить
3. Проверьте логи на платформе/VPS

---

## Обновление бота

После изменений в коде:

- **Railway/Render**: Просто сделайте `git push` - деплой произойдет автоматически
- **VPS**: Обновите файлы на сервере и перезапустите:
  ```bash
  sudo systemctl restart telegram-bot
  ```

---

## Рекомендация

Для начинающих рекомендуется **Railway.app** - самый простой способ с минимальной настройкой.


