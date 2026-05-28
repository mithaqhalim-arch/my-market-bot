import os
import time
import telebot
from telebot import types
import requests
from groq import Groq

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8870182878:AAGDeRoKSHgV6uKM8ZMJcpPl6qlh8lb_MNg")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ADMIN_ID = 413018511

groq_client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}
chat_histories = {}

def force_disconnect_old_sessions():
    try:
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            params={"offset": -1, "timeout": 1},
            timeout=3
        )
    except:
        pass
    time.sleep(3)

def load_instructions():
    try:
        with open("instructions.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "أنت مساعد ذكي مفيد. أجب باللغة العربية."

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton('🛢️ أسعار النفط'),
        types.KeyboardButton('🪙 أسعار الذهب'),
        types.KeyboardButton('💵 أسعار العملات'),
        types.KeyboardButton('🌤️ حالة الطقس'),
        types.KeyboardButton('₿ الجبوري'),
        types.KeyboardButton('🤖 اسأل الذكاء الاصطناعي'),
    )
    return markup

def chat_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💬 متابعة النقاش", callback_data="continue_chat"),
        types.InlineKeyboardButton("❌ إنهاء الدردشة", callback_data="end_chat"),
    )
    return markup

def ask_ai(chat_id, user_text):
    user_instructions = load_instructions()
    strict_system = (
        "أنت مساعد مقيّد تماماً. يجب أن تلتزم فقط بالتعليمات التالية ولا تتجاوزها أبداً.\n"
        "إذا طلب المستخدم أي شيء خارج نطاق هذه التعليمات (نكت، قصص، معلومات عامة، إلخ)، "
        "قل له بأدب: 'عذراً، أنا مخصص فقط للإجابة على أسئلة محددة. كيف أقدر أساعدك في هذا المجال؟'\n\n"
        "=== التعليمات المحددة ===\n"
        f"{user_instructions}"
    )
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    chat_histories[chat_id].append({"role": "user", "content": user_text})
    messages = [{"role": "system", "content": strict_system}] + chat_histories[chat_id]
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=500
    )
    answer = response.choices[0].message.content
    chat_histories[chat_id].append({"role": "assistant", "content": answer})
    return answer

@bot.message_handler(commands=['admin'])
def edit_instructions(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.chat.id] = 'waiting_new_instructions'
    current = load_instructions()
    bot.send_message(
        message.chat.id,
        f"📋 *التعليمات الحالية:*\n\n{current}\n\n✏️ أرسل التعليمات الجديدة الآن:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_states.pop(message.chat.id, None)
    chat_histories.pop(message.chat.id, None)
    bot.send_message(
        message.chat.id,
        "📊 أهلاً بك في بوت نشرة الأسواق والطقس المباشرة أونلاين!\n\nالرجاء اختيار الخدمة المطلوبة من الأزرار في الأسفل 👇",
        reply_markup=main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if call.data == "end_chat":
        user_states.pop(chat_id, None)
        chat_histories.pop(chat_id, None)
        bot.send_message(chat_id, "✅ تم إنهاء الدردشة. اختر من القائمة 👇", reply_markup=main_keyboard())

    elif call.data == "continue_chat":
        user_states[chat_id] = 'in_ai_chat'
        bot.send_message(chat_id, "💬 تفضّل، اكتب رسالتك:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text

    if user_states.get(chat_id) == 'waiting_new_instructions':
        user_states.pop(chat_id)
        try:
            with open("instructions.txt", "w", encoding="utf-8") as f:
                f.write(text)
            bot.send_message(chat_id, "✅ تم حفظ التعليمات الجديدة بنجاح!", reply_markup=main_keyboard())
        except:
            bot.send_message(chat_id, "❌ حصل خطأ أثناء الحفظ.", reply_markup=main_keyboard())
        return

    if user_states.get(chat_id) == 'in_ai_chat':
        bot.send_message(chat_id, "⏳ جاري المعالجة...")
        try:
            answer = ask_ai(chat_id, text)
            bot.send_message(chat_id, f"🤖 {answer}", reply_markup=chat_inline_keyboard())
        except Exception as e:
            bot.send_message(chat_id, f"❌ حصل خطأ: {str(e)}", reply_markup=main_keyboard())
            user_states.pop(chat_id, None)
        return

    if text == '🤖 اسأل الذكاء الاصطناعي':
        user_states[chat_id] = 'in_ai_chat'
        chat_histories.pop(chat_id, None)
        bot.send_message(chat_id, "🤖 مرحباً! اكتب سؤالك وأنا أجاوبك:", reply_markup=types.ReplyKeyboardRemove())

    elif text == '🛢️ أسعار النفط':
        bot.send_message(chat_id, "🛢️ *سعر خام برنت العالمي اليوم:*\nالسعر الحالي: *$98* للبرميل.", parse_mode="Markdown")

    elif text == '🪙 أسعار الذهب':
        try:
            res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", timeout=5).json()
            gold_price = res['pax-gold']['usd']
            bot.send_message(chat_id, f"🪙 *أسعار الذهب عالمياً:*\nسعر الأونصة: *${gold_price:,}*", parse_mode="Markdown")
        except:
            bot.send_message(chat_id, "🪙 *أسعار الذهب عالمياً:*\nسعر الأونصة التقريبي: *$4,509*", parse_mode="Markdown")

    elif text == '💵 أسعار العملات':
        try:
            res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
            iqd_rate = res['rates']['IQD']
            bot.send_message(chat_id, f"💵 *سعر الصرف الفوري:*\n1 دولار = *{iqd_rate:,.2f}* دينار عراقي", parse_mode="Markdown")
        except:
            bot.send_message(chat_id, "💵 *سعر الصرف الفوري:*\n1 دولار = *1,310* دينار عراقي", parse_mode="Markdown")

    elif text == '₿ الجبوري':
        try:
            res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5).json()
            btc_price = res['bitcoin']['usd']
            bot.send_message(chat_id, f"₿ *سعر البتكوين الآن:*\n1 BTC = *${btc_price:,}*", parse_mode="Markdown")
        except:
            bot.send_message(chat_id, "₿ *سعر البتكوين الآن:*\n1 BTC = *$68,000* (تقريبي)", parse_mode="Markdown")

    elif text == '🌤️ حالة الطقس':
        try:
            res = requests.get("https://wttr.in/Al-Hashimiyah?format=%C+%t+%h+%w", timeout=5).text
            bot.send_message(chat_id, f"🌤️ *حالة الطقس في الهاشمية:*\n{res}", parse_mode="Markdown")
        except:
            bot.send_message(chat_id, "🌤️ *حالة الطقس الحالية:*\nمشمس، 32°C، الرطوبة 18%.", parse_mode="Markdown")

    else:
        bot.send_message(chat_id, "اختر من القائمة أدناه 👇", reply_markup=main_keyboard())

print("جاري قطع الاتصالات القديمة...")
force_disconnect_old_sessions()
print("البوت يعمل الآن ✅")

while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"خطأ: {e} — إعادة التشغيل بعد 10 ثواني...")
        time.sleep(10)
        force_disconnect_old_sessions()
