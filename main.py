import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "8675542895:AAEr2_UCszsVB5xAqL-fmSr5EQkee1H5M1c"  # BotFather'dan olingan token
ADMIN_ID = 8371392099  # Telegram ID-ingiz

CARD_NUMBER = "5614 6820 1716 6317"
CARD_NAME = "Muxammadiyeva Dilafruz"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==================== FSM (HOLATLAR) ====================
class OrderState(StatesGroup):
    waiting_for_username = State()
    waiting_for_receipt = State()

# ==================== KEYBOARDLAR ====================
def main_menu():
    kb = [
        [KeyboardButton(text="⭐ Telegram Stars"), KeyboardButton(text="🌟 Telegram Premium")],
        [KeyboardButton(text="ℹ️ Biz haqimizda / Yordam")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def stars_menu():
    kb = [
        [InlineKeyboardButton(text="50 Stars — 15 000 so'm", callback_data="buy_stars_50_15000")],
        [InlineKeyboardButton(text="100 Stars — 29 000 so'm", callback_data="buy_stars_100_29000")],
        [InlineKeyboardButton(text="250 Stars — 72 000 so'm", callback_data="buy_stars_250_72000")],
        [InlineKeyboardButton(text="500 Stars — 135 000 so'm", callback_data="buy_stars_500_135000")],
        [InlineKeyboardButton(text="1000 Stars — 260 000 so'm", callback_data="buy_stars_1000_260000")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def premium_menu():
    kb = [
        [InlineKeyboardButton(text="1 Oy Premium — 45 000 so'm", callback_data="buy_prem_1_45000")],
        [InlineKeyboardButton(text="3 Oy Premium — 155 000 so'm", callback_data="buy_prem_3_155000")],
        [InlineKeyboardButton(text="6 Oy Premium — 225 000 so'm", callback_data="buy_prem_6_225000")],
        [InlineKeyboardButton(text="12 Oy Premium — 400 000 so'm", callback_data="buy_prem_12_397000")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== HANDLERLAR ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Xush kelibsiz, {message.from_user.first_name}!\n\n"
        "Telegram Premium va Stars xizmatlarimizdan birini tanlang:",
        reply_markup=main_menu()
    )

@dp.message(F.text == "⭐ Telegram Stars")
async def show_stars(message: types.Message):
    await message.answer("Kerakli Telegram Stars paketini tanlang:", reply_markup=stars_menu())

@dp.message(F.text == "🌟 Telegram Premium")
async def show_premium(message: types.Message):
    await message.answer("Kerakli Telegram Premium tarifini tanlang:", reply_markup=premium_menu())

@dp.message(F.text == "ℹ️ Biz haqimizda / Yordam")
async def show_help(message: types.Message):
    await message.answer(
        "📌 **Xizmatimiz haqida:**\n"
        "Barchasi rasmiy va 100% xavfsiz.\n\n"
        "📞 Murojaat uchun Admin: @Py_Craft"
    )

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    item_type = data[1]
    amount = data[2]
    price = data[3]

    title = f"{amount} Stars" if item_type == "stars" else f"{amount} Oylik Premium"
    await state.update_data(item_title=title, price=price)
    
    extra_note = ""
    if item_type == "prem" and amount == "1":
        extra_note = "\n\n⚠️ *Eslatma: 1 oylik Premium kirib berish orqali faollashtiriladi.*"

    await callback.message.edit_text(
        f"Siz tanladingiz: **{title}**\n"
        f"To'lov summasi: **{int(price):,} so'm**{extra_note}\n\n"
        "Iltimos, Telegram **@username**'ingizni yozib yuboring:"
    )
    await state.set_state(OrderState.waiting_for_username)

@dp.message(OrderState.waiting_for_username, F.text)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if not username.startswith("@"):
        username = "@" + username

    await state.update_data(target_username=username)
    user_data = await state.get_data()

    await message.answer(
        f"To'lovni amalga oshiring:\n\n"
        f"💳 Karta: `{CARD_NUMBER}`\n"
        f"👤 Egasining ismi: **{CARD_NAME}**\n"
        f"💰 Summa: **{int(user_data['price']):,} so'm**\n\n"
        f"To'lovni amalga oshirgach, to'lov **cheki (skrinshot/PDF)**'ini shu yerga yuboring."
    )
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo | F.document)
async def process_receipt(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    await message.answer(
        "✅ Rahmat! To'lov cheki qabul qilindi.\n"
        "Operatorimiz tez orada to'lovni tekshirib, xizmatni faollashtirib beradi.",
        reply_markup=main_menu()
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"done_{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
        ]
    ])

    admin_text = (
        "📥 **Yangi buyurtma!**\n\n"
        f"👤 Xaridor: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"🛒 Mahsulot: **{user_data['item_title']}**\n"
        f"💵 Summa: **{int(user_data['price']):,} so'm**\n"
        f"🎯 Qabul qiluvchi: **{user_data['target_username']}**"
    )

    if message.photo:
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=admin_text, reply_markup=admin_kb)
    elif message.document:
        await bot.send_document(chat_id=ADMIN_ID, document=message.document.file_id, caption=admin_text, reply_markup=admin_kb)

    await state.clear()

@dp.callback_query(F.data.startswith(("done_", "reject_")))
async def process_admin_action(callback: types.CallbackQuery):
    action, user_id = callback.data.split("_")
    user_id = int(user_id)

    if action == "done":
        await bot.send_message(chat_id=user_id, text="🎉 Buyurtmangiz muvaffaqiyatli bajarildi! Bizning xizmatimizdan foydalanganingiz uchun rahmat.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟢 **HOLAT: BAJARILDI**")
    elif action == "reject":
        await bot.send_message(chat_id=user_id, text="❌ To'lovingiz tasdiqlanmadi yoki xatolik yuz berdi. Iltimos, admin bilan bog'laning.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🔴 **HOLAT: RAD ETILDI**")

@dp.message()
async def fallback_unknown_message(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Iltimos, pastdagi menyudan foydalaning 👇",
        reply_markup=main_menu()
    )

# ==================== RENDER UCHUN VEB-SERVER (PORT TINGLOVCHI) ====================
async def handle(request):
    return web.Response(text="Bot Render serverida muvaffaqiyatli ishlayapti!")

async def main():
    # Render avtomatik beradigan PORT ni olamiz
    PORT = int(os.environ.get("PORT", 8080))
    
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    print(f"Veb-server {PORT}-portda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
