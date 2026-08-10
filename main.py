import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "8985969212:AAHq61X8uwtNokrSA1QBzedvUwlJdfb1Lg8"  # BotFather'dan olingan token
ADMIN_ID = 8371392099  # O'zingizning Telegram ID'ingiz
CARD_NUMBER = "5614 6820 1716 6317 (Muxammadiyeva Dilafruz)"  # Karta raqamingiz va ism-sharifingiz

# Majburiy a'zolik uchun kanal sozlamalari:
CHANNEL_USERNAME = "Uzb_Premium_Stars"  # @ belgisisiz yozing
CHANNEL_ID = f"@{CHANNEL_USERNAME}"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==================== MAJBURITY A'ZOLIK TEKSHIRUVI ====================
async def check_sub(user_id: int) -> bool:
  if user_id == ADMIN_ID:
    return True
  try:
    member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    if member.status in ["creator", "administrator", "member"]:
      return True
    return False
  except Exception as e:
    logging.error(f"Kanal a'zoligini tekshirishda xatolik: {e}")
    return False


def get_sub_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📢 Kanalga a'zo bo'lish",
                  url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="✅ Tekshirish", callback_data="check_subscription"
              )
          ],
      ]
  )


# ==================== DATABASE (SQLITE) ====================
def init_db():
  conn = sqlite3.connect("bot_data.db")
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
  default_prices = [
      ("prem_1", 45000),
      ("prem_3", 120000),
      ("prem_6", 210000),
      ("prem_12", 380000),
      ("star_price", 300),
  ]
  cursor.executemany("INSERT OR IGNORE INTO prices VALUES (?, ?)", default_prices)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER
        )
    """)
  conn.commit()
  conn.close()


def get_price(key):
  conn = sqlite3.connect("bot_data.db")
  cursor = conn.cursor()
  cursor.execute("SELECT value FROM prices WHERE key = ?", (key,))
  res = cursor.fetchone()
  conn.close()
  return res[0] if res else 0


def set_price(key, val):
  conn = sqlite3.connect("bot_data.db")
  cursor = conn.cursor()
  cursor.execute("UPDATE prices SET value = ? WHERE key = ?", (val, key))
  conn.commit()
  conn.close()


def add_product(name, price):
  conn = sqlite3.connect("bot_data.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO products (name, price) VALUES (?, ?)", (name, price)
  )
  conn.commit()
  conn.close()


def get_products():
  conn = sqlite3.connect("bot_data.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id, name, price FROM products")
  prods = cursor.fetchall()
  conn.close()
  return prods


def delete_product(prod_id):
  conn = sqlite3.connect("bot_data.db")
  cursor = conn.cursor()
  cursor.execute("DELETE FROM products WHERE id = ?", (prod_id,))
  conn.commit()
  conn.close()


orders_db = {}


# ==================== FSM HOLATLARI ====================
class OrderState(StatesGroup):
  waiting_for_username = State()
  waiting_for_stars_amount = State()
  waiting_for_check = State()


class AdminState(StatesGroup):
  waiting_for_price = State()
  waiting_for_prod_name = State()
  waiting_for_prod_price = State()


# ==================== KLAVIATURALAR ====================
def main_menu(user_id):
  kb = [
      [
          InlineKeyboardButton(
              text="⭐ Telegram Premium", callback_data="menu_premium"
          )
      ],
      [
          InlineKeyboardButton(
              text="🌟 Telegram Stars", callback_data="menu_stars"
          )
      ],
      [
          InlineKeyboardButton(
              text="📦 Sotiladigan mahsulotlar", callback_data="menu_products"
          )
      ],
  ]
  if user_id == ADMIN_ID:
    kb.append([
        InlineKeyboardButton(
            text="⚙️ Admin Panel", callback_data="admin_panel"
        )
    ])
  return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_menu():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="✏️ Premium Narxlarini O'zgartirish",
                  callback_data="admin_edit_prem",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⭐ Stars Narxini O'zgartirish",
                  callback_data="admin_edit_stars",
              )
          ],
          [
              InlineKeyboardButton(
                  text="➕ Yangi Mahsulot Qo'shish",
                  callback_data="admin_add_prod",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🗑 Mahsulotni O'chirish",
                  callback_data="admin_del_prod",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⬅️ Bosh Menyu", callback_data="back_to_main"
              )
          ],
      ]
  )


# ==================== USER HANDLERS ====================
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
  await state.clear()

  if not await check_sub(message.from_user.id):
    return await message.answer(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  await message.answer(
      "👋 Salom! Kerakli bo'limni tanlang:",
      reply_markup=main_menu(message.from_user.id),
  )


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
  await callback.answer()
  if await check_sub(callback.from_user.id):
    await callback.message.delete()
    await callback.message.answer(
        "✅ A'zolik tasdiqlandi! Kerakli bo'limni tanlang:",
        reply_markup=main_menu(callback.from_user.id),
    )
  else:
    await callback.answer(
        "❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True
    )


@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
  await callback.answer()
  await state.clear()

  if not await check_sub(callback.from_user.id):
    return await callback.message.edit_text(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  await callback.message.edit_text(
      "👋 Kerakli bo'limni tanlang:",
      reply_markup=main_menu(callback.from_user.id),
  )


# 1. TELEGRAM PREMIUM
@dp.callback_query(F.data == "menu_premium")
async def premium_tariffs(callback: types.CallbackQuery):
  await callback.answer()
  if not await check_sub(callback.from_user.id):
    return await callback.message.edit_text(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  p1, p3, p6, p12 = (
      get_price("prem_1"),
      get_price("prem_3"),
      get_price("prem_6"),
      get_price("prem_12"),
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text=f"1 Oy — {p1:,} so'm", callback_data="buy_prem_1"
              )
          ],
          [
              InlineKeyboardButton(
                  text=f"3 Oy — {p3:,} so'm", callback_data="buy_prem_3"
              )
          ],
          [
              InlineKeyboardButton(
                  text=f"6 Oy — {p6:,} so'm", callback_data="buy_prem_6"
              )
          ],
          [
              InlineKeyboardButton(
                  text=f"12 Oy — {p12:,} so'm", callback_data="buy_prem_12"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⬅️ Orqaga", callback_data="back_to_main"
              )
          ],
      ]
  )
  await callback.message.edit_text(
      "⭐ Telegram Premium tariflarini tanlang:", reply_markup=kb
  )


@dp.callback_query(F.data.startswith("buy_prem_"))
async def process_prem_choice(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.answer()
  if not await check_sub(callback.from_user.id):
    return await callback.message.edit_text(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  months = callback.data.split("_")[2]
  price = get_price(f"prem_{months}")

  await state.update_data(
      product=f"Telegram Premium ({months} oy)", price=f"{price:,}"
  )
  await callback.message.edit_text(
      f"Siz {months} oylik Premium tanladingiz.\n\nTelegram **username**ingizni"
      " kiriting (`@username`):"
  )
  await state.set_state(OrderState.waiting_for_username)


# 2. TELEGRAM STARS
@dp.callback_query(F.data == "menu_stars")
async def stars_menu(callback: types.CallbackQuery, state: FSMContext):
  await callback.answer()
  if not await check_sub(callback.from_user.id):
    return await callback.message.edit_text(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  star_p = get_price("star_price")
  await state.update_data(product="Telegram Stars")
  await callback.message.edit_text(
      f"🌟 Nechta Telegram Stars olmoqchisiz?\n(1 ta Stars = {star_p} so'm)\n\n"
      "Sanoqni kiriting (masalan: 50, 100, 500):"
  )
  await state.set_state(OrderState.waiting_for_stars_amount)


@dp.message(OrderState.waiting_for_stars_amount)
async def process_stars_amount(message: types.Message, state: FSMContext):
  if not await check_sub(message.from_user.id):
    return await message.answer(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  if not message.text.isdigit():
    return await message.answer("Iltimos, faqat raqam kiriting:")

  amount = int(message.text)
  star_p = get_price("star_price")
  total_price = amount * star_p

  await state.update_data(
      product=f"Telegram Stars ({amount} ta)", price=f"{total_price:,}"
  )
  await message.answer(
      "Stars yuborilishi kerak bo'lgan **username**ni kiriting (`@username`):"
  )
  await state.set_state(OrderState.waiting_for_username)


# 3. SOTILADIGAN MAHSULOTLAR
@dp.callback_query(F.data == "menu_products")
async def products_menu(callback: types.CallbackQuery):
  await callback.answer()
  if not await check_sub(callback.from_user.id):
    return await callback.message.edit_text(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  prods = get_products()
  kb = []
  for p_id, name, price in prods:
    kb.append([
        InlineKeyboardButton(
            text=f"📦 {name} — {price:,} so'm",
            callback_data=f"buy_prod_{p_id}",
        )
    ])
  kb.append(
      [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
  )

  await callback.message.edit_text(
      "📦 Mavjud mahsulotlar ro'yxati:",
      reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
  )


@dp.callback_query(F.data.startswith("buy_prod_"))
async def process_prod_choice(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.answer()
  if not await check_sub(callback.from_user.id):
    return await callback.message.edit_text(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  p_id = int(callback.data.split("_")[2])
  prods = get_products()
  selected = next((p for p in prods if p[0] == p_id), None)

  if selected:
    await state.update_data(product=selected[1], price=f"{selected[2]:,}")
    await callback.message.edit_text(
        "Mahsulot yetkazib berilishi uchun Telegram **username**ingizni"
        " kiriting:"
    )
    await state.set_state(OrderState.waiting_for_username)


# USERNAME VA TO'LOV CHEKI QABUL QILISH
@dp.message(OrderState.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
  if not await check_sub(message.from_user.id):
    return await message.answer(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  target_username = message.text.replace("@", "").strip()
  await state.update_data(username=target_username)
  data = await state.get_data()

  pay_text = (
      f"💳 **TO'LOV BAZASI**\n\n"
      f"📌 **Mahsulot:** {data['product']}\n"
      f"👤 **Qabul qiluvchi:** @{target_username}\n"
      f"💰 **To'lov summasi:** {data['price']} so'm\n\n"
      f"👇 To'lovni ushbu karta raqamiga o'tkazing:\n`{CARD_NUMBER}`\n\n"
      f"To'lovni amalga oshirgach, **to'lov chekini (skrinshot)** yuboring!"
  )
  await message.answer(pay_text, parse_mode="Markdown")
  await state.set_state(OrderState.waiting_for_check)


@dp.message(OrderState.waiting_for_check, F.photo)
async def process_check_photo(message: types.Message, state: FSMContext):
  if not await check_sub(message.from_user.id):
    return await message.answer(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  data = await state.get_data()
  photo_id = message.photo[-1].file_id
  order_id = f"{message.from_user.id}_{message.message_id}"

  orders_db[order_id] = {
      "user_id": message.from_user.id,
      "product": data["product"],
      "username": data["username"],
      "price": data["price"],
  }

  admin_kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="✅ Tasdiqlash", callback_data=f"approve_{order_id}"
          ),
          InlineKeyboardButton(
              text="❌ Rad etish", callback_data=f"reject_{order_id}"
          ),
      ]]
  )

  admin_text = (
      f"🔔 **Yangi buyurtma!**\n\n📦 **Mahsulot:** {data['product']}\n💵"
      f" **Narxi:** {data['price']} so'm\n👤 **Mijoz:** @{data['username']}"
  )
  await bot.send_photo(
      chat_id=ADMIN_ID,
      photo=photo_id,
      caption=admin_text,
      reply_markup=admin_kb,
      parse_mode="Markdown",
  )

  await message.answer(
      "✅ Chek qabul qilindi! Admin to'lovni tekshirib, tez orada xizmatni"
      " faollashtiradi."
  )
  await state.clear()


# ==================== ADMIN PANEL HANDLERS ====================
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  await callback.message.edit_text(
      "⚙️ **ADMIN PANEL**\nKerakli bo'limni tanlang:", reply_markup=admin_menu()
  )


@dp.callback_query(F.data == "admin_edit_prem")
async def edit_prem_menu(callback: types.CallbackQuery):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="1 Oy", callback_data="set_key_prem_1"
              ),
              InlineKeyboardButton(
                  text="3 Oy", callback_data="set_key_prem_3"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="6 Oy", callback_data="set_key_prem_6"
              ),
              InlineKeyboardButton(
                  text="12 Oy", callback_data="set_key_prem_12"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="⬅️ Orqaga", callback_data="admin_panel"
              )
          ],
      ]
  )
  await callback.message.edit_text(
      "Qaysi Premium tarif narxini o'zgartirmoqchisiz?", reply_markup=kb
  )


@dp.callback_query(F.data.startswith("set_key_"))
async def select_price_key(callback: types.CallbackQuery, state: FSMContext):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  key = callback.data.replace("set_key_", "")
  await state.update_data(edit_key=key)
  await callback.message.edit_text(
      "Yangi narxni kiriting (faqat raqam, masalan: 50000):"
  )
  await state.set_state(AdminState.waiting_for_price)


@dp.callback_query(F.data == "admin_edit_stars")
async def edit_stars_price(callback: types.CallbackQuery, state: FSMContext):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  await state.update_data(edit_key="star_price")
  await callback.message.edit_text(
      "1 ta Stars uchun yangi narxni kiriting (masalan: 350):"
  )
  await state.set_state(AdminState.waiting_for_price)


@dp.message(AdminState.waiting_for_price)
async def save_new_price(message: types.Message, state: FSMContext):
  if message.from_user.id != ADMIN_ID:
    return
  if not message.text.isdigit():
    return await message.answer("Iltimos, faqat raqam kiriting:")

  data = await state.get_data()
  set_price(data["edit_key"], int(message.text))
  await message.answer(
      "✅ Narx muvaffaqiyatli yangilandi!", reply_markup=admin_menu()
  )
  await state.clear()


@dp.callback_query(F.data == "admin_add_prod")
async def add_prod_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  await callback.message.edit_text(
      "Yangi mahsulot nomini kiriting (masalan: eFootball Akkaunt):"
  )
  await state.set_state(AdminState.waiting_for_prod_name)


@dp.message(AdminState.waiting_for_prod_name)
async def add_prod_name(message: types.Message, state: FSMContext):
  if message.from_user.id != ADMIN_ID:
    return
  await state.update_data(new_prod_name=message.text)
  await message.answer("Mahsulot narxini kiriting (so'mda, faqat raqam):")
  await state.set_state(AdminState.waiting_for_prod_price)


@dp.message(AdminState.waiting_for_prod_price)
async def add_prod_price(message: types.Message, state: FSMContext):
  if message.from_user.id != ADMIN_ID:
    return
  if not message.text.isdigit():
    return await message.answer("Iltimos, faqat raqam kiriting:")

  data = await state.get_data()
  add_product(data["new_prod_name"], int(message.text))
  await message.answer(
      f"✅ **{data['new_prod_name']}** mahsuloti qo'shildi!",
      reply_markup=admin_menu(),
  )
  await state.clear()


@dp.callback_query(F.data == "admin_del_prod")
async def del_prod_menu(callback: types.CallbackQuery):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  prods = get_products()
  kb = []
  for p_id, name, price in prods:
    kb.append(
        [InlineKeyboardButton(text=f"❌ {name}", callback_data=f"del_p_{p_id}")]
    )
  kb.append(
      [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel")]
  )

  await callback.message.edit_text(
      "O'chirmoqchi bo'lgan mahsulotingizni tanlang:",
      reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
  )


@dp.callback_query(F.data.startswith("del_p_"))
async def del_prod_action(callback: types.CallbackQuery):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  p_id = int(callback.data.split("_")[2])
  delete_product(p_id)
  await callback.answer("Mahsulot o'chirildi!")
  await admin_panel(callback)


# ADMIN TASDIQLASHI YOKI RAD ETISHI
@dp.callback_query(F.data.startswith("approve_"))
async def approve_order(callback: types.CallbackQuery):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  order_id = callback.data.replace("approve_", "")
  order = orders_db.get(order_id)
  if order:
    await bot.send_message(
        order["user_id"],
        f"🎉 **Xushxabar!** Sizning **{order['product']}** uchun to'lovingiz"
        " tasdiqlandi va yetkazib berildi!",
    )
    await callback.message.edit_caption(
        caption=(
            f"{callback.message.caption}\n\n✅ **ADMIN TARAFIDAN TASDIQLANDI**"
        )
    )
  else:
    await callback.answer("Buyurtma topilmadi.")


@dp.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: types.CallbackQuery):
  await callback.answer()
  if callback.from_user.id != ADMIN_ID:
    return
  order_id = callback.data.replace("reject_", "")
  order = orders_db.get(order_id)
  if order:
    await bot.send_message(
        order["user_id"],
        f"❌ Sizning **{order['product']}** uchun to'lovingiz rad etildi. Qayta"
        " tekshirib ko'ring.",
    )
    await callback.message.edit_caption(
        caption=(
            f"{callback.message.caption}\n\n❌ **ADMIN TARAFIDAN RAD ETILDI**"
        )
    )
  else:
    await callback.answer("Buyurtma topilmadi.")


# ==================== KUTILMAGAN XABARLARNI TUTISH (FALLBACK) ====================
@dp.message()
async def fallback_handler(message: types.Message, state: FSMContext):
  if not await check_sub(message.from_user.id):
    return await message.answer(
        "⚠️ Botdan foydalanish uchun avval quyidagi kanalga a'zo bo'ling:",
        reply_markup=get_sub_keyboard(),
    )

  current_state = await state.get_state()
  if current_state is None:
    await message.answer(
        "⚠️ Noma'lum buyruq! Iltimos, quyidagi menyudan birini tanlang:",
        reply_markup=main_menu(message.from_user.id),
    )


# ==================== MAIN ====================
async def main():
  init_db()
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
