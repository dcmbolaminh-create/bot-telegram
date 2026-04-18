import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite
import secrets
import hashlib

# ================== CẤU HÌNH ==================
TOKEN = "8605647524:AAHJRuq9xHsg1bHP42_3Rahftc-no_a5GSQ"          # Thay bằng token thật
ADMIN_ID = 7549551030                   # Telegram ID admin
QR_FILE = "qr.png"                     # File QR code

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

DB_NAME = "orders.db"

# ================== API CONFIG ==================
GAME_APIS = {
    "sun_sicbo": {
        "name": "🌟 Sun Sicbo",
        "api": "https://toolgamebinhoi.site/sun-sicbo.php",
        "desc": "Dự đoán Sicbo Sunwin - Tỉ lệ cao"
    },
    "hit_md5": {
        "name": "🔥 Hit MD5",
        "api": "https://toolgamebinhoi.site/api-hitmd5.php",
        "desc": "Hitclub MD5 Algorithm"
    },
    "hit": {
        "name": "🎰 Hit Normal",
        "api": "https://toolgamebinhoi.site/api-hit.php",
        "desc": "Hitclub Standard"
    },
    "789": {
        "name": "🃏 789 Club",
        "api": "https://toolgamebinhoi.site/789.php",
        "desc": "789 Prediction"
    },
    "b52_md5": {
        "name": "♠️ B52 MD5",
        "api": "https://toolgamebinhoi.site/api-b52md5.php",
        "desc": "B52 MD5 Advanced"
    },
    "b52": {
        "name": "♦️ B52 Normal",
        "api": "https://toolgamebinhoi.site/api-b52.php",
        "desc": "B52 Standard"
    },
    "bcr": {
        "name": "🀄 BCR (Baccarat)",
        "api": "https://toolgamebinhoi.site/api-bcr.php?ban={room}",
        "desc": "Baccarat Room Prediction"
    },
    "taixiu_md5": {
        "name": "📈 Tài Xỉu MD5 Max789",
        "api": "https://max789-vip.onrender.com/taixiumd5",
        "desc": "Tài Xỉu MD5 VIP"
    },
    "taixiu_lc79": {
        "name": "📉 Tài Xỉu LC79",
        "api": "https://lc79-vip-1.onrender.com/taixiu",
        "desc": "Tài Xỉu LC79 VIP"
    },
}

