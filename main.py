# freelance_bot/main.py
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from db import init_db,get_user_ads
from config import TOKEN, CHANNEL_ID, YOUR_ADMIN_ID
from freelancer import start_freelancer_flow, receive_ad_text, receive_user_id, WAITING_FOR_TEXT, WAITING_FOR_ID,handle_freelancer_payment
from employer import start_employer_flow, receive_employer_ad, receive_employer_contact, WAITING_FOR_AD_TEXT, WAITING_FOR_CONTACT,handle_employer_payment
from wallet import get_wallet_balance, create_wallet_if_not_exists, decrease_wallet
import logging
import re

# Logging setup
logging.basicConfig(level=logging.INFO)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📢 ثبت آگهی"], ["🎯 پنل انجام‌دهندگان", "📂 آگهی من", "🛠 پشتیبانی"], ["💰 کیف پول من"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("سلام! لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=reply_markup)

# Handle general messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "📝 درخواست کننده":
        await start_employer_flow(update, context)
    elif text == "💼 انجام‌دهنده":
        await start_freelancer_flow(update, context)
    elif text == "📂 آگهی من":
        ads = get_user_ads(user_id)
        if not ads:
            await update.message.reply_text("📂 شما هنوز هیچ آگهی‌ای ثبت نکردید.")
        else:
            msg = "📋 لیست آگهی‌های شما:\n\n"
            for i, (role, ad_text, contact, created_at) in enumerate(ads, 1):
                role_label = "کارفرما" if role == "employer" else "انجام‌دهنده"
                msg += f"🔹 [{role_label}] {created_at}\n📝 {ad_text}\n📞 {contact}\n\n"
            await update.message.reply_text(msg)
    elif text == "📢 ثبت آگهی":
        rules_text = (
            "📋 *قوانین ثبت آگهی:*\n"
            "1. محتوای آگهی باید شفاف و محترمانه باشد.\n"
            "2. از ثبت آگهی‌های غیرواقعی خودداری کنید.\n"
            "3. ثبت آگهی به منزله پذیرش مسئولیت آن است."
        )
        keyboard = [[
            InlineKeyboardButton("✅ تایید قوانین", callback_data="accept_rules"),
            InlineKeyboardButton("↩️ برگشت", callback_data="back_to_menu")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(rules_text, parse_mode="Markdown", reply_markup=reply_markup)
        await update.message.reply_text("لطفاً قوانین را مطالعه کرده و یکی از گزینه‌ها را انتخاب کنید.", reply_markup=ReplyKeyboardRemove())

    elif text == "🎯 پنل انجام‌دهندگان":
        await update.message.reply_text("درحال بارگذاری پنل فریلنسر...")

    elif text == "🛠 پشتیبانی":
        await update.message.reply_text("با پشتیبانی در تماس باشید: @support")

    elif text == "💰 کیف پول من":
        create_wallet_if_not_exists(user_id)
        balance = get_wallet_balance(user_id)
        context.user_data["awaiting_receipt"] = True

        await update.message.reply_text(
            f"💰 *موجودی کیف پول شما:* {balance:,} تومان\n"
            "حداقل موجودی برای ثبت آگهی: ۵۰,۰۰۰ تومان\n"
            "برای شارژ کیف پول، مبلغ موردنظر را کارت‌به‌کارت کرده و رسید را برای ادمین ارسال کنید.\n"
            "💳 شماره کارت: 1234-5678-9012-3456\n"
            "🆔 ادمین: @admin\n"
            "📤 حالا لطفاً رسید پرداخت (عکس یا کد رهگیری) را همین‌جا ارسال کنید.",
            parse_mode="Markdown"
        )

    elif context.user_data.get("awaiting_receipt"):
        context.user_data["awaiting_receipt"] = False

        admin_id = YOUR_ADMIN_ID
        user = update.effective_user

        message_text = update.message.text or ""
        match = re.search(r"\d{5,}", message_text.replace(",", ""))
        amount = match.group() if match else "50000"

        await context.bot.forward_message(
            chat_id=admin_id,
            from_chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ تایید و شارژ {int(amount):,} تومان", callback_data=f"approve_payment|{user.id}|{amount}")]
        ])
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"📥 رسید پرداخت از <b>{user.full_name}</b> (@{user.username or 'ندارد'})\n🆔 آیدی عددی کاربر: <code>{user.id}</code>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        await update.message.reply_text("✅ رسید شما دریافت شد. پس از تأیید ادمین، مبلغ مربوطه به کیف پول شما اضافه خواهد شد.")
        return

# Handle inline button callbacks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "accept_rules":
        keyboard = [["📝 درخواست کننده", "💼 انجام‌دهنده"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await query.edit_message_text("✅ قوانین تایید شد. لطفاً نقش خود را انتخاب کنید:")
        await query.message.reply_text("نقش خود را انتخاب کنید:", reply_markup=reply_markup)

    elif query.data == "back_to_menu":
        keyboard = [["📢 ثبت آگهی"], ["🎯 پنل انجام‌دهندگان", "📂 آگهی من", "🛠 پشتیبانی"], ["💰 کیف پول من"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await query.edit_message_text("بازگشت به منوی اصلی.")
        await query.message.reply_text("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=reply_markup)

    elif query.data == "back_to_wallet":
        create_wallet_if_not_exists(user_id)
        balance = get_wallet_balance(user_id)
        await query.edit_message_text(
            text=f"""💰 *موجودی کیف پول شما:* {balance:,} تومان

حداقل موجودی برای ثبت آگهی: ۵۰,۰۰۰ تومان

برای شارژ کیف پول، مبلغ موردنظر را کارت‌به‌کارت کرده و رسید را برای ادمین ارسال کنید.

💳 شماره کارت: 1234-5678-9012-3456
🆔 ادمین: @admin""",
            parse_mode="Markdown"
        )

    elif query.data.startswith("approve_payment"):
        try:
            _, uid, amount = query.data.split("|")
            from wallet import increase_wallet
            increase_wallet(int(uid), int(amount))

            await context.bot.send_message(chat_id=int(uid), text=f"✅ پرداخت شما تایید شد و مبلغ {int(amount):,} تومان به کیف پول شما اضافه شد.")
            await query.edit_message_text(f"✅ مبلغ {int(amount):,} تومان با موفقیت به کیف پول کاربر اضافه شد.")
        except Exception as e:
            await query.edit_message_text("❌ خطا در پردازش تایید پرداخت.")
            print(f"[خطا در approve_payment] {e}")





async def add_amount_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != YOUR_ADMIN_ID:
            await update.message.reply_text("⛔ شما اجازه استفاده از این دستور را ندارید.")
            return

        if len(context.args) != 2:
            await update.message.reply_text("❗ فرمت صحیح:\n`/addamount user_id amount`", parse_mode="Markdown")
            return

        user_id = int(context.args[0])
        amount = int(context.args[1])

        from wallet import increase_wallet
        increase_wallet(user_id, amount)

        await update.message.reply_text(f"✅ مبلغ {amount:,} تومان با موفقیت به کیف پول کاربر {user_id} اضافه شد.")
        await context.bot.send_message(chat_id=user_id, text=f"💰 مبلغ {amount:,} تومان به کیف پول شما اضافه شد.")
    except Exception as e:
        print(f"[خطا در /addamount] {e}")
        await update.message.reply_text("❌ خطا در پردازش دستور.")







# Main function
def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    # تعریف گفت‌و‌گوهای employer و freelancer
    freelancer_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💼 انجام‌دهنده$"), start_freelancer_flow)],
        states={
            WAITING_FOR_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ad_text)],
            WAITING_FOR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_id)],
        },
        fallbacks=[]
    )
    application.add_handler(CallbackQueryHandler(handle_employer_payment, pattern="^pay_employer_ad$"))
    application.add_handler(CallbackQueryHandler(handle_freelancer_payment, pattern="^pay_freelancer_ad$"))


    employer_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 درخواست کننده$"), start_employer_flow)],
        states={
            WAITING_FOR_AD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_employer_ad)],
            WAITING_FOR_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_employer_contact)],
        },
        fallbacks=[]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(employer_conv)
    application.add_handler(freelancer_conv)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()

