import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
QUESTION_1, QUESTION_2, QUESTION_3, QUESTION_4 = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [[InlineKeyboardButton("📝 Начать заполнение", callback_data="start_application")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        config.START_MESSAGE,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало заполнения анкеты"""
    query = update.callback_query
    await query.answer()
    
    # Инициализация хранилища для ответов
    context.user_data['answers'] = []
    context.user_data['user_info'] = {
        'user_id': query.from_user.id,
        'username': query.from_user.username,
        'first_name': query.from_user.first_name,
        'last_name': query.from_user.last_name
    }
    
    # Добавляем кнопку "Отмена"
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"**🖋️ Анкета · 1/4**\n\n{config.QUESTIONS[0]}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return QUESTION_1


async def question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка первого вопроса"""
    text = update.message.text
    context.user_data['answers'].append(text)
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**🖋️ Анкета · 2/4**\n\n{config.QUESTIONS[1]}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return QUESTION_2


async def question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка второго вопроса"""
    text = update.message.text
    context.user_data['answers'].append(text)
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**🖋️ Анкета · 3/4**\n\n{config.QUESTIONS[2]}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return QUESTION_3


async def question_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка третьего вопроса"""
    text = update.message.text
    context.user_data['answers'].append(text)
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**🖋️ Анкета · 4/4**\n\n{config.QUESTIONS[3]}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return QUESTION_4


async def question_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка четвертого вопроса и отправка заявки"""
    text = update.message.text
    context.user_data['answers'].append(text)
    
    # Отправка заявки пользователю
    await update.message.reply_text(
        config.APPLICATION_SENT_MESSAGE,
        parse_mode='Markdown'
    )
    
    # Формирование сообщения для админов
    user_info = context.user_data['user_info']
    answers = context.user_data['answers']
    
    username_text = f"@{user_info['username']}" if user_info['username'] else "нет"
    full_name = f"{user_info['first_name'] or ''} {user_info['last_name'] or ''}".strip()
    
    admin_message = f"""<b>📋 НОВАЯ ЗАЯВКА</b>

<b>👤 Пользователь:</b>
├ ID: <code>{user_info['user_id']}</code>
├ Имя: {full_name}
└ Username: {username_text}

"""
    
    for i, question in enumerate(config.QUESTIONS):
        admin_message += f"<b>{question}</b>\n<blockquote>{answers[i]}</blockquote>\n\n"
    
    # Кнопки для админов
    keyboard = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user_info['user_id']}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_info['user_id']}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправка в канал логов
    try:
        await context.bot.send_message(
            chat_id=config.LOG_CHANNEL_ID,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке в канал: {e}")
    
    # Очистка данных
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена заполнения анкеты"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "**❌ Заполнение анкеты отменено.**\n\n**Используйте /start чтобы начать заново.**",
        parse_mode='Markdown'
    )
    
    context.user_data.clear()
    
    return ConversationHandler.END


async def handle_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка решения админа (принять/отклонить)"""
    query = update.callback_query
    await query.answer()
    
    # Проверка прав админа
    if query.from_user.id not in config.ADMIN_IDS:
        await query.answer("⛔ У вас нет прав для этого действия", show_alert=True)
        return
    
    # Парсинг callback_data
    action, user_id = query.data.split('_')
    user_id = int(user_id)
    
    admin_username = query.from_user.username or query.from_user.first_name
    
    if action == "accept":
        # Уведомление пользователя о принятии
        keyboard = [
            [
                InlineKeyboardButton("💬 Чат", url=config.CHAT_LINK),
                InlineKeyboardButton("📢 Канал", url=config.CHANNEL_LINK)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=config.get_accepted_message_with_curators(),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Обновление сообщения в канале
            await query.edit_message_text(
                text=query.message.text + f"\n\n✅ <b>Принято</b> | Админ: @{admin_username}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")
            await query.answer("Ошибка при отправке уведомления пользователю", show_alert=True)
    
    elif action == "reject":
        # Уведомление пользователя об отклонении
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=config.REJECTED_MESSAGE,
                parse_mode='Markdown'
            )
            
            # Обновление сообщения в канале
            await query.edit_message_text(
                text=query.message.text + f"\n\n❌ <b>Отклонено</b> | Админ: @{admin_username}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")
            await query.answer("Ошибка при отправке уведомления пользователю", show_alert=True)


def main():
    """Основная функция запуска бота"""
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в .env файле!")
        return
    
    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # ConversationHandler для анкеты
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_application, pattern="^start_application$")],
        states={
            QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_1)],
            QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_2)],
            QUESTION_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_3)],
            QUESTION_4: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_4)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
    )
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_decision, pattern="^(accept|reject)_"))
    
    # Запуск бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
