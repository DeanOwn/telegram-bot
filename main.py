from keep_alive import keep_alive  # لتشغيل السيرفر على Replit
import re
import pandas as pd
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler

# تشغيل السيرفر المصغر لخداع Replit
keep_alive()

# دالة لتطبيع النصوص
def normalize_arabic(text):
    text = str(text)
    text = text.strip()

    # توحيد الحروف
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه")
    text = text.replace("ى", "ي")
    text = text.replace("ؤ", "و").replace("ئ", "ي")

    # توحيد الأرقام العربية والإنجليزية
    text = text.replace("٠", "0").replace("١", "1").replace("٢", "2").replace("٣", "3") \
               .replace("٤", "4").replace("٥", "5").replace("٦", "6").replace("٧", "7") \
               .replace("٨", "8").replace("٩", "9")

    # حذف التشكيل (فتحة، ضمة، كسرة، تنوين...)
    text = re.sub(r'[\u064B-\u0652]', '', text)

    # إزالة "أل التعريف" إذا كانت موجودة في بداية الكلمة
    if text.startswith("ال"):
        text = text[2:]

    return text

# إعدادات تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# تحميل بيانات الجهات من ملف Excel
df = pd.read_excel("data.xlsx")

# دالة البحث عن الرقم الضريبي
async def reply_tax_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return  # تجاهل الرسائل الفارغة أو غير النصية

    message = update.message.text.strip()
    normalized_message = normalize_arabic(message)

    # البحث في البيانات بعد تطبيع الأسماء
    matches = []
    for _, row in df.iterrows():
        original_name = str(row.iloc[0])  # اسم الجهة
        normalized_name = normalize_arabic(original_name)  # تطبيع اسم الجهة

        if normalized_message in normalized_name:
            matches.append(row)

    if matches:
        results = ""
        for row in matches:
            results += f"📌 جهة العمل: {row.iloc[0]}\n🧾 الرقم الضريبي: {row.iloc[1]}\n\n"
        await update.message.reply_text(results)
    else:
        await update.message.reply_text("❌ لم يتم العثور على الجهة، حاول كتابة الاسم بشكل أدق.")

# دالة الترحيب عند /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا! 🖐\nأنا بوت لمساعدتك في العثور على الرقم الضريبي لجهة العمل.\n\n"
        "كل ما عليك فعله هو كتابة اسم جهة العمل (يمكنك كتابة كلمة واحدة فقط) وسأساعدك في العثور على الرقم الضريبي الخاص بها.\n"
        "سيتم عرض جميع النتائج المتقاربة والمتشابهة بناءً على الكلمة المكتوبة، بما في ذلك:\n"
        "- التاء المربوطة والهاء\n"
        "- الألف بهمزة أو بدون همزة\n"
        "- الأرقام العربية والإنجليزية\n"
        "- وجود أو عدم وجود 'ال' التعريف\n\n"
        "ابدأ بكتابة اسم جهة العمل الآن!"
    )

# إعداد البوت
app = ApplicationBuilder().token("7206442489:AAGnAUNioRKPs3rrkT2LeGcf35FHqZOWnzQ").build()

# إضافة المعالجات
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_tax_id))

# تشغيل البوت
app.run_polling(allowed_updates=Update.ALL_TYPES)
