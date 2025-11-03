# bot.py

# Применяем патч для Python 3.13 ДО импорта telegram
import patch_telegram

import os
import logging
import html
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Уменьшаем уровень логирования для httpx и telegram, чтобы не видеть запросы каждые 10 секунд
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# === НАСТРОЙКИ ===

BOT_TOKEN = os.getenv("BOT_TOKEN", "8534379995:AAFO-66CK3tOk6p-fC0FqjoFdIqm8xM759I")

CHANNEL_USERNAME = "@vyhod_est_law"   # можно и числовой id канала, но username удобнее

BOT_USERNAME = "@ShnaptsevaHelper_Bot"  # username вашего бота для ссылок

PDF_PATH = "Checklist_Dogovora_Yulia_Shnaptseva.pdf"  # файл лежит рядом с bot.py

POST_IMAGE_PATH = "post_image.jpg"  # путь к изображению для поста (может быть .jpg, .png и т.д.)

# Функция для получения текста поста
def get_channel_post_text():
    """Возвращает текст поста в канал"""
    return (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я — Юлия Шнапцева, юрист-практик.\n\n"
        "Помогаю вернуть деньги и имущество, решить трудовые споры, защитить права в суде.\n\n"
        "<b>Как я работаю:</b>\n\n"
        "• разбираю ситуацию по документам (договоры, переписка, платежи) — это база;\n\n"
        "• даю план действий и варианты решений;\n\n"
        "• объясняю простыми словами, без «воды».\n\n"
        "<b>Форматы:</b> консультация, подготовка документов, проверка/составление договора, представительство в суде.\n\n"
        "──────────\n\n"
        "👉 <b>СТАРТ ЗДЕСЬ</b> — помощник выдаст чек-лист «9 пунктов перед подписанием договора» и подберёт формат работы.\n\n"
        "──────────\n\n"
        "Всё решаемо. Главное — начать с первого шага."
    )

# ID администратора (ваш Telegram ID) - узнайте через команду /myid в боте
# Можно указать несколько ID через запятую: [123456789, 987654321]
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "1498469510").split(",") if x.strip().isdigit()
]

START_TEXT = (

    "Здравствуйте! Я пришлю вам PDF-чек-лист «9 пунктов перед подписанием договора».\n\n"

    "Сначала проверю подписку на канал. Это займёт секунду."

)

NOT_SUB_TEXT = (

    "Похоже, вы пока не подписаны на канал.\n"

    "Пожалуйста, подпишитесь, затем нажмите «Проверить подписку»."

)

AFTER_SEND_TEXT = (

    "Готово! Чек-лист отправлен.\n\n"

    "Нужна быстрая проверка договора? Нажмите кнопку ниже 👇"

)

QUICK_CHECK_MESSAGE = (

    "🔍 <b>Как получить быструю проверку договора</b>\n\n"

    "Для прицельной помощи попрошу ответить на 3 вопроса и предложу формат (мини-разбор/подготовка правок):\n\n"

    "1️⃣ Какой договор (аренда/услуги/подряд/поставка/трудовой)?\n\n"

    "2️⃣ На какой стадии вы (до подписания/подписан/спор)?\n\n"

    "3️⃣ Где сейчас главное сомнение (сроки, деньги, штрафы, расторжение)?\n\n"

    "Можно просто написать ответ в одном сообщении."

)


