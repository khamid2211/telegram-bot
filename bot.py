import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(level=logging.INFO)

ASK_ELIGIBLE, ASK_CLASS, ASK_NAME, ASK_ATTENDANCE = range(4)
users_answered = set()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Yubiley 25 yil")

def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if user_id in users_answered:
        update.message.reply_text("Siz allaqachon ishtirok etgansiz.")
        return ConversationHandler.END

    reply_keyboard = [["Ha", "Yo'q"]]
    update.message.reply_text(
        "Siz 1990-2000-yillarda 63-maktabda o'qiganmisiz?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ASK_ELIGIBLE

def ask_class(update: Update, context: CallbackContext) -> int:
    if update.message.text == "Ha":
        reply_keyboard = [["A", "B", "V", "G", "D", "E"]]
        update.message.reply_text("Siz qaysi sinfda o'qigansiz?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return ASK_CLASS
    else:
        update.message.reply_text("Kechirasiz, vaqtingizni olganimiz uchun uzr so'raymiz.")
        return ConversationHandler.END

def ask_name(update: Update, context: CallbackContext) -> int:
    context.user_data["class"] = update.message.text
    update.message.reply_text("Iltimos, familiya va ismingizni kiriting:")
    return ASK_NAME

def ask_attendance(update: Update, context: CallbackContext) -> int:
    context.user_data["name"] = update.message.text
    reply_keyboard = [["Ha", "Yo'q"]]
    update.message.reply_text(
        "Siz 25 yillik yubileyga kela olasizmi?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return ASK_ATTENDANCE

def save_data(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if user_id in users_answered:
        update.message.reply_text("Siz allaqachon qatnashgansiz.")
        return ConversationHandler.END

    context.user_data["attendance"] = update.message.text
    user_class = context.user_data["class"]
    user_name = context.user_data["name"]
    attendance = context.user_data["attendance"]

    try:
        class_sheet = sheet.worksheet(user_class)
    except:
        class_sheet = sheet.add_worksheet(title=user_class, rows="100", cols="3")
        class_sheet.append_row(["Ism Familiya", "Kela oladimi?", "Telegram ID"])

    class_sheet.append_row([user_name, attendance, str(user_id)])
    users_answered.add(user_id)

    update.message.reply_text("Javobingiz uchun rahmat!")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Jarayon bekor qilindi.")
    return ConversationHandler.END

def main():
    updater = Updater("8000187155:AAEyFXN4UHdFXtHJ_QNsiYOxRiMFQxFdfC8", use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_ELIGIBLE: [MessageHandler(Filters.text & ~Filters.command, ask_class)],
            ASK_CLASS: [MessageHandler(Filters.text & ~Filters.command, ask_name)],
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_attendance)],
            ASK_ATTENDANCE: [MessageHandler(Filters.text & ~Filters.command, save_data)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
