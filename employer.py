# freelance_bot/employer.py
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
import random
import re
from config import CHANNEL_ID
from wallet import get_wallet_balance, decrease_wallet
from db import save_ad,get_all_keyword_users

WAITING_FOR_AD_TEXT, WAITING_FOR_CONTACT = range(2)

async def start_employer_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 *ثبت آگهی کارفرما*\n\nلطفاً توضیحات پروژه خود را وارد کنید:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_FOR_AD_TEXT


async def receive_employer_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['employer_ad'] = update.message.text.strip()
    await update.message.reply_text(
        "📎 *لطفاً آیدی تلگرام خود را وارد کنید:*\n\n"
        "برای اینکه فریلنسر بتونه با شما تماس بگیره، آیدی تلگرام خودتون رو به صورت دقیق و با فرمت `@username` وارد کنید.\n"
        "فقط آیدی رو بنویسید و از نوشتن متن اضافه خودداری کنید.",
        parse_mode="Markdown"
    )
    return WAITING_FOR_CONTACT


async def receive_employer_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.text.strip()

    if not re.fullmatch(r"^@[a-zA-Z0-9_]{5,}$", contact):
        await update.message.reply_text(
            "❌ آیدی نامعتبر است. فقط از حروف انگلیسی، اعداد و زیرخط (`_`) استفاده کنید و با `@` شروع شود.\nمثال: `@username123`",
            parse_mode="Markdown"
        )
        return WAITING_FOR_CONTACT

    ad_text = context.user_data.get("employer_ad", "بدون توضیح")
    unique_id = random.randint(1000000, 9999999)

    summary = (
        "✅ *آگهی شما با موفقیت دریافت شد.*\n\n"
        f"🆔 شناسه آگهی: {unique_id}\n"
        f"📝 توضیحات پروژه:\n{ad_text}\n\n"
        f"📞 راه ارتباطی: {contact}\n\n"
        "📣 پس از پرداخت و تایید توسط ادمین، آگهی شما منتشر خواهد شد."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 پرداخت و نهایی‌سازی", callback_data="pay_employer_ad")]
    ])

    context.bot_data[update.effective_user.id] = {
        "ad_text": ad_text,
        "custom_id": contact
    }

    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=keyboard)
    return ConversationHandler.END



from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def handle_employer_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    balance = get_wallet_balance(user_id)
    if balance >= 50000:
        success = decrease_wallet(user_id, 50000)
        if success:
            user_info = context.bot_data.get(user_id, {})
            ad_text = user_info.get("ad_text", "بدون متن")
            contact = user_info.get("custom_id", "ندارد")

            save_ad(user_id, "employer", ad_text, contact)

            # ✅ پیام آگهی
            message = (
                "#درخواست_کارفرما\n\n"
                f"{ad_text}\n\n"
                f"🆔 {contact}"
            )

            # ✳️ ساخت دکمه با لینک به ربات
            bot_username = (await context.bot.get_me()).username
            button = InlineKeyboardMarkup([[
                InlineKeyboardButton("✉️ ارتباط با کارفرما", url=f"https://t.me/{bot_username}?start=from_channel_{user_id}")
            ]])

            # 📣 ارسال به کانال همراه با دکمه
            sent_msg = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                reply_markup=button  # ← دکمه ورود به بات
            )

            # ذخیره اطلاعات آگهی به همراه reply_markup
            context.bot_data[f"ad_{user_id}"] = {
                "message_id": sent_msg.message_id,
                "channel_id": sent_msg.chat_id,
                "original_text": message,
                "reply_markup": button,  # ← اضافه کن
                "role": "employer"
            }


            # ارسال به کاربران دارای کلمات کلیدی
            from db import get_all_keyword_users
            user_keywords = get_all_keyword_users()
            text_to_check = ad_text.lower()

            for uid, keywords in user_keywords.items():
                if any(kw in text_to_check for kw in keywords):
                    try:
                        await context.bot.send_message(
                            chat_id=uid,
                            text=message
                        )
                    except Exception as e:
                        print(f"[خطا در ارسال به کاربر {uid}]: {e}")

            await query.message.edit_text("✅ پرداخت موفق. آگهی شما در کانال منتشر شد.")
        else:
            await query.message.edit_text("⚠️ مشکلی در کسر موجودی رخ داد. لطفاً دوباره تلاش کنید.")
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 کیف پول من", callback_data="back_to_wallet")]
        ])
        await query.message.edit_text(
            "❌ موجودی کیف پول شما کافی نیست. لطفاً ابتدا کیف پول خود را شارژ کنید.",
            reply_markup=keyboard
        )
