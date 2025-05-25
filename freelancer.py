# freelance_bot/freelancer.py
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
import re
import random
from db import save_ad
from config import CHANNEL_ID
from wallet import get_wallet_balance, decrease_wallet
# States
WAITING_FOR_TEXT, WAITING_FOR_ID = range(2)

async def start_freelancer_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💼 *ورود به پنل انجام‌دهنده*\n\n"
        "📝 *لطفاً متن آگهی خود را وارد کنید:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_FOR_TEXT

async def receive_ad_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad_text'] = update.message.text.strip()
    await update.message.reply_text(
        "📎 *لطفاً آیدی تلگرام خود را وارد کنید:*\n\n"
        "برای اینکه کارفرما بتونه با شما تماس بگیره، آیدی تلگرام خودتون رو به صورت دقیق و با فرمت `@username` ارسال کنید.\n"
        "لطفاً فقط آیدی رو بنویسید و از نوشتن متن اضافه خودداری کنید.",
        parse_mode="Markdown"
    )
    return WAITING_FOR_ID

async def receive_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if re.fullmatch(r"@\w{5,}", text):
        ad_text = context.user_data.get('ad_text', 'بدون متن')

        # ذخیره نهایی آگهی در bot_data برای استفاده در مرحله پرداخت
        context.bot_data[update.effective_user.id] = {
            "ad_text": ad_text,
            "custom_id": text
        }

        unique_id = random.randint(1000000, 9999999)
        cost = "50,000"
        message = (
            "☑️ *جزئیات ثبت آگهی شما با موفقیت ایجاد شد.*\n\n"
            f"🪧 شناسه یکتا آگهی : {unique_id}\n"
            f"💵 هزینه ثبت آگهی : {cost} تومان\n"
            f"📝 پیشنمایش آگهی :\n\n{ad_text}\n\n"
            f"🆔 {text}\n"
            "_-_-_-_-_-_-_-_-_-_-_-_\n\n"
            "📣 آگهی پس از پرداخت شما و تایید ادمین به صورت آنی در کانال منتشر می‌شود."
        )

        keyboard = [[InlineKeyboardButton("💳 پرداخت و ثبت نهایی آگهی", callback_data="pay_freelancer_ad")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ دستور نامعتبر. لطفاً آیدی خود را با فرمت @username وارد کنید.")
        return WAITING_FOR_ID


async def handle_freelancer_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    balance = get_wallet_balance(user_id)
    if balance >= 50000:
        if decrease_wallet(user_id, 50000):
            user_info = context.bot_data.get(user_id, {})
            ad_text = user_info.get("ad_text", "بدون متن")
            custom_id = user_info.get("custom_id", "❌ آیدی وارد نشده")

            save_ad(user_id, "freelancer", ad_text, custom_id)

            message = f"#انجام_دهنده\n\n{ad_text}\n\n🆔 {custom_id}"
            await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
            await query.edit_message_text("✅ پرداخت انجام شد. آگهی شما منتشر شد.")
        else:
            await query.edit_message_text("❌ خطا در کسر موجودی. لطفاً دوباره تلاش کنید.")
    else:
        await query.edit_message_text(
            "❌ موجودی شما کافی نیست. لطفاً ابتدا کیف پول را شارژ کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 کیف پول من", callback_data="back_to_wallet")]
            ])
        )