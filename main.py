import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, ChatJoinRequestHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler

# --- KONFIGURASI ---
TOKEN = '8370842756:AAEbjHtrnZNPnduqGNl-mTyuVmE8iuNB4fE'
ADMIN_ID = 7655136272
GROUP_CHAT_ID = -1003649901491
YT_LINK = "https://youtu.be/fpCazjiKloU?si=MIq_fYenJdfBC3Hl"

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- KEYBOARD MENU ---

def get_main_menu():
    keyboard = [
        [KeyboardButton("📝 Registrasi"), KeyboardButton("❓ Bantuan")],
        [KeyboardButton("📊 Status Permintaan")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_upload_menu():
    # Menambahkan kembali tombol instruksi sesuai permintaan kamu
    keyboard = [
        [KeyboardButton("📸 Kirim Bukti Subscribe"), KeyboardButton("📸 Kirim Bukti Like")],
        [KeyboardButton("❌ Batal Registrasi")]
    ]
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        input_field_placeholder="Lampirkan foto bukti di sini..."
    )

def get_link_menu():
    keyboard = [
        [KeyboardButton("🔗 Request Link")],
        [KeyboardButton("🔙 Kembali ke Menu Utama")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- FUNGSI GENERATE LINK ---
async def generate_unique_link(context: ContextTypes.DEFAULT_TYPE, user_name):
    try:
        new_link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_CHAT_ID,
            name=f"Link {user_name}",
            creates_join_request=True
        )
        return new_link.invite_link
    except Exception as e:
        logger.error(f"Error link: {e}")
        return None

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    context.user_data.clear() 
    
    await update.message.reply_text(
        f"Halo <b>{user_name}</b>! 👋\nSilakan pilih menu <b>📝 Registrasi</b> untuk memulai.",
        reply_markup=get_main_menu(),
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text: return
    
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if "Registrasi" in text:
        context.user_data['proof_count'] = 0
        context.user_data['status'] = 'uploading_proofs'
        context.user_data['proof_completed'] = False
        
        msg = (
            "🔒 <b>MODE REGISTRASI AKTIF</b>\n\n"
            f"Silakan <b>Subscribe & Like</b> di sini:\n{YT_LINK}\n\n"
            "📸 <b>TUGAS:</b>\n"
            "Klik ikon penjepit kertas (attachment) dan kirimkan <b>2 Screenshot</b> bukti ke sini."
        )
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_upload_menu(), disable_web_page_preview=True)

    elif "Kirim Bukti" in text:
        # Jika user menekan tombol instruksi, ingatkan untuk kirim foto asli
        await update.message.reply_text(
            "Silakan kirimkan <b>FOTO ASLI</b> melalui menu lampiran (attachment) di bawah.",
            parse_mode='HTML'
        )

    elif "Batal" in text or "Kembali" in text:
        context.user_data.clear()
        await update.message.reply_text("✅ Kembali ke Menu Utama:", reply_markup=get_main_menu())

    elif "Request Link" in text:
        if context.user_data.get('proof_completed'):
            await update.message.reply_text("⏳ Sedang membuat link unik...")
            link = await generate_unique_link(context, user_name)
            if link:
                await update.message.reply_text(
                    f"✅ <b>Link Akses:</b>\n{link}\n\n"
                    "Silakan klik link di atas dan pilih <b>'Request to Join'</b>.", 
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text("⛔ <b>Akses Ditolak!</b> Selesaikan kirim bukti foto dulu.", parse_mode='HTML')

    elif "Status" in text:
        status = "⏳ Menunggu Admin" if f"pending_{user_id}" in context.bot_data else "❌ Tidak ada permintaan aktif."
        await update.message.reply_text(f"Status: <b>{status}</b>", parse_mode='HTML')

    elif "Bantuan" in text:
        await update.message.reply_text(f"Hubungi Admin: <a href='tg://user?id={ADMIN_ID}'>Klik di Sini</a>", parse_mode='HTML')

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('status') != 'uploading_proofs':
        await update.message.reply_text("⚠️ Silakan klik menu <b>📝 Registrasi</b> terlebih dahulu.", parse_mode='HTML')
        return

    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    current_count = context.user_data.get('proof_count', 0) + 1
    context.user_data['proof_count'] = current_count
    
    photo_id = update.message.photo[-1].file_id
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_id,
            caption=f"📩 <b>BUKTI {current_count}</b>\n👤 User: {user_name}\n🆔 ID: <code>{user_id}</code>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Gagal kirim ke admin: {e}")

    if current_count < 2:
        await update.message.reply_text(f"✅ Bukti ke-{current_count} diterima. Kirim <b>1 foto lagi</b>!", parse_mode='HTML')
    else:
        context.user_data['proof_completed'] = True
        context.user_data['status'] = 'completed'
        await update.message.reply_text(
            "✅ <b>SEMUA BUKTI DITERIMA!</b>\n\nSilakan ambil link Anda di bawah:",
            reply_markup=get_link_menu(),
            parse_mode='HTML'
        )

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.chat_join_request.from_user
    c_id = update.chat_join_request.chat.id
    context.bot_data[f"pending_{u.id}"] = c_id
    
    btn = [[InlineKeyboardButton("Approve ✅", callback_data=f"app_{u.id}_{c_id}"),
            InlineKeyboardButton("Decline ❌", callback_data=f"dec_{u.id}_{c_id}")]]
            
    await context.bot.send_message(
        ADMIN_ID, 
        f"🚨 <b>JOIN REQUEST BARU</b>\n👤 Nama: {u.full_name}\n🆔 ID: <code>{u.id}</code>", 
        parse_mode='HTML', 
        reply_markup=InlineKeyboardMarkup(btn)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    action, u_id, c_id = data[0], int(data[1]), int(data[2])
    
    try:
        if action == "app":
            await context.bot.approve_chat_join_request(chat_id=c_id, user_id=u_id)
            try:
                await context.bot.send_message(u_id, "🥳 <b>Selamat!</b> Permintaan Anda disetujui Admin.", parse_mode='HTML')
            except: pass
            await query.edit_message_text(f"✅ Berhasil Menyetujui ID: {u_id}")
        else:
            await context.bot.decline_chat_join_request(chat_id=c_id, user_id=u_id)
            await query.edit_message_text(f"❌ Menolak ID: {u_id}")
        
        context.bot_data.pop(f"pending_{u_id}", None)
    except Exception as e:
        await query.edit_message_text(f"❌ Gagal: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_screenshot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot standby di chat pribadi...")
    app.run_polling()

if __name__ == '__main__':
    main()
