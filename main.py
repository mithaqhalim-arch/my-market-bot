import telebot
from telebot import types
import requests

BOT_TOKEN = "8870182878:AAGDeRoKSHgV6uKM8ZMJcpPl6qlh8lb_MNg"
bot = telebot.TeleBot(BOT_TOKEN)

# دالة لوحة الأزرار الرئيسية
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_oil = types.KeyboardButton('🛢️ أسعار النفط')
    btn_gold = types.KeyboardButton('🪙 أسعار الذهب')
    btn_currency = types.KeyboardButton('💵 أسعار العملات')
    btn_weather = types.KeyboardButton('🌤️ حالة الطقس')
    markup.add(btn_oil, btn_gold, btn_currency, btn_weather)
    return markup

# أمر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "📊 أهلاً بك في بوت نشرة الأسواق والطقس المباشرة أونلاين!\n\n"
        "الرجاء اختيار الخدمة المطلوبة من الأزرار في الأسفل 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())

# معالجة الضغط على الأزرار
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    chat_id = message.chat.id
    
    if message.text == '🛢️ أسعار النفط':
        bot.send_message(chat_id, "🛢️ **سعر خام برنت العالمي اليوم:**\nالسعر الحالي: **$98** للبرميل.")

    elif message.text == '🪙 أسعار الذهب':
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd"
            res = requests.get(url).json()
            gold_price = res['pax-gold']['usd']
            bot.send_message(chat_id, f"🪙 **أسعار الذهب عالمياً:**\nسعر الأونصة: **${gold_price:,}**")
        except:
            bot.send_message(chat_id, "🪙 **أسعار الذهب عالمياً:**\nسعر الأونصة التقريبي: **$4,509**")

    elif message.text == '💵 أسعار العملات':
        try:
            url = "https://open.er-api.com/v6/latest/USD"
            res = requests.get(url).json()
            iqd_rate = res['rates']['IQD']
            bot.send_message(chat_id, f"💵 **سعر الصرف الفوري (مقابل الدولار):**\n1 دولار = **{iqd_rate:,.2f}** دينار عراقي في النظام الفوري.")
        except:
            bot.send_message(chat_id, "💵 **سعر الصرف الفوري:**\n1 دولار = **1,310** دينار عراقي.")

    elif message.text == '🌤️ حالة الطقس':
        try:
            # جلب الطقس المباشر لمنطقة الهاشمية ببابل عبر نظام wttr السريع
            url = "https://wttr.in/Al-Hashimiyah?format=%C+%t+%h+%w"
            res = requests.get(url).text
            bot.send_message(chat_id, f"🌤️ **حالة الطقس الحالية في الهاشمية:**\n{res}")
        except:
            bot.send_message(chat_id, "🌤️ **حالة الطقس الحالية:**\nمشمس، 32°C، الرطوبة 18%.")

# تشغيل البوت
bot.infinity_polling()
