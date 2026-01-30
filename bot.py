import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
from datetime import datetime

# Bot Token - Environment variable dan olish
BOT_TOKEN = os.getenv("BOT_TOKEN", "7673962223:AAHAE0HRRwTcFG_lFtkKz_1HkF7ThWJ2_34")

# Admin ID - Environment variable dan olish
ADMIN_ID = int(os.getenv("ADMIN_ID", "6965587290"))

# Kuryerlar ID lari - Environment variable dan olish
COURIER_IDS_STR = os.getenv("COURIER_IDS", "6168822836")
COURIER_IDS = [int(id.strip()) for id in COURIER_IDS_STR.split(",") if id.strip()]

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Database yaratish
def init_db():
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    
    # Buyurtmalar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            phone TEXT,
            address TEXT,
            items TEXT,
            total_price INTEGER,
            payment_method TEXT,
            status TEXT DEFAULT 'Yangi',
            courier_id INTEGER,
            courier_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            delivered_at TIMESTAMP
        )
    ''')
    
    # Kuryerlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS couriers (
            id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            total_orders INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Mahsulotlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '🍔',
            price INTEGER NOT NULL,
            photo TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Standart mahsulotlarni qo'shish (agar jadval bo'sh bo'lsa)
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        default_products = [
            ("Burger", "🍔", 25000, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500", "Mazali burger"),
            ("Lavash", "🌯", 20000, "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=500", "Go'shtli lavash"),
            ("Pizza", "🍕", 35000, "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500", "Pepperoni pizza"),
            ("Hot Dog", "🌭", 15000, "https://images.unsplash.com/photo-1612392166886-ee7c87380c5c?w=500", "Sosiskali hot-dog"),
            ("Fri", "🍟", 12000, "https://images.unsplash.com/photo-1630431341973-02e6c2c2c4b7?w=500", "Kartoshka fri"),
            ("Cola", "🥤", 5000, "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=500", "Sovuq ichimlik"),
        ]
        cursor.executemany(
            "INSERT INTO products (name, emoji, price, photo, description) VALUES (?, ?, ?, ?, ?)",
            default_products
        )
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Holatlar
class OrderStates(StatesGroup):
    phone = State()
    address = State()
    payment = State()

class CourierStates(StatesGroup):
    register_name = State()
    register_phone = State()

# Admin mahsulot qo'shish holatlari
class ProductStates(StatesGroup):
    name = State()
    emoji = State()
    price = State()
    photo = State()
    description = State()

# Admin mahsulot tahrirlash holatlari
class EditProductStates(StatesGroup):
    choose_field = State()
    new_value = State()

# Mahsulotlarni bazadan olish
def get_products():
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, emoji, price, photo, description FROM products WHERE is_active=1")
    products = cursor.fetchall()
    conn.close()
    
    menu = {}
    for product in products:
        product_id, name, emoji, price, photo, description = product
        menu[f"product_{product_id}"] = {
            "id": product_id,
            "name": f"{emoji} {name}",
            "price": price,
            "photo": photo,
            "description": description
        }
    return menu

DELIVERY_PRICE = 10000

# Buyurtma statuslari
ORDER_STATUS = {
    "Yangi": "🆕 Yangi",
    "Qabul qilindi": "✅ Qabul qilindi",
    "Kuryerda": "🚚 Kuryerda",
    "Yetkazildi": "✅ Yetkazildi",
    "Bekor qilindi": "❌ Bekor qilindi"
}

# Savat - har bir foydalanuvchi uchun
user_carts = {}

def get_cart(user_id):
    if user_id not in user_carts:
        user_carts[user_id] = {}
    return user_carts[user_id]

def format_price(price):
    return f"{price:,}".replace(",", " ")

def is_courier(user_id):
    return user_id in COURIER_IDS

def is_admin(user_id):
    return user_id == ADMIN_ID

# Asosiy menyu
def main_menu():
    keyboard = [
        [KeyboardButton(text="🍽 Menyu"), KeyboardButton(text="🛒 Savat")],
        [KeyboardButton(text="📦 Mening buyurtmalarim"), KeyboardButton(text="ℹ️ Ma'lumot")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Admin menyu
def admin_menu():
    keyboard = [
        [KeyboardButton(text="📊 Barcha buyurtmalar"), KeyboardButton(text="🆕 Yangi buyurtmalar")],
        [KeyboardButton(text="👥 Kuryerlar"), KeyboardButton(text="📈 Statistika")],
        [KeyboardButton(text="🍽 Mahsulotlar boshqaruvi"), KeyboardButton(text="➕ Mahsulot qo'shish")],
        [KeyboardButton(text="🍽 Menyu"), KeyboardButton(text="🛒 Savat")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Kuryer menyu
def courier_menu():
    keyboard = [
        [KeyboardButton(text="📋 Aktiv buyurtmalar"), KeyboardButton(text="✅ Yetkazilgan buyurtmalar")],
        [KeyboardButton(text="📊 Mening statistikam"), KeyboardButton(text="📦 Barcha buyurtmalarim")],
        [KeyboardButton(text="ℹ️ Ma'lumot")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Kategoriyalar inline keyboard
def menu_keyboard():
    MENU = get_products()
    keyboard = []
    row = []
    for i, (key, item) in enumerate(MENU.items()):
        row.append(InlineKeyboardButton(text=item["name"], callback_data=f"item_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Mahsulot tafsilotlari
def item_keyboard(item_id):
    keyboard = [
        [
            InlineKeyboardButton(text="➖", callback_data=f"decrease_{item_id}"),
            InlineKeyboardButton(text="Savatga qo'shish", callback_data=f"add_{item_id}"),
            InlineKeyboardButton(text="➕", callback_data=f"increase_{item_id}")
        ],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Savat tugmalari
def cart_keyboard(user_id):
    cart = get_cart(user_id)
    MENU = get_products()
    keyboard = []
    
    for item_id, quantity in cart.items():
        if item_id in MENU:
            item = MENU[item_id]
            keyboard.append([
                InlineKeyboardButton(text="➖", callback_data=f"cart_decrease_{item_id}"),
                InlineKeyboardButton(text=f"{item['name']} x{quantity}", callback_data=f"cart_view_{item_id}"),
                InlineKeyboardButton(text="➕", callback_data=f"cart_increase_{item_id}")
            ])
    
    if cart:
        keyboard.append([InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart")])
        keyboard.append([InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="checkout")])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Asosiy menyu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# To'lov usullari
def payment_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="💵 Naqd pul", callback_data="pay_cash")],
        [InlineKeyboardButton(text="💳 Payme", callback_data="pay_payme")],
        [InlineKeyboardButton(text="💳 Click", callback_data="pay_click")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Admin: Buyurtma boshqarish
def admin_order_keyboard(order_id, current_status):
    keyboard = []
    
    if current_status == "Yangi":
        keyboard.append([InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"admin_accept_{order_id}")])
        keyboard.append([InlineKeyboardButton(text="🚚 Kuryerga topshirish", callback_data=f"admin_assign_{order_id}")])
    elif current_status == "Qabul qilindi":
        keyboard.append([InlineKeyboardButton(text="🚚 Kuryerga topshirish", callback_data=f"admin_assign_{order_id}")])
    
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin_cancel_{order_id}")])
    keyboard.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Kuryer tanlash
def select_courier_keyboard(order_id):
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name, username FROM couriers WHERE is_active=1')
    couriers = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for courier_id, full_name, username in couriers:
        keyboard.append([InlineKeyboardButton(
            text=f"👤 {full_name} (@{username})", 
            callback_data=f"assign_courier_{order_id}_{courier_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"admin_order_{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Kuryer: Buyurtma boshqarish
def courier_order_keyboard(order_id, current_status):
    keyboard = []
    
    if current_status == "Kuryerda":
        keyboard.append([InlineKeyboardButton(text="✅ Yetkazib berdim", callback_data=f"courier_delivered_{order_id}")])
    
    keyboard.append([InlineKeyboardButton(text="📞 Mijozga qo'ng'iroq qilish", callback_data=f"courier_call_{order_id}")])
    keyboard.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="courier_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Admin: Mahsulotlar boshqaruvi keyboard
def products_management_keyboard():
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, emoji, price, is_active FROM products ORDER BY id")
    products = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for product_id, name, emoji, price, is_active in products:
        status = "✅" if is_active else "❌"
        keyboard.append([InlineKeyboardButton(
            text=f"{status} {emoji} {name} - {format_price(price)} so'm",
            callback_data=f"edit_product_{product_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Admin: Mahsulotni tahrirlash keyboard
def edit_product_keyboard(product_id):
    keyboard = [
        [InlineKeyboardButton(text="✏️ Nomini o'zgartirish", callback_data=f"edit_name_{product_id}")],
        [InlineKeyboardButton(text="🎨 Emoji o'zgartirish", callback_data=f"edit_emoji_{product_id}")],
        [InlineKeyboardButton(text="💰 Narxini o'zgartirish", callback_data=f"edit_price_{product_id}")],
        [InlineKeyboardButton(text="🖼 Rasmini o'zgartirish", callback_data=f"edit_photo_{product_id}")],
        [InlineKeyboardButton(text="📝 Ta'rifini o'zgartirish", callback_data=f"edit_desc_{product_id}")],
        [InlineKeyboardButton(text="🔄 Faolligini o'zgartirish", callback_data=f"toggle_active_{product_id}")],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_product_{product_id}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="products_management")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# /start buyrug'i
@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        keyboard = admin_menu()
        text = "Assalomu alaykum, Admin! 👨‍💼\n\n📊 Boshqaruv paneliga xush kelibsiz."
    elif is_courier(user_id):
        keyboard = courier_menu()
        
        # Kuryerni bazaga qo'shish (agar yo'q bo'lsa)
        conn = sqlite3.connect('fastfood.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM couriers WHERE id=?', (user_id,))
        if not cursor.fetchone():
            full_name = message.from_user.first_name or "Kuryer"
            username = message.from_user.username or "kuryer"
            cursor.execute('''
                INSERT INTO couriers (id, username, full_name) 
                VALUES (?, ?, ?)
            ''', (user_id, username, full_name))
            conn.commit()
            logger.info(f"Yangi kuryer ro'yxatga olindi: {full_name} (ID: {user_id})")
        conn.close()
        
        text = f"Assalomu alaykum, {message.from_user.first_name}! 🚚\n\n"
        text += f"📋 Kuryer paneliga xush kelibsiz.\n"
        text += f"Sizning ID: {user_id}\n\n"
        text += f"✅ Siz muvaffaqiyatli tizimga kiritildingiz!"
    else:
        keyboard = main_menu()
        text = f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n🍕 FoodTime botiga xush kelibsiz!\n\nMenyu ko'rish va buyurtma berish uchun tugmalardan foydalaning."
    
    await message.answer(text, reply_markup=keyboard)

# ==================== MAHSULOTLAR BOSHQARUVI ====================

# Admin: Mahsulotlar ro'yxati
@router.message(F.text == "🍽 Mahsulotlar boshqaruvi")
async def products_management(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    await message.answer(
        "🍽 *Mahsulotlar boshqaruvi*\n\nTahrirlash uchun mahsulotni tanlang:",
        reply_markup=products_management_keyboard(),
        parse_mode="Markdown"
    )

# Admin: Mahsulot qo'shish - boshlash
@router.message(F.text == "➕ Mahsulot qo'shish")
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    await message.answer(
        "➕ *Yangi mahsulot qo'shish*\n\n📝 Mahsulot nomini kiriting:",
        parse_mode="Markdown"
    )
    await state.set_state(ProductStates.name)

# Mahsulot nomi
@router.message(ProductStates.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        "🎨 Mahsulot uchun emoji kiriting:\n\nMasalan: 🍔, 🍕, 🌭"
    )
    await state.set_state(ProductStates.emoji)

# Mahsulot emoji
@router.message(ProductStates.emoji)
async def add_product_emoji(message: Message, state: FSMContext):
    await state.update_data(emoji=message.text.strip())
    await message.answer(
        "💰 Mahsulot narxini kiriting (faqat raqam):\n\nMasalan: 25000"
    )
    await state.set_state(ProductStates.price)

# Mahsulot narxi
@router.message(ProductStates.price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        await state.update_data(price=price)
        await message.answer(
            "🖼 Mahsulot rasmining URL manzilini kiriting:\n\n"
            "Masalan: https://example.com/image.jpg\n\n"
            "Yoki 'o'tkazib yuborish' deb yozing."
        )
        await state.set_state(ProductStates.photo)
    except ValueError:
        await message.answer("❌ Narx faqat raqamdan iborat bo'lishi kerak. Qaytadan kiriting:")

# Mahsulot rasmi
@router.message(ProductStates.photo)
async def add_product_photo(message: Message, state: FSMContext):
    photo = message.text.strip()
    if photo.lower() in ['o\'tkazib yuborish', 'skip', 'otkazib yuborish']:
        photo = ""
    await state.update_data(photo=photo)
    await message.answer(
        "📝 Mahsulot ta'rifini kiriting:\n\n"
        "Yoki 'o'tkazib yuborish' deb yozing."
    )
    await state.set_state(ProductStates.description)

# Mahsulot ta'rifi va saqlash
@router.message(ProductStates.description)
async def add_product_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if description.lower() in ['o\'tkazib yuborish', 'skip', 'otkazib yuborish']:
        description = ""
    
    data = await state.get_data()
    
    # Ma'lumotlar bazasiga saqlash
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, emoji, price, photo, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['name'], data['emoji'], data['price'], data.get('photo', ''), description))
    conn.commit()
    conn.close()
    
    text = f"✅ *Mahsulot muvaffaqiyatli qo'shildi!*\n\n"
    text += f"{data['emoji']} *{data['name']}*\n"
    text += f"💰 Narxi: {format_price(data['price'])} so'm\n"
    if description:
        text += f"📝 Ta'rif: {description}"
    
    await message.answer(text, parse_mode="Markdown")
    await state.clear()

# Mahsulotni tahrirlash
@router.callback_query(F.data.startswith("edit_product_"))
async def edit_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q.", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, emoji, price, photo, description, is_active FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        await callback.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return
    
    name, emoji, price, photo, description, is_active = product
    status = "✅ Faol" if is_active else "❌ Nofaol"
    
    text = f"✏️ *Mahsulotni tahrirlash*\n\n"
    text += f"{emoji} *{name}*\n"
    text += f"💰 Narxi: {format_price(price)} so'm\n"
    text += f"📝 Ta'rif: {description or 'Kiritilmagan'}\n"
    text += f"📊 Holati: {status}\n\n"
    text += f"Nima o'zgartirmoqchisiz?"
    
    await callback.message.edit_text(
        text,
        reply_markup=edit_product_keyboard(product_id),
        parse_mode="Markdown"
    )
    await callback.answer()

# Mahsulot nomini o'zgartirish
@router.callback_query(F.data.startswith("edit_name_"))
async def edit_product_name(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id, field='name')
    await callback.message.edit_text("📝 Yangi nomni kiriting:")
    await state.set_state(EditProductStates.new_value)
    await callback.answer()

# Mahsulot emoji o'zgartirish
@router.callback_query(F.data.startswith("edit_emoji_"))
async def edit_product_emoji(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id, field='emoji')
    await callback.message.edit_text("🎨 Yangi emoji kiriting:")
    await state.set_state(EditProductStates.new_value)
    await callback.answer()

# Mahsulot narxini o'zgartirish
@router.callback_query(F.data.startswith("edit_price_"))
async def edit_product_price(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id, field='price')
    await callback.message.edit_text("💰 Yangi narxni kiriting (faqat raqam):")
    await state.set_state(EditProductStates.new_value)
    await callback.answer()

# Mahsulot rasmini o'zgartirish
@router.callback_query(F.data.startswith("edit_photo_"))
async def edit_product_photo(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id, field='photo')
    await callback.message.edit_text("🖼 Yangi rasm URL manzilini kiriting:")
    await state.set_state(EditProductStates.new_value)
    await callback.answer()

# Mahsulot ta'rifini o'zgartirish
@router.callback_query(F.data.startswith("edit_desc_"))
async def edit_product_desc(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id, field='description')
    await callback.message.edit_text("📝 Yangi ta'rifni kiriting:")
    await state.set_state(EditProductStates.new_value)
    await callback.answer()

# Yangi qiymatni saqlash
@router.message(EditProductStates.new_value)
async def save_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    field = data['field']
    new_value = message.text.strip()
    
    # Narx bo'lsa int ga o'tkazish
    if field == 'price':
        try:
            new_value = int(new_value)
        except ValueError:
            await message.answer("❌ Narx faqat raqamdan iborat bo'lishi kerak. Qaytadan kiriting:")
            return
    
    # Ma'lumotlar bazasini yangilash
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE products SET {field}=? WHERE id=?", (new_value, product_id))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ {field.capitalize()} muvaffaqiyatli o'zgartirildi!")
    await state.clear()

# Mahsulot faolligini o'zgartirish
@router.callback_query(F.data.startswith("toggle_active_"))
async def toggle_product_active(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q.", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM products WHERE id=?", (product_id,))
    is_active = cursor.fetchone()[0]
    new_status = 0 if is_active else 1
    cursor.execute("UPDATE products SET is_active=? WHERE id=?", (new_status, product_id))
    conn.commit()
    conn.close()
    
    status_text = "faollashtirildi" if new_status else "nofaol qilindi"
    await callback.answer(f"✅ Mahsulot {status_text}!", show_alert=True)
    
    # Qayta ko'rsatish
    await edit_product(callback)

# Mahsulotni o'chirish
@router.callback_query(F.data.startswith("delete_product_"))
async def delete_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q.", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    
    await callback.message.edit_text("🗑 Mahsulot o'chirildi!")
    await callback.answer()

# Mahsulotlar boshqaruviga qaytish
@router.callback_query(F.data == "products_management")
async def back_to_products_management(callback: CallbackQuery):
    await callback.message.edit_text(
        "🍽 *Mahsulotlar boshqaruvi*\n\nTahrirlash uchun mahsulotni tanlang:",
        reply_markup=products_management_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== MENU VA SAVAT ====================

# Menyu ko'rsatish
@router.message(F.text == "🍽 Menyu")
async def show_menu(message: Message):
    text = "🍽 *Bizning menyu:*\n\nKerakli mahsulotni tanlang:"
    await message.answer(text, reply_markup=menu_keyboard(), parse_mode="Markdown")

# Mahsulot tanlash
@router.callback_query(F.data.startswith("item_"))
async def show_item(callback: CallbackQuery):
    item_id = callback.data.split("_", 1)[1]
    MENU = get_products()
    
    if item_id not in MENU:
        await callback.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return
    
    item = MENU[item_id]
    
    text = f"*{item['name']}*\n\n"
    if item.get('description'):
        text += f"📝 {item['description']}\n\n"
    text += f"💰 Narxi: {format_price(item['price'])} so'm\n\nNechta buyurtma berasiz?"
    
    try:
        await callback.message.edit_text(text, reply_markup=item_keyboard(item_id), parse_mode="Markdown")
    except:
        await callback.message.answer(text, reply_markup=item_keyboard(item_id), parse_mode="Markdown")
    
    await callback.answer()

# Savatga qo'shish
@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split("_", 1)[1]
    MENU = get_products()
    
    if item_id not in MENU:
        await callback.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return
    
    cart = get_cart(user_id)
    
    if item_id in cart:
        cart[item_id] += 1
    else:
        cart[item_id] = 1
    
    item = MENU[item_id]
    await callback.answer(f"✅ {item['name']} savatga qo'shildi! ({cart[item_id]} ta)", show_alert=True)

# Miqdorni oshirish
@router.callback_query(F.data.startswith("increase_"))
async def increase_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split("_", 1)[1]
    cart = get_cart(user_id)
    
    if item_id in cart:
        cart[item_id] += 1
    else:
        cart[item_id] = 1
    
    await callback.answer(f"➕ Miqdor: {cart[item_id]} ta")

# Miqdorni kamaytirish
@router.callback_query(F.data.startswith("decrease_"))
async def decrease_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split("_", 1)[1]
    cart = get_cart(user_id)
    
    if item_id in cart and cart[item_id] > 0:
        cart[item_id] -= 1
        if cart[item_id] == 0:
            del cart[item_id]
        await callback.answer(f"➖ Miqdor: {cart.get(item_id, 0)} ta")
    else:
        await callback.answer("❌ Savat bo'sh", show_alert=True)

# Orqaga - menuga
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    text = "🍽 *Bizning menyu:*\n\nKerakli mahsulotni tanlang:"
    await callback.message.edit_text(text, reply_markup=menu_keyboard(), parse_mode="Markdown")
    await callback.answer()

# Savat ko'rsatish
@router.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = get_cart(user_id)
    MENU = get_products()
    
    if not cart:
        await message.answer("🛒 Savatingiz bo'sh.\n\n🍽 Menyu bo'limidan mahsulot tanlang.")
        return
    
    text = "🛒 *Savatingiz:*\n\n"
    total = 0
    
    for item_id, quantity in list(cart.items()):
        if item_id in MENU:
            item = MENU[item_id]
            item_total = item["price"] * quantity
            total += item_total
            text += f"{item['name']} x{quantity} = {format_price(item_total)} so'm\n"
        else:
            # Mahsulot o'chirilgan bo'lsa savatdan olib tashlash
            del cart[item_id]
    
    if not cart:
        await message.answer("🛒 Savatingiz bo'sh.\n\n🍽 Menyu bo'limidan mahsulot tanlang.")
        return
    
    text += f"\n🚚 Yetkazib berish: {format_price(DELIVERY_PRICE)} so'm"
    text += f"\n\n💰 *Jami: {format_price(total + DELIVERY_PRICE)} so'm*"
    
    await message.answer(text, reply_markup=cart_keyboard(user_id), parse_mode="Markdown")

# Savat ichida miqdorni oshirish
@router.callback_query(F.data.startswith("cart_increase_"))
async def cart_increase(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split("_", 2)[2]
    cart = get_cart(user_id)
    MENU = get_products()
    
    if item_id not in MENU:
        await callback.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return
    
    cart[item_id] += 1
    
    text = "🛒 *Savatingiz:*\n\n"
    total = 0
    
    for item_id_loop, quantity in cart.items():
        if item_id_loop in MENU:
            item = MENU[item_id_loop]
            item_total = item["price"] * quantity
            total += item_total
            text += f"{item['name']} x{quantity} = {format_price(item_total)} so'm\n"
    
    text += f"\n🚚 Yetkazib berish: {format_price(DELIVERY_PRICE)} so'm"
    text += f"\n\n💰 *Jami: {format_price(total + DELIVERY_PRICE)} so'm*"
    
    await callback.message.edit_text(text, reply_markup=cart_keyboard(user_id), parse_mode="Markdown")
    await callback.answer("➕ Miqdor oshirildi")

# Savat ichida miqdorni kamaytirish
@router.callback_query(F.data.startswith("cart_decrease_"))
async def cart_decrease(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split("_", 2)[2]
    cart = get_cart(user_id)
    MENU = get_products()
    
    if cart[item_id] > 1:
        cart[item_id] -= 1
    else:
        del cart[item_id]
    
    if not cart:
        await callback.message.edit_text("🛒 Savatingiz bo'sh.\n\n🍽 Menyu bo'limidan mahsulot tanlang.")
        await callback.answer()
        return
    
    text = "🛒 *Savatingiz:*\n\n"
    total = 0
    
    for item_id_loop, quantity in cart.items():
        if item_id_loop in MENU:
            item = MENU[item_id_loop]
            item_total = item["price"] * quantity
            total += item_total
            text += f"{item['name']} x{quantity} = {format_price(item_total)} so'm\n"
    
    text += f"\n🚚 Yetkazib berish: {format_price(DELIVERY_PRICE)} so'm"
    text += f"\n\n💰 *Jami: {format_price(total + DELIVERY_PRICE)} so'm*"
    
    await callback.message.edit_text(text, reply_markup=cart_keyboard(user_id), parse_mode="Markdown")
    await callback.answer("➖ Miqdor kamaytirildi")

# Savatni tozalash
@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_carts[user_id] = {}
    
    await callback.message.edit_text("🗑 Savat tozalandi.\n\n🍽 Menyu bo'limidan mahsulot tanlang.")
    await callback.answer("✅ Savat tozalandi")

# Buyurtma berish - telefon so'rash
@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📞 *Telefon raqamingizni kiriting:*\n\nMasalan: +998901234567", parse_mode="Markdown")
    await state.set_state(OrderStates.phone)
    await callback.answer()

# Telefon qabul qilish
@router.message(OrderStates.phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    
    if len(phone) < 9:
        await message.answer("❌ Telefon raqam noto'g'ri. Qaytadan kiriting:\n\nMasalan: +998901234567")
        return
    
    await state.update_data(phone=phone)
    await message.answer("📍 *Manzilni kiriting:*\n\nMasalan: Toshkent sh., Chilonzor tumani, 12-kvartal", parse_mode="Markdown")
    await state.set_state(OrderStates.address)

# Manzil qabul qilish
@router.message(OrderStates.address)
async def process_address(message: Message, state: FSMContext):
    address = message.text.strip()
    
    if len(address) < 5:
        await message.answer("❌ Manzil juda qisqa. Qaytadan kiriting:")
        return
    
    await state.update_data(address=address)
    await message.answer("💳 *To'lov usulini tanlang:*", reply_markup=payment_keyboard(), parse_mode="Markdown")
    await state.set_state(OrderStates.payment)

# To'lov usulini tanlash
@router.callback_query(OrderStates.payment, F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    payment_method = callback.data.split("_")[1].title()
    
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    data = await state.get_data()
    phone = data.get("phone")
    address = data.get("address")
    
    cart = get_cart(user_id)
    MENU = get_products()
    
    # Buyurtma tafsilotlari
    items_text = ""
    total = 0
    
    for item_id, quantity in cart.items():
        if item_id in MENU:
            item = MENU[item_id]
            item_total = item["price"] * quantity
            total += item_total
            items_text += f"{item['name']} x{quantity}, "
    
    items_text = items_text.rstrip(", ")
    total_with_delivery = total + DELIVERY_PRICE
    
    # Ma'lumotlar bazasiga saqlash
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, username, phone, address, items, total_price, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, phone, address, items_text, total_with_delivery, payment_method))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Foydalanuvchiga tasdiqlash
    confirmation_text = f"✅ *Buyurtma qabul qilindi!*\n\n"
    confirmation_text += f"📋 Buyurtma №{order_id}\n\n"
    confirmation_text += f"🛒 *Mahsulotlar:*\n"
    
    for item_id, quantity in cart.items():
        if item_id in MENU:
            item = MENU[item_id]
            item_total = item["price"] * quantity
            confirmation_text += f"{item['name']} x{quantity} = {format_price(item_total)} so'm\n"
    
    confirmation_text += f"\n🚚 Yetkazib berish: {format_price(DELIVERY_PRICE)} so'm"
    confirmation_text += f"\n💰 *Jami: {format_price(total_with_delivery)} so'm*"
    confirmation_text += f"\n\n📞 Telefon: {phone}"
    confirmation_text += f"\n📍 Manzil: {address}"
    confirmation_text += f"\n💳 To'lov: {payment_method}"
    confirmation_text += f"\n\n⏳ Buyurtmangiz tez orada yetkazib beriladi!"
    
    await callback.message.edit_text(confirmation_text, parse_mode="Markdown")
    
    # Adminga xabar
    admin_text = f"🔔 *YANGI BUYURTMA №{order_id}*\n\n"
    admin_text += f"👤 Mijoz: @{username}\n"
    admin_text += f"📞 Telefon: {phone}\n"
    admin_text += f"📍 Manzil: {address}\n\n"
    admin_text += f"🛒 *Mahsulotlar:*\n{items_text}\n\n"
    admin_text += f"💰 *Jami: {format_price(total_with_delivery)} so'm*"
    admin_text += f"\n💳 To'lov: {payment_method}"
    
    try:
        await bot.send_message(ADMIN_ID, admin_text, 
                             reply_markup=admin_order_keyboard(order_id, "Yangi"),
                             parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Admin xabar yuborishda xatolik: {e}")
    
    # Savatni tozalash
    user_carts[user_id] = {}
    await state.clear()
    await callback.answer("✅ Buyurtma muvaffaqiyatli yuborildi!", show_alert=True)

# Ma'lumot
@router.message(F.text == "ℹ️ Ma'lumot")
async def show_info(message: Message):
    text = "ℹ️ *FastFood Express*\n\n"
    text += "🍕 Eng mazali fast food yetkazib berish xizmati!\n\n"
    text += "📞 Telefon: +998 90 123 45 67\n"
    text += "⏰ Ish vaqti: 09:00 - 23:00\n"
    text += "🚚 Yetkazib berish: 30-40 daqiqa\n"
    text += "💰 Yetkazib berish narxi: 10,000 so'm\n\n"
    text += "📱 Buyurtma berish uchun 🍽 Menyu tugmasini bosing!"
    
    await message.answer(text, parse_mode="Markdown")

# ==================== ADMIN PANEL ====================

# Admin: Barcha buyurtmalar
@router.message(F.text == "📊 Barcha buyurtmalar")
async def show_all_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders ORDER BY id DESC LIMIT 10')
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("📊 Hali buyurtmalar yo'q.")
        return
    
    text = "📊 *So'nggi 10 ta buyurtma:*\n\n"
    
    for order in orders:
        order_id = order[0]
        username = order[2]
        total_price = order[6]
        status = order[8]
        created_at = order[12]
        
        text += f"📋 №{order_id} | @{username}\n"
        text += f"💰 {format_price(total_price)} so'm | {ORDER_STATUS.get(status, status)}\n"
        text += f"📅 {created_at}\n\n"
    
    await message.answer(text, parse_mode="Markdown")

# Admin: Yangi buyurtmalar
@router.message(F.text == "🆕 Yangi buyurtmalar")
async def show_new_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE status='Yangi' ORDER BY id DESC")
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("🆕 Yangi buyurtmalar yo'q.")
        return
    
    for order in orders:
        order_id = order[0]
        username = order[2]
        phone = order[3]
        address = order[4]
        items = order[5]
        total_price = order[6]
        payment_method = order[7]
        
        text = f"🆕 *YANGI BUYURTMA №{order_id}*\n\n"
        text += f"👤 Mijoz: @{username}\n"
        text += f"📞 Telefon: {phone}\n"
        text += f"📍 Manzil: {address}\n\n"
        text += f"🛒 *Mahsulotlar:*\n{items}\n\n"
        text += f"💰 *Jami: {format_price(total_price)} so'm*\n"
        text += f"💳 To'lov: {payment_method}"
        
        await message.answer(text, reply_markup=admin_order_keyboard(order_id, "Yangi"), parse_mode="Markdown")

# Admin: Buyurtmani qabul qilish
@router.callback_query(F.data.startswith("admin_accept_"))
async def admin_accept_order(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q.", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Qabul qilindi', accepted_at=? WHERE id=?", 
                  (datetime.now(), order_id))
    conn.commit()
    
    # Mijozga xabar
    cursor.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
    user_id = cursor.fetchone()[0]
    conn.close()
    
    try:
        await bot.send_message(
            user_id, 
            f"✅ *Buyurtma №{order_id} qabul qilindi!*\n\n"
            f"🚚 Buyurtmangiz tez orada yo'lga chiqadi.\n"
            f"⏰ Taxminiy yetkazib berish vaqti: 30-40 daqiqa\n\n"
            f"Sabr qilganingiz uchun rahmat! 😊",
            parse_mode="Markdown"
        )
        logger.info(f"Mijozga qabul qilish xabari yuborildi: User ID {user_id}")
    except Exception as e:
        logger.error(f"Mijozga xabar yuborishda xatolik: {e}")
    
    text = callback.message.text.replace("🆕 YANGI", "✅ QABUL QILINDI")
    await callback.message.edit_text(text, 
                                    reply_markup=admin_order_keyboard(order_id, "Qabul qilindi"),
                                    parse_mode="Markdown")
    await callback.answer("✅ Buyurtma qabul qilindi va mijozga xabar yuborildi!")

# Admin: Kuryerga topshirish
@router.callback_query(F.data.startswith("admin_assign_"))
async def admin_assign_courier(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q.", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[2])
    
    await callback.message.edit_text(
        f"🚚 Buyurtma №{order_id} uchun kuryerni tanlang:",
        reply_markup=select_courier_keyboard(order_id)
    )
    await callback.answer()

# Kuryerni tayinlash
@router.callback_query(F.data.startswith("assign_courier_"))
async def assign_courier_to_order(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q.", show_alert=True)
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[2])
    courier_id = int(parts[3])
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    
    # Kuryer ma'lumotlarini olish yoki yaratish
    cursor.execute("SELECT full_name, username FROM couriers WHERE id=?", (courier_id,))
    courier = cursor.fetchone()
    
    if not courier:
        cursor.execute('''
            INSERT INTO couriers (id, username, full_name) 
            VALUES (?, ?, ?)
        ''', (courier_id, "kuryer", "Kuryer"))
        conn.commit()
        courier_name = "Kuryer"
        courier_username = "kuryer"
        logger.info(f"Yangi kuryer bazaga qo'shildi: ID {courier_id}")
    else:
        courier_name = courier[0]
        courier_username = courier[1]
    
    # Buyurtma tafsilotlarini olish
    cursor.execute("SELECT user_id, username, phone, address, items, total_price, payment_method, created_at FROM orders WHERE id=?", (order_id,))
    order_data = cursor.fetchone()
    
    if not order_data:
        await callback.answer("❌ Buyurtma topilmadi!", show_alert=True)
        conn.close()
        return
    
    user_id, username, phone, address, items, total_price, payment_method, created_at = order_data
    
    # Buyurtmani yangilash
    cursor.execute("""
        UPDATE orders 
        SET status='Kuryerda', courier_id=?, courier_name=? 
        WHERE id=?
    """, (courier_id, courier_name, order_id))
    
    # Kuryer statistikasini yangilash
    cursor.execute("UPDATE couriers SET total_orders=total_orders+1 WHERE id=?", (courier_id,))
    
    conn.commit()
    conn.close()
    
    # Mijozga xabar
    try:
        await bot.send_message(user_id, 
            f"🚚 *Buyurtma №{order_id} kuryerga topshirildi!*\n\n"
            f"👤 Kuryer: {courier_name}\n"
            f"📞 Kuryer tez orada siz bilan bog'lanadi.\n\n"
            f"⏰ Buyurtmangiz yo'lda!",
            parse_mode="Markdown"
        )
        logger.info(f"Mijozga kuryer topshirilish xabari yuborildi: User ID {user_id}")
    except Exception as e:
        logger.error(f"Mijozga xabar yuborishda xatolik: {e}")
    
    # Kuryerga BATAFSIL xabar
    courier_text = f"🔔 *YANGI BUYURTMA TAYINLANDI!*\n\n"
    courier_text += f"━━━━━━━━━━━━━━━━━━━━\n"
    courier_text += f"📋 *Buyurtma №{order_id}*\n"
    courier_text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    
    courier_text += f"👤 *MIJOZ MA'LUMOTLARI:*\n"
    courier_text += f"├ Ism: @{username}\n"
    courier_text += f"├ 📞 Telefon: *{phone}*\n"
    courier_text += f"└ 📍 Manzil: *{address}*\n\n"
    
    courier_text += f"🛒 *BUYURTMA TARKIBI:*\n"
    courier_text += f"{items}\n\n"
    
    courier_text += f"💰 *TO'LOV MA'LUMOTLARI:*\n"
    courier_text += f"├ Summa: *{format_price(total_price)} so'm*\n"
    courier_text += f"└ To'lov usuli: *{payment_method}*\n\n"
    
    courier_text += f"📅 Buyurtma vaqti: {created_at}\n\n"
    courier_text += f"━━━━━━━━━━━━━━━━━━━━\n"
    courier_text += f"⚡️ *Mijozga qo'ng'iroq qiling va buyurtmani yetkazib bering!*"
    
    try:
        await bot.send_message(
            courier_id, 
            courier_text, 
            reply_markup=courier_order_keyboard(order_id, "Kuryerda"),
            parse_mode="Markdown"
        )
        logger.info(f"Kuryerga batafsil xabar yuborildi: Courier ID {courier_id}")
        
        await callback.message.edit_text(
            f"✅ *Buyurtma №{order_id} kuryerga topshirildi!*\n\n"
            f"👤 Kuryer: {courier_name} (@{courier_username})\n"
            f"📱 Kuryer ID: {courier_id}\n\n"
            f"✅ Kuryerga buyurtma haqida to'liq ma'lumot yuborildi.\n"
            f"✅ Mijozga ham xabar yuborildi.",
            parse_mode="Markdown"
        )
        await callback.answer("✅ Kuryer tayinlandi va xabardor qilindi!", show_alert=True)
        
    except Exception as e:
        logger.error(f"Kuryerga xabar yuborishda xatolik: {e}")
        await callback.message.edit_text(
            f"⚠️ *Buyurtma №{order_id} kuryer {courier_name} ga tayinlandi.*\n\n"
            f"❌ *Xatolik:* Kuryerga xabar yuborishda muammo:\n{str(e)}\n\n"
            f"📋 Kuryer ID: {courier_id}\n"
            f"⚠️ Kuryer botni ishga tushirganiga ishonch hosil qiling (/start).",
            parse_mode="Markdown"
        )
        await callback.answer(f"⚠️ Xatolik: {str(e)}", show_alert=True)

# Admin: Buyurtmani bekor qilish
@router.callback_query(F.data.startswith("admin_cancel_"))
async def admin_cancel_order(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q.", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Bekor qilindi' WHERE id=?", (order_id,))
    conn.commit()
    
    # Mijozga xabar
    cursor.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
    user_id = cursor.fetchone()[0]
    conn.close()
    
    try:
        await bot.send_message(user_id, 
            f"❌ *Buyurtma №{order_id} bekor qilindi.*\n\n"
            f"Sababi haqida tez orada aloqaga chiqamiz.\n"
            f"Noqulaylik uchun uzr so'raymiz.",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.message.edit_text(f"❌ Buyurtma №{order_id} bekor qilindi.")
    await callback.answer("❌ Buyurtma bekor qilindi!")

# Admin: Kuryerlar ro'yxati
@router.message(F.text == "👥 Kuryerlar")
async def show_couriers(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM couriers ORDER BY total_orders DESC')
    couriers = cursor.fetchall()
    conn.close()
    
    if not couriers:
        text = "👥 *Kuryerlar ro'yxati:*\n\n"
        text += "Hozircha kuryerlar yo'q.\n\n"
        text += "Kuryer qo'shish uchun:\n"
        text += "1. Kuryer Telegram ID sini oling\n"
        text += "2. Bot kodida COURIER_IDS ga qo'shing"
    else:
        text = "👥 *Kuryerlar ro'yxati:*\n\n"
        for courier in couriers:
            courier_id, username, full_name, phone, is_active, total_orders, created_at = courier
            status = "✅ Aktiv" if is_active else "❌ Nofaol"
            text += f"👤 {full_name} (@{username})\n"
            text += f"ID: {courier_id}\n"
            text += f"📦 Buyurtmalar: {total_orders}\n"
            text += f"{status}\n\n"
    
    await message.answer(text, parse_mode="Markdown")

# Admin: Statistika
@router.message(F.text == "📈 Statistika")
async def show_statistics(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    
    # Umumiy statistika
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Yangi'")
    new_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Kuryerda'")
    delivery_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Yetkazildi'")
    delivered_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE status='Yetkazildi'")
    total_revenue = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM couriers WHERE is_active=1")
    active_couriers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE is_active=1")
    active_products = cursor.fetchone()[0]
    
    conn.close()
    
    text = "📈 *STATISTIKA*\n\n"
    text += f"📦 Jami buyurtmalar: {total_orders}\n"
    text += f"🆕 Yangi: {new_orders}\n"
    text += f"🚚 Yetkazilmoqda: {delivery_orders}\n"
    text += f"✅ Yetkazildi: {delivered_orders}\n\n"
    text += f"💰 Umumiy daromad: {format_price(total_revenue)} so'm\n\n"
    text += f"👥 Aktiv kuryerlar: {active_couriers}\n"
    text += f"🍽 Aktiv mahsulotlar: {active_products}"
    
    await message.answer(text, parse_mode="Markdown")

# ==================== KURYER PANEL ====================

# Kuryer: Aktiv buyurtmalar
@router.message(F.text == "📋 Aktiv buyurtmalar")
async def courier_active_orders(message: Message):
    if not is_courier(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    courier_id = message.from_user.id
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE courier_id=? AND status='Kuryerda' 
        ORDER BY id DESC
    """, (courier_id,))
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("📋 Sizda hozir aktiv buyurtmalar yo'q.\n\n⏳ Yangi buyurtmalar kelishini kutamiz!")
        return
    
    await message.answer(f"📋 *Sizda {len(orders)} ta aktiv buyurtma bor:*", parse_mode="Markdown")
    
    for order in orders:
        order_id = order[0]
        user_id = order[1]
        username = order[2]
        phone = order[3]
        address = order[4]
        items = order[5]
        total_price = order[6]
        payment_method = order[7]
        created_at = order[12]
        accepted_at = order[13]
        
        text = f"🚚 *BUYURTMA №{order_id}*\n\n"
        text += f"👤 Mijoz: @{username}\n"
        text += f"📞 Telefon: {phone}\n"
        text += f"📍 Manzil: {address}\n\n"
        text += f"🛒 *Mahsulotlar:*\n{items}\n\n"
        text += f"💰 *Jami: {format_price(total_price)} so'm*\n"
        text += f"💳 To'lov usuli: {payment_method}\n\n"
        text += f"📅 Buyurtma vaqti: {created_at}\n"
        if accepted_at:
            text += f"✅ Qabul qilingan: {accepted_at}\n"
        text += f"\n⏰ Mijozga yetkazib bering!"
        
        await message.answer(text, reply_markup=courier_order_keyboard(order_id, "Kuryerda"), parse_mode="Markdown")

# Kuryer: Mening buyurtmalarim va Oddiy foydalanuvchi buyurtmalari
@router.message(F.text == "📦 Mening buyurtmalarim")
async def courier_my_orders(message: Message):
    user_id = message.from_user.id
    
    if is_courier(user_id):
        # Kuryer uchun - barcha buyurtmalarni ko'rsatish
        conn = sqlite3.connect('fastfood.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM orders 
            WHERE courier_id=? 
            ORDER BY id DESC LIMIT 10
        """, (user_id,))
        orders = cursor.fetchall()
        conn.close()
        
        if not orders:
            await message.answer("📦 Sizda hali buyurtmalar yo'q.")
            return
        
        text = f"📦 *Sizning so'nggi 10 ta buyurtmalaringiz:*\n\n"
        
        for order in orders:
            order_id = order[0]
            username = order[2]
            phone = order[3]
            address = order[4]
            items = order[5]
            total_price = order[6]
            status = order[8]
            created_at = order[12]
            delivered_at = order[14]
            
            text += f"━━━━━━━━━━━━━━━━\n"
            text += f"📋 *Buyurtma №{order_id}*\n"
            text += f"👤 Mijoz: @{username}\n"
            text += f"📞 Tel: {phone}\n"
            text += f"📍 Manzil: {address}\n"
            text += f"🛒 Mahsulotlar: {items}\n"
            text += f"💰 Summa: {format_price(total_price)} so'm\n"
            text += f"📊 Status: {ORDER_STATUS.get(status, status)}\n"
            text += f"📅 Qabul qilingan: {created_at}\n"
            if delivered_at:
                text += f"✅ Yetkazilgan: {delivered_at}\n"
            text += "\n"
        
        await message.answer(text, parse_mode="Markdown")
    else:
        # Oddiy foydalanuvchi uchun
        conn = sqlite3.connect('fastfood.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 5', (user_id,))
        orders = cursor.fetchall()
        conn.close()
        
        if not orders:
            await message.answer("📦 Sizda hali buyurtmalar yo'q.")
            return
        
        text = "📦 *Sizning buyurtmalaringiz:*\n\n"
        
        for order in orders:
            order_id = order[0]
            total_price = order[6]
            status = order[8]
            created_at = order[12]
            
            text += f"📋 Buyurtma №{order_id}\n"
            text += f"💰 {format_price(total_price)} so'm\n"
            text += f"📍 Status: {ORDER_STATUS.get(status, status)}\n"
            text += f"📅 {created_at}\n\n"
        
        await message.answer(text, parse_mode="Markdown")

# Kuryer: Buyurtmani yetkazib berish
@router.callback_query(F.data.startswith("courier_delivered_"))
async def courier_deliver_order(callback: CallbackQuery):
    if not is_courier(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q.", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Yetkazildi', delivered_at=? WHERE id=?", 
                  (datetime.now(), order_id))
    conn.commit()
    
    # Mijozga xabar
    cursor.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
    user_id = cursor.fetchone()[0]
    conn.close()
    
    try:
        await bot.send_message(user_id, 
            f"✅ *Buyurtma №{order_id} muvaffaqiyatli yetkazib berildi!*\n\n"
            f"Bizni tanlaganingiz uchun rahmat! 😊\n"
            f"Yoqimli ishtaha! 🍕",
            parse_mode="Markdown"
        )
    except:
        pass
    
    # Adminga xabar
    try:
        await bot.send_message(ADMIN_ID, 
            f"✅ *Buyurtma №{order_id} yetkazib berildi!*\n"
            f"Kuryer: {callback.from_user.first_name}",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.message.edit_text(f"✅ Buyurtma №{order_id} muvaffaqiyatli yetkazib berildi!")
    await callback.answer("✅ Ajoyib! Buyurtma yetkazib berildi!", show_alert=True)

# Kuryer: Mijozga qo'ng'iroq
@router.callback_query(F.data.startswith("courier_call_"))
async def courier_call_customer(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM orders WHERE id=?", (order_id,))
    phone = cursor.fetchone()[0]
    conn.close()
    
    await callback.answer(f"📞 Mijoz telefoni: {phone}", show_alert=True)

# Kuryer: Statistika
@router.message(F.text == "📊 Mening statistikam")
async def courier_statistics(message: Message):
    if not is_courier(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    courier_id = message.from_user.id
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT total_orders FROM couriers WHERE id=?", (courier_id,))
    total_orders = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE courier_id=? AND status='Kuryerda'", (courier_id,))
    active_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE courier_id=? AND status='Yetkazildi'", (courier_id,))
    delivered_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE courier_id=? AND status='Yetkazildi'", (courier_id,))
    total_delivered = cursor.fetchone()[0] or 0
    
    conn.close()
    
    text = f"📊 *MENING STATISTIKAM*\n\n"
    text += f"📦 Jami buyurtmalar: {total_orders}\n"
    text += f"🚚 Aktiv: {active_orders}\n"
    text += f"✅ Yetkazildi: {delivered_orders}\n\n"
    text += f"💰 Yetkazilgan summa: {format_price(total_delivered)} so'm"
    
    await message.answer(text, parse_mode="Markdown")

# Kuryer: Barcha buyurtmalarim
@router.message(F.text == "📦 Barcha buyurtmalarim")
async def courier_all_orders(message: Message):
    if not is_courier(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    courier_id = message.from_user.id
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE courier_id=? 
        ORDER BY id DESC LIMIT 20
    """, (courier_id,))
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("📦 Sizda hali buyurtmalar yo'q.")
        return
    
    # Har bir buyurtma uchun batafsil ma'lumot
    for order in orders:
        order_id = order[0]
        username = order[2]
        phone = order[3]
        address = order[4]
        items = order[5]
        total_price = order[6]
        payment_method = order[7]
        status = order[8]
        created_at = order[12]
        accepted_at = order[13]
        delivered_at = order[14]
        
        text = f"📦 *BUYURTMA №{order_id}*\n\n"
        text += f"👤 Mijoz: @{username}\n"
        text += f"📞 Telefon: {phone}\n"
        text += f"📍 Manzil: {address}\n\n"
        text += f"🛒 *Mahsulotlar:*\n{items}\n\n"
        text += f"💰 *Jami: {format_price(total_price)} so'm*\n"
        text += f"💳 To'lov: {payment_method}\n"
        text += f"📊 Status: {ORDER_STATUS.get(status, status)}\n\n"
        text += f"📅 Buyurtma vaqti: {created_at}\n"
        if accepted_at:
            text += f"✅ Qabul qilingan: {accepted_at}\n"
        if delivered_at:
            text += f"🎉 Yetkazilgan: {delivered_at}"
        
        # Status bo'yicha tugmalar
        if status == "Kuryerda":
            keyboard = courier_order_keyboard(order_id, status)
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📞 Mijozga qo'ng'iroq", callback_data=f"courier_call_{order_id}")]
            ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

# Kuryer: Yetkazilgan buyurtmalar
@router.message(F.text == "✅ Yetkazilgan buyurtmalar")
async def courier_delivered_orders(message: Message):
    if not is_courier(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q.")
        return
    
    courier_id = message.from_user.id
    
    conn = sqlite3.connect('fastfood.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE courier_id=? AND status='Yetkazildi' 
        ORDER BY delivered_at DESC LIMIT 15
    """, (courier_id,))
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("✅ Hali yetkazilgan buyurtmalar yo'q.")
        return
    
    await message.answer(f"✅ *Yetkazilgan buyurtmalar: {len(orders)} ta*", parse_mode="Markdown")
    
    for order in orders:
        order_id = order[0]
        username = order[2]
        phone = order[3]
        address = order[4]
        items = order[5]
        total_price = order[6]
        payment_method = order[7]
        created_at = order[12]
        delivered_at = order[14]
        
        text = f"✅ *BUYURTMA №{order_id}* (Yetkazildi)\n\n"
        text += f"👤 Mijoz: @{username}\n"
        text += f"📞 Telefon: {phone}\n"
        text += f"📍 Manzil: {address}\n\n"
        text += f"🛒 *Mahsulotlar:*\n{items}\n\n"
        text += f"💰 *Jami: {format_price(total_price)} so'm*\n"
        text += f"💳 To'lov: {payment_method}\n\n"
        text += f"📅 Qabul: {created_at}\n"
        text += f"🎉 Yetkazildi: {delivered_at}"
        
        await message.answer(text, parse_mode="Markdown")

# ==================== YORDAMCHI CALLBACK'LAR ====================

# Orqaga - asosiy menyu
@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("🏠 Asosiy menyu:", reply_markup=main_menu())
    await callback.answer()

# Admin asosiy menyu
@router.callback_query(F.data == "admin_main")
async def admin_main_callback(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("🏠 Admin panel:", reply_markup=admin_menu())
    await callback.answer()

# Orqaga - savat
@router.callback_query(F.data == "back_to_cart")
async def back_to_cart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    cart = get_cart(user_id)
    MENU = get_products()
    
    if not cart:
        await callback.message.edit_text("🛒 Savatingiz bo'sh.\n\n🍽 Menyu bo'limidan mahsulot tanlang.")
        await callback.answer()
        return
    
    text = "🛒 *Savatingiz:*\n\n"
    total = 0
    
    for item_id, quantity in cart.items():
        if item_id in MENU:
            item = MENU[item_id]
            item_total = item["price"] * quantity
            total += item_total
            text += f"{item['name']} x{quantity} = {format_price(item_total)} so'm\n"
    
    text += f"\n🚚 Yetkazib berish: {format_price(DELIVERY_PRICE)} so'm"
    text += f"\n\n💰 *Jami: {format_price(total + DELIVERY_PRICE)} so'm*"
    
    await callback.message.edit_text(text, reply_markup=cart_keyboard(user_id), parse_mode="Markdown")
    await callback.answer()

# Asosiy funksiya
async def main():
    try:
        init_db()
        dp.include_router(router)
        logger.info("✅ Bot ishga tushdi!")
        logger.info(f"Admin ID: {ADMIN_ID}")
        logger.info(f"Kuryerlar: {COURIER_IDS}")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot ishga tushirishda xatolik: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