# ================== DATABASE ==================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                package TEXT,
                price INTEGER,
                game_type TEXT DEFAULT 'all',
                activation_key TEXT,
                expiry_date TEXT,
                status TEXT DEFAULT 'pending',
                bill_file_id TEXT,
                created_at TEXT
            )
        """)
        await db.commit()
    logger.info("Database initialized successfully")

# ================== STATES ==================
class Payment(StatesGroup):
    waiting_bill = State()
    waiting_game_selection = State()

# ================== KEYBOARD ==================
def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Mua Gói Tool", callback_data="buy_package")],
        [InlineKeyboardButton(text="🛠 Thông Tin Tool & Game", callback_data="info_tool")],
        [InlineKeyboardButton(text="🔑 Kiểm tra Key của tôi", callback_data="check_key")],
        [InlineKeyboardButton(text="👨‍💼 Liên Hệ Admin", url="https://t.me/vanminh2603")]
    ])

def get_packages_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 Ngày - 35.000đ", callback_data="package_1d")],
        [InlineKeyboardButton(text="3 Ngày - 75.000đ", callback_data="package_3d")],
        [InlineKeyboardButton(text="1 Tuần - 120.000đ", callback_data="package_1w")],
        [InlineKeyboardButton(text="1 Tháng - 220.000đ", callback_data="package_1m")],
        [InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_to_start")]
    ])

def get_games_keyboard():
    keyboard = []
    for key, info in GAME_APIS.items():
        keyboard.append([InlineKeyboardButton(text=info["name"], callback_data=f"game_{key}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Quay lại", callback_data="buy_package")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ================== UTILS ==================
def generate_activation_key():
    return secrets.token_urlsafe(16).upper()

def get_expiry_date(days: int):
    return (datetime.now() + timedelta(days=days)).isoformat()

def get_package_days(package: str) -> int:
    mapping = {"1 Ngày": 1, "3 Ngày": 3, "1 Tuần": 7, "1 Tháng": 30}
    return mapping.get(package, 1)

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "<b>🤖 TOOL DỰ ĐOÁN TÀI XỈU CAO CẤP 2026</b>\n\n"
        "👤 Creator: @vanminh2603\n"
        "🔥 Thuật toán AI + MD5 + Pattern Recognition\n"
        "✅ Tỉ lệ thắng thực tế: <b>85-92%</b>\n"
        "🎮 Hỗ trợ: Sun Sicbo, Hit, B52, 789, BCR, Tài Xỉu MD5...\n\n"
        "Chọn chức năng bên dưới:",
        reply_markup=get_start_keyboard()
    )

@dp.callback_query(F.data == "info_tool")
async def show_info(callback: CallbackQuery):
    info_text = (
        "🛠 <b>THÔNG TIN TOOL 2026</b>\n\n"
        "• Dự đoán Tài/Xỉu, Sicbo, Baccarat siêu chính xác\n"
        "• Kết hợp AI + MD5 Hash + Historical Pattern\n"
        "• Hỗ trợ đầy đủ các game hot:\n"
        "   - Sun Sicbo\n"
        "   - Hit Club (MD5 & Normal)\n"
        "   - B52 (MD5 & Normal)\n"
        "   - 789 Club\n"
        "   - BCR\n"
        "   - Tài Xỉu Max789 & LC79\n\n"
        ".\n\n"
        "Liên hệ @vanminh2603 để được hướng dẫn sử dụng chi tiết."
    )
    await callback.message.edit_text(info_text, reply_markup=get_start_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "buy_package")
async def buy_package(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 <b>Chọn gói Tool bạn muốn mua:</b>",
        reply_markup=get_packages_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("package_"))
async def select_package(callback: CallbackQuery, state: FSMContext):
    packages = {
        "package_1d": ("1 Ngày", 35000),
        "package_3d": ("3 Ngày", 75000),
        "package_1w": ("1 Tuần", 120000),
        "package_1m": ("1 Tháng", 220000),
    }
    pkg_name, price = packages[callback.data]
    
    await state.update_data(package=pkg_name, price=price)
    
    await callback.message.edit_text(
        f"<b>Bạn đã chọn:</b> {pkg_name}\n"
        f"<b>Giá:</b> {price:,} VNĐ\n\n"
        "Vui lòng chọn game bạn muốn sử dụng (có thể chọn All sau khi kích hoạt):",
        reply_markup=get_games_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("game_"))
async def select_game(callback: CallbackQuery, state: FSMContext):
    game_key = callback.data.replace("game_", "")
    game_info = GAME_APIS.get(game_key, {"name": "Tất cả game", "desc": ""})
    
    await state.update_data(game_type=game_key, game_name=game_info["name"])
    
    data = await state.get_data()
    await callback.message.edit_text(
        f"<b>✅ Đã chọn:</b>\n"
        f"Gói: {data['package']}\n"
        f"Game: {game_info['name']}\n"
        f"Giá: {data['price']:,} VNĐ\n\n"
        "💳 Quét mã QR để thanh toán.\n"
        "Sau khi chuyển khoản, gửi bill để admin duyệt nhanh.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tôi đã thanh toán - Gửi Bill", callback_data="send_bill")],
            [InlineKeyboardButton(text="🔙 Chọn lại game", callback_data="buy_package")]
        ])
    )
    
    qr = FSInputFile(QR_FILE)
    await callback.message.answer_photo(photo=qr, caption="📸 Quét QR để chuyển khoản")
    await callback.answer()

@dp.callback_query(F.data == "send_bill")
async def request_bill(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(
        f"📤 Gửi ảnh bill thanh toán cho gói <b>{data.get('package')}</b> - Game: <b>{data.get('game_name', 'All')}</b>\n\n"
        "Admin sẽ kiểm tra và gửi key kích hoạt trong thời gian sớm nhất."
    )
    await state.set_state(Payment.waiting_bill)
    await callback.answer()

@dp.message(Payment.waiting_bill, F.photo)
async def receive_bill(message: Message, state: FSMContext):
    data = await state.get_data()
    bill_file_id = message.photo[-1].file_id
    game_type = data.get("game_type", "all")
    
    activation_key = generate_activation_key()
    days = get_package_days(data['package'])
    expiry = get_expiry_date(days)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT INTO orders 
               (user_id, username, package, price, game_type, activation_key, expiry_date, bill_file_id, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (message.from_user.id, message.from_user.username or "NoUsername",
             data['package'], data['price'], game_type, activation_key, expiry,
             bill_file_id, datetime.now().isoformat())
        )
        await db.commit()
        
        cursor = await db.execute("SELECT last_insert_rowid()")
        order_id = (await cursor.fetchone())[0]

    await message.answer("✅ Bill đã được nhận! Đơn hàng đang chờ admin duyệt.")

    # Thông báo admin
    await bot.send_message(
        ADMIN_ID,
        f"🛎 <b>ĐƠN HÀNG MỚI CẦN DUYỆT</b>\n\n"
        f"Order ID: <code>{order_id}</code>\n"
        f"User: @{message.from_user.username} (ID: {message.from_user.id})\n"
        f"Gói: {data['package']}\n"
        f"Game: {data.get('game_name', 'All')}\n"
        f"Giá: {data['price']:,}đ\n"
        f"Key dự kiến: <code>{activation_key}</code>"
    )
    await bot.send_photo(ADMIN_ID, bill_file_id, caption=f"Bill Order #{order_id}")

    await state.clear()

@dp.message(Command("duyet"))
async def admin_approve(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Chỉ admin mới dùng lệnh này.")

    try:
        order_id = int(message.text.split()[1])
    except:
        return await message.answer("Cách dùng: /duyet <order_id>")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE orders SET status = 'approved' WHERE id = ?", (order_id,))
        await db.commit()
        
        cursor = await db.execute(
            "SELECT user_id, package, activation_key, game_type, expiry_date FROM orders WHERE id = ?", 
            (order_id,)
        )
        row = await cursor.fetchone()

    if row:
        user_id, package, key, game_type, expiry = row
        game_name = GAME_APIS.get(game_type, {}).get("name", "Tất cả game") if game_type != "all" else "Tất cả game"

        await bot.send_message(
            user_id,
            f"✅ <b>ĐƠN HÀNG #{order_id} ĐÃ ĐƯỢC DUYỆT!</b>\n\n"
            f"Gói: <b>{package}</b>\n"
            f"Game: <b>{game_name}</b>\n"
            f"<b>KEY KÍCH HOẠT:</b> <code>{key}</code>\n"
            f"Hạn sử dụng: {expiry[:10]}\n\n"
            f"Cách dùng:\n"
            f"1. Truy cập tool tương ứng\n"
            f"2. Mở DevTool (F12) → Tab Console hoặc Network\n"
            f"3. Nhập key vào ô bảo mật để hiển thị dự đoán\n"
            f"4. Tool sẽ tự động dự đoán với tỉ lệ cao.\n\n"
            f"Hỗ trợ: @vanminh2603"
        )
        await message.answer(f"✅ Đã duyệt Order #{order_id} và gửi key cho user.")
    else:
        await message.answer("❌ Không tìm thấy đơn hàng.")

@dp.callback_query(F.data == "check_key")
async def check_key(callback: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT package, activation_key, expiry_date, status FROM orders WHERE user_id = ? AND status = 'approved'",
            (callback.from_user.id,)
        )
        rows = await cursor.fetchall()

    if not rows:
        text = "❌ Bạn chưa có key kích hoạt nào. Vui lòng mua gói!"
    else:
        text = "<b>🔑 Các Key của bạn:</b>\n\n"
        for row in rows:
            text += f"• Gói: {row[0]}\n  Key: <code>{row[1]}</code>\n  Hạn: {row[2][:10]}\n\n"

    await callback.message.edit_text(text, reply_markup=get_start_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back_to_start")
async def back_start(callback: CallbackQuery):
    await callback.message.edit_text("Chọn chức năng:", reply_markup=get_start_keyboard())
    await callback.answer()

# ================== CHẠY BOT ==================
async def main():
    await init_db()
    logger.info("Bot Tool Dự Đoán Tài Xỉu 2026 đã khởi động...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
