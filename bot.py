import logging
import openpyxl
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =============================================
# ⚙️ الإعدادات
# =============================================
import os
BOT_TOKEN = os.environ.get ("8659028115:AAGAn26CbFSRgNy4eOhNjkVCJFWdo0M12zs")
EXCEL_FILE = "/home/Deanown30/جدول المعيدين.xlsx"

# =============================================
# تحميل البيانات من Excel
# =============================================
def load_data(filepath):
    members = {}
    all_slots = set()

    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active

    for row in ws.iter_rows(min_row=2, values_only=True):
        name = row[0]
        if not name:
            continue
        name = str(name).strip()
        busy_slots = set()

        for cell in row[2:]:
            if not cell:
                continue
            val = str(cell).strip()
            if not val or val == "None":
                continue
            try:
                parts = val.split(",")
                date_part = parts[0].strip()
                time_part = parts[1].strip()[:5] if len(parts) > 1 else ""
                d = datetime.strptime(date_part, "%d/%m/%Y")
                date_str = d.strftime("%Y-%m-%d")
                date_display = d.strftime("%d/%m/%Y")
                slot = (date_str, date_display, time_part)
                busy_slots.add(slot)
                all_slots.add(slot)
            except Exception:
                continue

        members[name] = busy_slots

    wb.close()
    sorted_slots = sorted(all_slots, key=lambda x: (x[0], x[2]))
    return members, sorted_slots


MEMBERS, ALL_SLOTS = load_data(EXCEL_FILE)
UNIQUE_DATES = sorted(set((s[0], s[1]) for s in ALL_SLOTS), key=lambda x: x[0])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_dates(update, context)


async def show_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"📅 {display}", callback_data=f"date:{sort_key}:{display}")]
        for sort_key, display in UNIQUE_DATES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "🎓 أهلاً بيك في بوت المراقبة!\n\n"
        "📋 هنا تقدر تعرف مين من المعيدين فاضي للمراقبة\n\n"
        "👇 اختار التاريخ:"
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        await query.message.reply_text("⚠️ انتهت صلاحية هذا الزرار، اكتب /start من جديد 😊")
        return

    _, sort_key, display = query.data.split(":", 2)
    context.user_data["date_sort"] = sort_key
    context.user_data["date_display"] = display

    times = sorted(set(s[2] for s in ALL_SLOTS if s[0] == sort_key))

    def time_label(t):
        hour = int(t.split(":")[0]) if t else 0
        if hour == 9:
            return "🌅 9:00 ص"
        elif hour == 12:
            return "☀️ 12:00 م"
        elif hour == 15:
            return "🌆 3:00 م"
        else:
            return f"🕐 {t}"

    keyboard = [
        [InlineKeyboardButton(time_label(t), callback_data=f"time:{t}")]
        for t in times
    ]
    keyboard.append([InlineKeyboardButton("🔙 رجوع للتواريخ", callback_data="back:dates")])

    await query.edit_message_text(
        f"📅 التاريخ المختار: {display}\n\n⏰ دلوقتي اختار الفترة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        await query.message.reply_text("⚠️ انتهت صلاحية هذا الزرار، اكتب /start من جديد 😊")
        return

    selected_time = query.data.split(":", 1)[1]
    date_sort = context.user_data.get("date_sort", "")
    date_display = context.user_data.get("date_display", "")

    busy_names = set()
    for name, slots in MEMBERS.items():
        for slot in slots:
            if slot[0] == date_sort and slot[2] == selected_time:
                busy_names.add(name)
                break

    available = [name for name in MEMBERS if name not in busy_names]

    hour = int(selected_time.split(":")[0]) if selected_time else 0
    if hour == 9:
        time_display = "9:00 ص"
    elif hour == 12:
        time_display = "12:00 م"
    elif hour == 15:
        time_display = "3:00 م"
    else:
        time_display = selected_time

    if available:
        names_list = "\n".join(f"✅ {name}" for name in available)
        result_text = (
            f"🗓️ {date_display}  |  ⏰ {time_display}\n"
            f"{'─' * 30}\n\n"
            f"🙋 الفاضيين للمراقبة ({len(available)} معيد):\n\n"
            f"{names_list}\n\n"
            f"{'─' * 30}\n"
            f"💡 تقدر تتواصل مع أي واحد منهم!"
        )
    else:
        result_text = (
            f"🗓️ {date_display}  |  ⏰ {time_display}\n"
            f"{'─' * 30}\n\n"
            f"😔 للأسف كل المعيدين مشغولين في هذه الفترة\n\n"
            f"🔍 جرب تاريخ أو فترة تانية!"
        )

    keyboard = [[InlineKeyboardButton("🔄 بحث جديد", callback_data="back:dates")]]
    await query.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        await query.message.reply_text("⚠️ انتهت صلاحية هذا الزرار، اكتب /start من جديد 😊")
        return
    await show_dates(update, context)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_date, pattern=r"^date:"))
    app.add_handler(CallbackQueryHandler(handle_time, pattern=r"^time:"))
    app.add_handler(CallbackQueryHandler(handle_back, pattern=r"^back:"))
    logger.info("✅ البوت شغال...")
    app.run_polling()


if __name__ == "__main__":
    main()
