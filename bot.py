import json
import os
import re
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

import config

# ========== СОСТОЯНИЯ ==========
(
    NAME, CONFIRM_NAME, SERVICE, ADDRESS, PORCH, FLOOR, APARTMENT,
    WHAT_WASH, WASH_COUNT, WASH_AGAIN, PHONE, CONFIRM_APPLICATION,
    OTHER_TZ, OTHER_NAME, OTHER_CONFIRM_NAME, OTHER_PHONE, OTHER_CONFIRM
) = range(17)

# ========== КНОПКИ ==========
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🚀 Оставить заявку")],
        [KeyboardButton("ℹ️ О компании"), KeyboardButton("📋 Наши услуги")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("⭐ Оставить отзыв")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_yes_no_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")]], resize_keyboard=True)

def get_service_keyboard():
    keyboard = [
        [KeyboardButton("🏠 Частная мойка")],
        [KeyboardButton("👥 Выборочная (с соседями)")],
        [KeyboardButton("🔧 Другие работы")],
        [KeyboardButton("◀️ Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_wash_type_keyboard():
    keyboard = [[KeyboardButton("🪟 Окно"), KeyboardButton("🏠 Балкон")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_wash_again_keyboard():
    keyboard = [
        [KeyboardButton("🪟 Окно"), KeyboardButton("🏠 Балкон")],
        [KeyboardButton("❌ Нет, всё")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== СОХРАНЕНИЕ ЗАЯВКИ ==========
def save_application(user_data):
    app = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_data.get("user_id"),
        "username": user_data.get("username"),
        "name": user_data.get("name"),
        "service": user_data.get("service"),
        "address": user_data.get("address", ""),
        "porch": user_data.get("porch", ""),
        "floor": user_data.get("floor", ""),
        "apartment": user_data.get("apartment", ""),
        "items": user_data.get("items", []),
        "phone": user_data.get("phone"),
        "tz": user_data.get("tz", "")
    }
    if os.path.exists(config.DATABASE_FILE):
        with open(config.DATABASE_FILE, 'r', encoding='utf-8') as f:
            apps = json.load(f)
    else:
        apps = []
    apps.append(app)
    with open(config.DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(apps, f, ensure_ascii=False, indent=2)
    return app

def format_for_admin(app):
    text = f"""
📋 *НОВАЯ ЗАЯВКА!* 🔔

━━━━━━━━━━━━━━━━━━━━
🕐 *Время:* {app['timestamp']}
👤 *Имя:* {app['name']}
📱 *Телефон:* `{app['phone']}`
🏷️ *Услуга:* {app['service']}
━━━━━━━━━━━━━━━━━━━━
"""
    if app.get('address'):
        text += f"📍 *Адрес:* {app['address']}\n"
    if app.get('porch'):
        text += f"🚪 *Подъезд:* {app['porch']}\n"
    if app.get('floor'):
        text += f"🏢 *Этаж:* {app['floor']}\n"
    if app.get('apartment'):
        text += f"🏠 *Квартира:* {app['apartment']}\n"
    if app.get('items'):
        text += f"\n🧼 *Что моем:*\n"
        for item in app['items']:
            text += f"   • {item['type']}: {item['count']} створок\n"
    if app.get('tz'):
        text += f"\n📝 *ТЗ:*\n{app['tz']}\n"
    
    text += f"\n🆔 *ID:* `{app['user_id']}`"
    if app.get('username'):
        text += f"\n📢 *Username:* @{app['username']}"
    text += "\n━━━━━━━━━━━━━━━━━━━━"
    return text

# ========== ОБРАБОТЧИКИ ==========
async def start(update, context):
    context.user_data.clear()
    await update.message.reply_text(
        "✨ *Добро пожаловать в Pureza!* ✨\n\n"
        "🧼 *Профессиональная мойка окон*\n"
        "🚀 *Быстро | Качественно | Недорого*\n\n"
        "Нажмите кнопку ниже, чтобы оставить заявку",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def about_company(update, context):
    photo_path = "/Users/user/my_bot/photo.jpg"
    text = """
👋 *Меня зовут Сергей*

Работаю промышленным альпинистом более 5 лет и профессионально занимаюсь:
• 🪟 Мойкой остекления
• 🔧 Монтажом
• 🎨 Покраской
• И многим другим

📜 Имею необходимые документы, допуски, а так же инструмент и инвентарь.

📍 Работаю в *Питере и Л.О.*

📞 *Обращайтесь, с радостью отвечу на все ваши вопросы!*
"""
    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def handle_menu(update, context):
    text = update.message.text
    
    if text == "ℹ️ О компании":
        await about_company(update, context)
        return ConversationHandler.END
        
    elif text == "📋 Наши услуги":
        await update.message.reply_text(
            "🔧 *Наши услуги*\n\nВыберите нужный вариант 👇",
            parse_mode="Markdown",
            reply_markup=get_service_keyboard()
        )
        return ConversationHandler.END
        
    elif text == "📞 Контакты":
        contacts_text = """
📞 *Наши контакты*

📱 *Телефон:* +7 (999) 669-28-02

💬 *Telegram:* [@sergeizorkiyy](https://t.me/sergeizorkiyy)

По любым вопросам обращайтесь! 🧼
"""
        await update.message.reply_text(contacts_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    elif text == "⭐ Оставить отзыв":
        review_text = """
📝 *ПОДРОБНЫЙ ГАЙД: Как оставить отзыв на Авито*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 *Почему Авито блокирует отзывы?*

Авито проверяет:
• Поведение пользователя
• Историю аккаунта
• Текст отзыва
• Время написания

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠 *ПОШАГОВАЯ ИНСТРУКЦИЯ:*

*ШАГ 1. Подготовьте аккаунт*
✅ Подтверждённый номер телефона

*ШАГ 2. Создайте историю переписки*
✅ Найдите объявление через поиск (номер `8069451225`)
✅ Напишите в чат Авито 3-5 сообщений

*ШАГ 3. Выдержите паузу*
✅ Подождите 1–3 дня после сделки

*ШАГ 4. Напишите «живой» текст*
✅ Конкретные детали, без шаблонов

*ШАГ 5. Добавьте фото*
✅ Реальное фото увеличивает шансы

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *ЧЕГО НЕЛЬЗЯ ДЕЛАТЬ:*
❌ Прямые ссылки на отзыв
❌ Копировать одинаковый текст
❌ Писать «Скину деньги за отзыв»
❌ Использовать VPN с продавцом

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 *НОМЕР ОБЪЯВЛЕНИЯ:* `8069451225`

💬 *Telegram:* @sergeizorkiyy

Спасибо за доверие! 🙏
"""
        await update.message.reply_text(review_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    elif text == "◀️ Главное меню":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    elif text == "🚀 Оставить заявку":
        await start_app(update, context)
        return NAME
        
    elif text in ["🏠 Частная мойка", "👥 Выборочная (с соседями)"]:
        context.user_data['service'] = text
        await update.message.reply_text("📍 *Укажите адрес* (город, улица, дом):", parse_mode="Markdown")
        return ADDRESS
        
    elif text == "🔧 Другие работы":
        await update.message.reply_text(
            "📝 *Другие работы*\n\nРасскажите, что нужно сделать? Опишите задачу (до 500 символов):",
            parse_mode="Markdown"
        )
        return OTHER_TZ
        
    else:
        await update.message.reply_text(
            "❓ *Не понимаю команду*\n\nИспользуйте кнопки меню 👇",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

async def start_app(update, context):
    await update.message.reply_text(
        "📝 *Давайте познакомимся!* 🤝\n\nКак я могу к вам обращаться?\n\n✏️ *Напишите ваше имя:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
    )
    return NAME

async def get_name(update, context):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ *Некорректное имя*\n\nПопробуйте еще раз:", parse_mode="Markdown")
        return NAME
    context.user_data['name'] = name
    context.user_data['user_id'] = update.effective_user.id
    context.user_data['username'] = update.effective_user.username
    await update.message.reply_text(
        f"👤 *Ваше имя:* {name}\n\n✅ *Всё верно?*",
        parse_mode="Markdown",
        reply_markup=get_yes_no_keyboard()
    )
    return CONFIRM_NAME

async def confirm_name(update, context):
    if update.message.text == "✅ Да":
        await update.message.reply_text("🏢 *Выберите тип услуги:*", parse_mode="Markdown", reply_markup=get_service_keyboard())
        return SERVICE
    else:
        await update.message.reply_text("✏️ *Напишите ваше имя заново:*", parse_mode="Markdown")
        return NAME

async def get_address(update, context):
    context.user_data['address'] = update.message.text.strip()
    await update.message.reply_text("🚪 *Введите номер подъезда:*", parse_mode="Markdown")
    return PORCH

async def get_porch(update, context):
    context.user_data['porch'] = update.message.text.strip()
    await update.message.reply_text("🏢 *Введите этаж:*", parse_mode="Markdown")
    return FLOOR

async def get_floor(update, context):
    context.user_data['floor'] = update.message.text.strip()
    await update.message.reply_text("🏠 *Введите номер квартиры:*", parse_mode="Markdown")
    return APARTMENT

async def get_apartment(update, context):
    context.user_data['apartment'] = update.message.text.strip()
    context.user_data['items'] = []
    await update.message.reply_text("🧼 *Что будем мыть?*", parse_mode="Markdown", reply_markup=get_wash_type_keyboard())
    return WHAT_WASH

async def get_wash_type(update, context):
    wash_type = update.message.text
    context.user_data['current_wash_type'] = wash_type
    await update.message.reply_text(
        f"🔢 *Сколько створок в {wash_type}?*\n\nВведите число:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
    )
    return WASH_COUNT

async def get_wash_count(update, context):
    try:
        count = int(update.message.text.strip())
        if count < 1 or count > 50:
            raise ValueError
    except:
        await update.message.reply_text("❌ *Введите корректное число (от 1 до 50):*", parse_mode="Markdown")
        return WASH_COUNT
    
    context.user_data['items'].append({
        "type": context.user_data['current_wash_type'],
        "count": count
    })
    
    items_text = "\n".join([f"• {i['type']}: {i['count']} створок" for i in context.user_data['items']])
    await update.message.reply_text(
        f"✅ *Добавлено!*\n\n📋 *Текущий список:*\n{items_text}\n\n🔄 *Будем мыть еще что-то?*",
        parse_mode="Markdown",
        reply_markup=get_wash_again_keyboard()
    )
    return WASH_AGAIN

async def get_wash_again(update, context):
    if update.message.text == "❌ Нет, всё":
        await update.message.reply_text(
            "📱 *Укажите номер телефона* ☎️\n\nПример: `+7 999 123-45-67`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
        )
        return PHONE
    else:
        wash_type = update.message.text
        context.user_data['current_wash_type'] = wash_type
        await update.message.reply_text(
            f"🔢 *Сколько створок в {wash_type}?*\n\nВведите число:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
        )
        return WASH_COUNT

async def get_phone(update, context):
    phone = update.message.text.strip()
    context.user_data['phone'] = phone
    
    items_text = "\n".join([f"• {i['type']}: {i['count']} створок" for i in context.user_data.get('items', [])])
    
    # Формируем текст для подтверждения
    summary_text = f"""📋 *Проверьте заявку:*

👤 *Имя:* {context.user_data['name']}
📍 *Адрес:* {context.user_data.get('address', '')}
🚪 *Подъезд:* {context.user_data.get('porch', '')}
🏢 *Этаж:* {context.user_data.get('floor', '')}
🏠 *Квартира:* {context.user_data.get('apartment', '')}
🧼 *Что моем:*
{items_text}
📱 *Телефон:* {phone}

✅ *Всё верно?*"""
    
    await update.message.reply_text(
        summary_text,
        parse_mode="Markdown",
        reply_markup=get_yes_no_keyboard()
    )
    return CONFIRM_APPLICATION

async def confirm_application(update, context):
    if update.message.text == "✅ Да":
        app = save_application(context.user_data)
        await update.message.reply_text(
            "🎉 *Спасибо за доверие!* 🎉\n\n"
            "Ваша заявка принята! 📋\n\n"
            "Наш менеджер свяжется с вами в ближайшее время.\n\n"
            "*Pureza — чистота, которой доверяют* 🧼✨",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        try:
            await context.bot.send_message(chat_id=config.ADMIN_ID, text=format_for_admin(app), parse_mode="Markdown")
        except Exception as e:
            print("Ошибка отправки админу:", e)
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ *Заявка отменена*\n\nВозвращаемся в главное меню:", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return ConversationHandler.END

# ========== ДРУГИЕ РАБОТЫ ==========
async def other_get_tz(update, context):
    tz = update.message.text.strip()
    if len(tz) < 5 or len(tz) > 500:
        await update.message.reply_text("❌ *Текст должен быть от 5 до 500 символов*\n\nПопробуйте еще раз:", parse_mode="Markdown")
        return OTHER_TZ
    context.user_data['tz'] = tz
    await update.message.reply_text("📝 *Представьтесь*\n\nНапишите ваше имя:", parse_mode="Markdown")
    return OTHER_NAME

async def other_get_name(update, context):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ *Некорректное имя*\n\nПопробуйте еще раз:", parse_mode="Markdown")
        return OTHER_NAME
    context.user_data['name'] = name
    context.user_data['user_id'] = update.effective_user.id
    context.user_data['username'] = update.effective_user.username
    await update.message.reply_text(
        f"👤 *Ваше имя:* {name}\n\n✅ *Всё верно?*",
        parse_mode="Markdown",
        reply_markup=get_yes_no_keyboard()
    )
    return OTHER_CONFIRM_NAME

async def other_confirm_name(update, context):
    if update.message.text == "✅ Да":
        await update.message.reply_text(
            "📱 *Укажите номер телефона* ☎️",
            parse_mode="Markdown"
        )
        return OTHER_PHONE
    else:
        await update.message.reply_text("✏️ *Напишите ваше имя заново:*", parse_mode="Markdown")
        return OTHER_NAME

async def other_get_phone(update, context):
    phone = update.message.text.strip()
    context.user_data['phone'] = phone
    context.user_data['service'] = "Другие работы"
    
    summary = f"""
📋 *Проверьте заявку:*

👤 *Имя:* {context.user_data['name']}
📝 *Описание задачи:* {context.user_data['tz']}
📱 *Телефон:* `{phone}`

✅ *Всё верно?*
"""
    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=get_yes_no_keyboard())
    return OTHER_CONFIRM

async def other_confirm(update, context):
    if update.message.text == "✅ Да":
        app = save_application(context.user_data)
        await update.message.reply_text(
            "🎉 *Спасибо за доверие!* 🎉\n\n"
            "Ваша заявка принята! 📋\n\n"
            "Наш менеджер свяжется с вами в ближайшее время.\n\n"
            "*Pureza — чистота, которой доверяют* 🧼✨",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        try:
            await context.bot.send_message(chat_id=config.ADMIN_ID, text=format_for_admin(app), parse_mode="Markdown")
        except Exception as e:
            print("Ошибка отправки админу:", e)
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ *Заявка отменена*\n\nВозвращаемся в главное меню:", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("❌ *Действие отменено*\n\nВозвращаемся в главное меню:", parse_mode="Markdown", reply_markup=get_main_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

async def get_apps(update, context):
    if update.effective_user.id != config.ADMIN_ID:
        await update.message.reply_text("⛔ *Доступ запрещен*", parse_mode="Markdown")
        return
    if not os.path.exists(config.DATABASE_FILE):
        await update.message.reply_text("📭 *Заявок пока нет*", parse_mode="Markdown")
        return
    with open(config.DATABASE_FILE, 'r', encoding='utf-8') as f:
        apps = json.load(f)
    if not apps:
        await update.message.reply_text("📭 *Заявок пока нет*", parse_mode="Markdown")
        return
    text = f"📊 *СТАТИСТИКА ЗАЯВОК*\n━━━━━━━━━━━━━━━━━━━━\n📋 *Всего:* {len(apps)}\n\n"
    for app in apps[-5:]:
        text += f"🕐 {app['timestamp']}\n👤 {app['name']} | 📱 `{app['phone']}`\n🏷️ {app['service']}\n━━━━━━━━━━━━━━━━━━━━\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== ЗАПУСК ==========
def main():
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🚀 Оставить заявку$"), start_app),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CONFIRM_NAME: [MessageHandler(filters.Regex("^(✅ Да|❌ Нет)$"), confirm_name)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            PORCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_porch)],
            FLOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_floor)],
            APARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_apartment)],
            WHAT_WASH: [MessageHandler(filters.Regex("^(🪟 Окно|🏠 Балкон)$"), get_wash_type)],
            WASH_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wash_count)],
            WASH_AGAIN: [MessageHandler(filters.Regex("^(🪟 Окно|🏠 Балкон|❌ Нет, всё)$"), get_wash_again)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CONFIRM_APPLICATION: [MessageHandler(filters.Regex("^(✅ Да|❌ Нет)$"), confirm_application)],
            OTHER_TZ: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_get_tz)],
            OTHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_get_name)],
            OTHER_CONFIRM_NAME: [MessageHandler(filters.Regex("^(✅ Да|❌ Нет)$"), other_confirm_name)],
            OTHER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_get_phone)],
            OTHER_CONFIRM: [MessageHandler(filters.Regex("^(✅ Да|❌ Нет)$"), other_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start), MessageHandler(filters.Regex("^◀️ Главное меню$"), cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("apps", get_apps))
    
    print("🤖 Бот Pureza запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()