async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:

    """

    Проверяем статус пользователя в канале.

    Важно: бот должен быть админом канала.

    """

    try:

        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)

        return member.status in ("member", "administrator", "creator")

    except Exception:

        # Если бот не админ канала или нет доступа

        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    
    # Сразу проверяем подписку при старте
    subscribed = await check_subscription(context, user_id)
    
    if subscribed:
        # Если подписан - сразу отправляем PDF
        try:
            with open(PDF_PATH, "rb") as f:
                await context.bot.send_document(
                    chat_id=user_id, 
                    document=f, 
                    filename=os.path.basename(PDF_PATH)
                )
        except FileNotFoundError:
            await update.message.reply_text(
                "Файл временно недоступен. Напишите мне, пришлю вручную: @YuliyaShn"
            )
            return
        
        # Отправляем сообщение с кнопкой "Проверка"
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Проверка", callback_data="quick_check")
        ]])
        await update.message.reply_text(AFTER_SEND_TEXT, reply_markup=kb)
    else:
        # Если не подписан - показываем кнопки
        kb = InlineKeyboardMarkup([

            [InlineKeyboardButton("Проверить подписку", callback_data="check")],

            [InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")]

        ])

        await update.message.reply_text(START_TEXT, reply_markup=kb)


async def on_check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    subscribed = await check_subscription(context, user_id)

    if subscribed:

        # Отправляем файл

        try:

            with open(PDF_PATH, "rb") as f:

                await context.bot.send_document(chat_id=user_id, document=f, filename=os.path.basename(PDF_PATH))

        except FileNotFoundError:

            await query.message.reply_text("Файл временно недоступен. Напишите мне, пришлю вручную: @YuliyaShn")

            return

        # Отправляем сообщение с кнопкой "Проверка"
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Проверка", callback_data="quick_check")
        ]])
        await query.message.reply_text(AFTER_SEND_TEXT, reply_markup=kb)

    else:

        kb = InlineKeyboardMarkup([

            [InlineKeyboardButton("Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],

            [InlineKeyboardButton("Проверить подписку", callback_data="check")]

        ])

        await query.message.reply_text(NOT_SUB_TEXT, reply_markup=kb)


async def on_quick_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Проверка'"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        QUICK_CHECK_MESSAGE,
        parse_mode="HTML"
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения своего Telegram ID"""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "нет username"
    first_name = update.message.from_user.first_name or ""
    
    # Экранируем специальные символы для Markdown
    from telegram.constants import ParseMode
    
    await update.message.reply_text(
        f"👤 Ваш Telegram ID: <code>{user_id}</code>\n\n"
        f"Имя: {first_name}\n"
        f"Username: @{username}\n\n"
        f"📋 Скопируйте ID и добавьте его в переменную ADMIN_IDS в файле bot.py",
        parse_mode=ParseMode.HTML
    )
    
    logger.info(f"User {username} (ID: {user_id}) requested their ID")


# Хранилище ожидающих ответа (user_id -> admin_id)
pending_replies = {}

# Хранилище для создания постов (user_id -> {'text': None, 'photo': None})
pending_posts = {}


async def handle_reply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Ответить'"""
    query = update.callback_query
    await query.answer()
    
    admin_id = query.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if ADMIN_IDS and admin_id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    # Извлекаем user_id из callback_data (формат: reply_123456789)
    try:
        user_id = int(query.data.split("_")[1])
        pending_replies[admin_id] = user_id
        
        # Получаем информацию о пользователе для отображения
        try:
            chat = await context.bot.get_chat(user_id)
            user_info = f"{chat.first_name or ''} (@{chat.username or 'без username'})"
        except:
            user_info = f"ID: {user_id}"
        
        await query.message.reply_text(
            f"✍️ <b>Режим ответа включен</b>\n\n"
            f"Отвечаете пользователю: {user_info}\n\n"
            f"Просто напишите текст ответа, и он будет отправлен пользователю.\n"
            f"Для отмены используйте /cancel",
            parse_mode="HTML"
        )
    except (ValueError, IndexError):
        await query.message.reply_text("❌ Ошибка: неверный формат данных.")


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений от администратора (ответы пользователям и создание постов)"""
    admin_id = update.message.from_user.id
    
    # Проверяем, создается ли пост
    if admin_id in pending_posts:
        await handle_post_creation(update, context)
        return
    
    # Проверяем, ожидается ли ответ от этого администратора
    if admin_id in pending_replies:
        target_user_id = pending_replies[admin_id]
        reply_text = update.message.text
        
        try:
            # Отправляем ответ пользователю
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💬 <b>Ответ от специалиста:</b>\n\n{reply_text}",
                parse_mode="HTML"
            )
            
            # Уведомляем администратора об успешной отправке
            await update.message.reply_text(
                "✅ Ответ успешно отправлен пользователю!"
            )
            
            # Удаляем из ожидающих ответа
            del pending_replies[admin_id]
            
            logger.info(f"Admin {admin_id} replied to user {target_user_id}")
        except Exception as e:
            await update.message.reply_text(
                f"❌ Ошибка отправки: {e}\n"
                f"Пользователь, возможно, заблокировал бота или удалил аккаунт."
            )
            del pending_replies[admin_id]


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для отмены режима ответа или создания поста"""
    admin_id = update.message.from_user.id
    
    cancelled = False
    
    if admin_id in pending_replies:
        del pending_replies[admin_id]
        cancelled = True
    
    if admin_id in pending_posts:
        del pending_posts[admin_id]
        cancelled = True
    
    if cancelled:
        await update.message.reply_text("❌ Операция отменена.")
    else:
        await update.message.reply_text("ℹ️ Нет активных операций для отмены.")


async def publish_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для публикации поста в канал (только для администраторов)"""
    user_id = update.message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not ADMIN_IDS or user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    # Запускаем режим создания поста
    pending_posts[user_id] = {'text': None, 'photo': None}
    
    await update.message.reply_text(
        "📝 <b>Создание нового поста</b>\n\n"
        "1️⃣ Отправьте мне текст поста (выделяйте жирный, курсив прямо в Telegram)\n\n"
        "2️⃣ Затем отправьте фото для поста\n\n"
        "После получения текста и фото пост будет автоматически опубликован в канале.\n\n"
        "Для отмены используйте /cancel",
        parse_mode="HTML"
    )


async def handle_post_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текста и фото для создания поста"""
    user_id = update.message.from_user.id
    
    # Проверяем, находится ли пользователь в режиме создания поста
    if user_id not in pending_posts:
        return
    
    # Функция для конвертации текста с entities в HTML
    def convert_text_to_html(msg):
        text = msg.text_html if hasattr(msg, 'text_html') else msg.text
        
        if not hasattr(msg, 'text_html') or text == msg.text:
            entities = msg.entities or []
            text = msg.text
            if entities:
                result_parts = []
                last_offset = 0
                for entity in sorted(entities, key=lambda e: e.offset):
                    if entity.offset > last_offset:
                        result_parts.append(html.escape(text[last_offset:entity.offset]))
                    
                    entity_text = text[entity.offset:entity.offset + entity.length]
                    escaped_text = html.escape(entity_text)
                    
                    if entity.type == "bold":
                        formatted_text = f"<b>{escaped_text}</b>"
                    elif entity.type == "italic":
                        formatted_text = f"<i>{escaped_text}</i>"
                    elif entity.type == "code":
                        formatted_text = f"<code>{escaped_text}</code>"
                    elif entity.type == "pre":
                        formatted_text = f"<pre>{escaped_text}</pre>"
                    elif entity.type == "text_link":
                        formatted_text = f'<a href="{entity.url}">{escaped_text}</a>'
                    elif entity.type == "underline":
                        formatted_text = f"<u>{escaped_text}</u>"
                    elif entity.type == "strikethrough":
                        formatted_text = f"<s>{escaped_text}</s>"
                    else:
                        formatted_text = escaped_text
                    
                    result_parts.append(formatted_text)
                    last_offset = entity.offset + entity.length
                
                if last_offset < len(text):
                    result_parts.append(html.escape(text[last_offset:]))
                
                text = ''.join(result_parts)
        return text
    
    # Если это фото
    if update.message.photo:
        photo = update.message.photo[-1]  # Берем фото наибольшего размера
        
        # Сохраняем ID фото
        pending_posts[user_id]['photo'] = photo.file_id
        
        await update.message.reply_text(
            "✅ Фото получено!\n\n"
            "Ожидаю текст поста..."
        )
        
        # Если есть и текст, и фото - публикуем
        if pending_posts[user_id]['text']:
            await publish_ready_post(update, context, user_id)
    
    # Если это текст
    elif update.message.text:
        text = convert_text_to_html(update.message)
        
        # Сохраняем текст с форматированием
        pending_posts[user_id]['text'] = text
        
        await update.message.reply_text(
            "✅ Текст получен!\n\n"
            "Отправьте фото для поста..."
        )
        
        # Если есть и текст, и фото - публикуем
        if pending_posts[user_id]['photo']:
            await publish_ready_post(update, context, user_id)


async def publish_ready_post(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Публикует готовый пост в канал"""
    try:
        post_data = pending_posts[user_id]
        post_text = post_data['text']
        photo_id = post_data['photo']
        
        # Убеждаемся, что текст не пустой
        if not post_text:
            await update.message.reply_text("❌ Ошибка: текст поста пуст!")
            return
        
        # Создаем кнопку со ссылкой на бота
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "👉 СТАРТ ЗДЕСЬ",
                url=f"https://t.me/{BOT_USERNAME.lstrip('@')}?start=checklist"
            )
        ]])
        
        # Импортируем ParseMode для явного указания
        from telegram.constants import ParseMode
        
        # Отправляем пост в канал
        if photo_id:
            # Всегда пытаемся отправить фото с текстом и кнопкой в одном сообщении
            try:
                message = await context.bot.send_photo(
                    chat_id=CHANNEL_USERNAME,
                    photo=photo_id,
                    caption=post_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            except Exception as e:
                # Если получили ошибку о длине caption, отправляем раздельно
                error_str = str(e).lower()
                if "caption" in error_str and ("too long" in error_str or "too long" in error_str):
                    # Отправляем фото отдельно, затем текст с кнопкой
                    await context.bot.send_photo(
                        chat_id=CHANNEL_USERNAME,
                        photo=photo_id
                    )
                    message = await context.bot.send_message(
                        chat_id=CHANNEL_USERNAME,
                        text=post_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb
                    )
                else:
                    # Другая ошибка - пробрасываем дальше
                    raise
        else:
            # Отправляем только текст с кнопкой
            message = await context.bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=post_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
        
        # Закрепляем сообщение
        try:
            await context.bot.pin_chat_message(
                chat_id=CHANNEL_USERNAME,
                message_id=message.message_id,
                disable_notification=False
            )
            await update.message.reply_text(
                f"✅ Пост успешно опубликован и закреплён в канале {CHANNEL_USERNAME}!"
            )
        except Exception as pin_error:
            await update.message.reply_text(
                f"✅ Пост успешно опубликован в канале {CHANNEL_USERNAME}!\n"
                f"⚠️ Не удалось закрепить сообщение. Возможно, у бота нет прав на закрепление.\n"
                f"Закрепите его вручную в канале."
            )
            logger.warning(f"Не удалось закрепить сообщение: {pin_error}")
        
        # Удаляем из ожидающих
        del pending_posts[user_id]
        
        logger.info(f"Admin {user_id} published post to channel {CHANNEL_USERNAME}")
        
    except Exception as e:
        error_msg = f"❌ Ошибка публикации поста: {e}\n\n"
        error_msg += f"Убедитесь, что:\n"
        error_msg += f"• Бот является администратором канала {CHANNEL_USERNAME}\n"
        error_msg += f"• У бота есть права на публикацию сообщений\n"
        error_msg += f"• Канал существует и доступен"
        
        await update.message.reply_text(error_msg)
        logger.error(f"Ошибка публикации поста: {e}")
        
        # Удаляем из ожидающих при ошибке
        if user_id in pending_posts:
            del pending_posts[user_id]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений от пользователей"""
    
    user = update.message.from_user
    user_id = user.id
    
    # Пропускаем сообщения от администраторов (они обрабатываются отдельно)
    if ADMIN_IDS and user_id in ADMIN_IDS:
        # Если администратор не в режиме ответа, его сообщения игнорируются
        return
    
    message_text = update.message.text
    username = user.username or f"ID_{user_id}"
    first_name = user.first_name or ""
    
    # Логируем сообщение в консоль
    log_message = f"\n{'='*50}\n"
    log_message += f"📩 НОВОЕ СООБЩЕНИЕ\n"
    log_message += f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    log_message += f"От: {first_name} (@{username}) [ID: {user_id}]\n"
    log_message += f"Текст: {message_text}\n"
    log_message += f"{'='*50}\n"
    
    print(log_message)
    logger.info(f"Message from {username} (ID: {user_id}): {message_text}")
    
    # Сохраняем в файл (опционально, для истории)
    try:
        with open("messages_log.txt", "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception as e:
        logger.error(f"Ошибка записи в лог: {e}")
    
    # Формируем сообщение для администратора
    admin_message = (
        f"📩 <b>Новое сообщение от пользователя</b>\n\n"
        f"👤 <b>От:</b> {first_name} (@{username})\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        f"💬 <b>Сообщение:</b>\n{message_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    # Отправляем сообщение всем администраторам
    sent_to_admins = False
    if ADMIN_IDS:
        for admin_id in ADMIN_IDS:
            try:
                # Кнопка для быстрого ответа
                reply_kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        f"💬 Ответить пользователю",
                        callback_data=f"reply_{user_id}"
                    )
                ]])
                
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    parse_mode="HTML",
                    reply_markup=reply_kb
                )
                sent_to_admins = True
                logger.info(f"Message forwarded to admin {admin_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки администратору {admin_id}: {e}")
                print(f"⚠️ Не удалось отправить сообщение администратору {admin_id}. "
                      f"Убедитесь, что бот может отправлять вам сообщения (напишите боту /start)")
    else:
        print("⚠️ ADMIN_IDS не настроен! Сообщения не будут пересылаться в личку.")
        print("   Используйте команду /myid в боте, чтобы узнать свой ID, и добавьте его в ADMIN_IDS")
    
    # Отправляем подтверждение пользователю
    await update.message.reply_text(
        "✅ Спасибо за ответ! Я получил ваше сообщение и свяжусь с вами в ближайшее время.\n\n"
        "Если у вас срочный вопрос, напишите мне напрямую: @YuliyaShn"
    )


def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))  # Команда для получения своего ID
    app.add_handler(CommandHandler("cancel", cancel))  # Отмена режима ответа
    app.add_handler(CommandHandler("publish", publish_post))  # Публикация поста в канал
    app.add_handler(CallbackQueryHandler(on_check, pattern="^check$"))
    app.add_handler(CallbackQueryHandler(on_quick_check, pattern="^quick_check$"))
    app.add_handler(CallbackQueryHandler(handle_reply_callback, pattern="^reply_"))
    
    # Обработчик сообщений от администраторов (для ответов и создания постов)
    # Обрабатывает только если администратор в режиме ответа или создания поста
    if ADMIN_IDS:
        admin_filter = filters.User(ADMIN_IDS)
        # Обработчик текста и фото от администраторов
        app.add_handler(MessageHandler(
            (filters.TEXT | filters.PHOTO) & ~filters.COMMAND & admin_filter,
            handle_admin_message
        ))
    
    # Обработчик текстовых сообщений от обычных пользователей (должен быть последним)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("\n" + "="*50)
    print("🤖 Бот запущен и готов к работе!")
    print("="*50)
    print("Все сообщения от пользователей будут выводиться в консоль.")
    print("Также сохраняются в файл messages_log.txt")
    if ADMIN_IDS:
        print(f"📩 Сообщения будут пересылаться администраторам: {ADMIN_IDS}")
    else:
        print("⚠️ ADMIN_IDS не настроен! Используйте /myid в боте для получения ID")
    print("="*50 + "\n")

    # Запускаем бота (синхронная версия для совместимости)
    app.run_polling(allowed_updates=None, drop_pending_updates=True, stop_signals=None)


if __name__ == "__main__":
    main()

