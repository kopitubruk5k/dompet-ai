"""
╔══════════════════════════════════════════╗
║       ASISTEN KEUANGAN TELEGRAM BOT      ║
║         Powered by Claude AI             ║
╚══════════════════════════════════════════╝

Cara menjalankan:
  1. Isi file .env dengan TELEGRAM_TOKEN dan GEMINI_API_KEY
  2. Jalankan: python main.py
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

import database as db
import ai_handler as ai
import chart

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

NAMA_BULAN = [
    '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]

# ── /start ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nama = update.effective_user.first_name
    pesan = f"""👋 Halo, *{nama}*! Selamat datang di *Dompet AI* 💰

Saya asisten keuangan pribadimu yang cerdas. Kamu bisa:

📝 *Catat transaksi* dengan bahasa natural:
   • "beli makan siang 25rb"
   • "gajian 8 juta"
   • "bayar listrik 150rb"

📊 *Lihat laporan* dengan perintah:
   • /laporan — Ringkasan bulan ini
   • /chart — Grafik keuangan
   • /reminder — Daftar tagihan

💡 *Tips:* Cukup chat seperti biasa, saya akan otomatis mencatat!

Ketik /bantuan untuk panduan lengkap."""
    await update.message.reply_text(pesan, parse_mode='Markdown')

# ── /bantuan ─────────────────────────────────────────────────────────────────

async def bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = """📚 *PANDUAN DOMPET AI*

━━━━━━━━━━━━━━━━━━━━━━━
*💬 Catat Transaksi (Cukup Chat Biasa)*
• "beli kopi 25.000"
• "makan siang 35rb"
• "gajian 5 juta"
• "dapat bonus 1.5jt"
• "bayar Netflix 54rb"

*📊 Perintah Laporan*
/laporan — Ringkasan bulan ini
/laporan_bulan — Pilih bulan tertentu
/analisis — Analisis AI kondisi keuangan
/chart — Semua grafik sekaligus
/chart_kategori — Donut chart per kategori
/chart_tren — Grafik tren harian

*⏰ Reminder Tagihan*
/tambah_reminder — Tambah tagihan
/reminder — Lihat semua tagihan

*🔧 Lainnya*
/start — Mulai ulang
/bantuan — Panduan ini
━━━━━━━━━━━━━━━━━━━━━━━"""
    await update.message.reply_text(pesan, parse_mode='Markdown')

# ── /laporan ─────────────────────────────────────────────────────────────────

async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    ringkasan = db.get_ringkasan(user_id, now.month, now.year)
    nama_bln = f"{NAMA_BULAN[now.month]} {now.year}"

    emoji_saldo = "✅" if ringkasan['saldo'] >= 0 else "⚠️"
    pesan = f"""📊 *Laporan Keuangan — {nama_bln}*

💚 Pemasukan:   Rp{ringkasan['pemasukan']:>12,.0f}
❤️ Pengeluaran: Rp{ringkasan['pengeluaran']:>12,.0f}
━━━━━━━━━━━━━━━━━━━━━
{emoji_saldo} Saldo:      Rp{ringkasan['saldo']:>12,.0f}

📝 Total transaksi: {len(ringkasan['transaksi'])} kali

Gunakan /chart untuk melihat grafik 📈"""
    await update.message.reply_text(pesan, parse_mode='Markdown')

# ── /analisis ────────────────────────────────────────────────────────────────

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    await update.message.reply_text("🤔 Sedang menganalisis keuanganmu...")

    ringkasan = db.get_ringkasan(user_id, now.month, now.year)
    if not ringkasan['transaksi']:
        await update.message.reply_text(
            "Belum ada transaksi bulan ini. Mulai catat dengan chat biasa ya!"
        )
        return

    hasil = ai.analisis_keuangan(ringkasan)
    await update.message.reply_text(f"🧠 *Analisis AI:*\n\n{hasil}", parse_mode='Markdown')

# ── /chart ───────────────────────────────────────────────────────────────────

async def chart_semua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    nama_bln = f"{NAMA_BULAN[now.month]} {now.year}"
    await update.message.reply_text("📊 Membuat grafik, tunggu sebentar...")

    ringkasan = db.get_ringkasan(user_id, now.month, now.year)
    per_kategori = db.get_per_kategori(user_id, now.month, now.year)

    if not ringkasan['transaksi']:
        await update.message.reply_text("Belum ada data transaksi bulan ini.")
        return

    # Chart 1: Ringkasan
    img_ringkasan = chart.buat_chart_ringkasan(ringkasan, nama_bln)
    await update.message.reply_photo(photo=img_ringkasan,
                                     caption=f"📊 Ringkasan {nama_bln}")

    # Chart 2: Kategori
    img_kategori = chart.buat_chart_kategori(per_kategori)
    if img_kategori:
        await update.message.reply_photo(photo=img_kategori,
                                         caption="🍩 Pengeluaran per Kategori")

    # Chart 3: Tren
    img_tren = chart.buat_chart_tren(ringkasan['transaksi'])
    if img_tren:
        await update.message.reply_photo(photo=img_tren,
                                         caption="📈 Tren Harian")

# ── /reminder ────────────────────────────────────────────────────────────────

async def lihat_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reminders = db.get_reminder(user_id)

    if not reminders:
        await update.message.reply_text(
            "Tidak ada reminder aktif.\n\n"
            "Tambahkan dengan: /tambah_reminder\n"
            "atau chat: \"ingatkan tagihan listrik 200rb tanggal 20\""
        )
        return

    pesan = "⏰ *Reminder Tagihan Aktif:*\n\n"
    for r in reminders:
        tgl = r.tanggal_jatuh_tempo.strftime('%d %B %Y')
        sisa = (r.tanggal_jatuh_tempo - datetime.now()).days
        emoji = "🔴" if sisa <= 3 else "🟡" if sisa <= 7 else "🟢"
        pesan += f"{emoji} *{r.judul}*\n"
        if r.jumlah:
            pesan += f"   💰 Rp{r.jumlah:,.0f}\n"
        pesan += f"   📅 Jatuh tempo: {tgl}\n"
        pesan += f"   ⏱ {sisa} hari lagi\n\n"

    await update.message.reply_text(pesan, parse_mode='Markdown')

async def tambah_reminder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "➕ *Tambah Reminder Tagihan*\n\n"
        "Chat seperti ini:\n"
        "\"ingatkan tagihan listrik 200rb tanggal 20\"\n"
        "\"reminder cicilan motor 800rb tanggal 15\"\n\n"
        "Saya akan otomatis menyimpannya! 😊",
        parse_mode='Markdown'
    )

# ── HANDLER PESAN UTAMA ───────────────────────────────────────────────────────

async def proses_pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pesan_user = update.message.text

    # Tampilkan "sedang mengetik..."
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    # Kirim ke AI untuk diproses
    now = datetime.now()
    konteks = f"Tanggal hari ini: {now.strftime('%d %B %Y')}"
    hasil = ai.parse_pesan(pesan_user, konteks)
    aksi = hasil.get('aksi', 'percakapan')
    data = hasil.get('data', {})
    pesan_balas = hasil.get('pesan', 'Maaf, saya tidak mengerti.')

    if aksi == 'catat_transaksi':
        try:
            sukses = db.tambah_transaksi(
                user_id=user_id,
                tipe=data.get('tipe') or 'pengeluaran',
                jumlah=float(data.get('jumlah') or 0),
                kategori=data.get('kategori') or 'Lainnya',
                deskripsi=data.get('deskripsi') or pesan_user
            )
            if sukses:
                emoji = "📥" if data.get('tipe') == 'pemasukan' else "📤"
                await update.message.reply_text(
                    f"{emoji} *Tercatat!*\n\n{pesan_balas}\n\n"
                    f"💡 Ketik /laporan untuk melihat ringkasan.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("Gagal menyimpan transaksi.")
        except Exception as e:
            logger.error(f"Error catat transaksi: {e}")
            await update.message.reply_text(
                "Maaf, gagal mencatat. Coba format seperti: 'beli makan 25rb'"
            )

    elif aksi == 'tambah_reminder':
        try:
            tgl_str = str(data.get('tanggal') or '')
            now = datetime.now()
            
            if not tgl_str:
                raise ValueError("Tanggal tidak ditemukan")

            # Jika hanya tanggal (angka), set ke bulan ini
            if tgl_str.isdigit():
                tgl = datetime(now.year, now.month, int(tgl_str))
            else:
                tgl = datetime.strptime(tgl_str, '%Y-%m-%d')

            db.tambah_reminder(
                user_id=user_id,
                judul=data.get('judul') or 'Tagihan',
                jumlah=float(data.get('jumlah') or 0),
                tanggal_jatuh_tempo=tgl
            )
            await update.message.reply_text(
                f"⏰ *Reminder Tersimpan!*\n\n{pesan_balas}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error tambah reminder: {e}")
            await update.message.reply_text(
                "Maaf, gagal menyimpan reminder. "
                "Coba: 'ingatkan tagihan listrik 200rb tanggal 20'"
            )

    elif aksi == 'tanya_laporan':
        # Auto-tampilkan laporan
        ringkasan = db.get_ringkasan(user_id, now.month, now.year)
        nama_bln = f"{NAMA_BULAN[now.month]} {now.year}"
        emoji_saldo = "✅" if ringkasan['saldo'] >= 0 else "⚠️"
        pesan = (
            f"📊 *Laporan {nama_bln}*\n\n"
            f"💚 Pemasukan:   Rp{ringkasan['pemasukan']:>12,.0f}\n"
            f"❤️ Pengeluaran: Rp{ringkasan['pengeluaran']:>12,.0f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{emoji_saldo} Saldo:      Rp{ringkasan['saldo']:>12,.0f}\n\n"
            f"{pesan_balas}"
        )
        await update.message.reply_text(pesan, parse_mode='Markdown')

    else:
        # Percakapan biasa
        await update.message.reply_text(pesan_balas)

# ── REMINDER SCHEDULER ────────────────────────────────────────────────────────

async def cek_reminder_otomatis(context: ContextTypes.DEFAULT_TYPE):
    """Cek dan kirim reminder yang mendekati jatuh tempo."""
    reminders = db.get_reminder_jatuh_tempo(hari_ke_depan=3)
    for r in reminders:
        sisa = (r.tanggal_jatuh_tempo - datetime.now()).days
        pesan = (
            f"⚠️ *REMINDER TAGIHAN!*\n\n"
            f"📋 {r.judul}\n"
            f"💰 Rp{r.jumlah:,.0f}\n"
            f"📅 Jatuh tempo: {r.tanggal_jatuh_tempo.strftime('%d %B %Y')}\n"
            f"⏱ {sisa} hari lagi!\n\n"
            f"Jangan lupa dibayar ya! 😊"
        )
        try:
            await context.bot.send_message(
                chat_id=int(r.user_id), text=pesan, parse_mode='Markdown'
            )
            db.tandai_reminder_selesai(r.id)
        except Exception as e:
            logger.error(f"Gagal kirim reminder ke {r.user_id}: {e}")

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    db.init_db()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ ERROR: TELEGRAM_TOKEN tidak ditemukan di .env!")
        return

    app = Application.builder().token(token).build()

    # Daftarkan semua handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bantuan", bantuan))
    app.add_handler(CommandHandler("laporan", laporan))
    app.add_handler(CommandHandler("analisis", analisis))
    app.add_handler(CommandHandler("chart", chart_semua))
    app.add_handler(CommandHandler("chart_kategori", chart_semua))
    app.add_handler(CommandHandler("chart_tren", chart_semua))
    app.add_handler(CommandHandler("reminder", lihat_reminder))
    app.add_handler(CommandHandler("tambah_reminder", tambah_reminder_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, proses_pesan))

    # Jadwalkan cek reminder setiap pagi jam 08:00
    app.job_queue.run_daily(
        cek_reminder_otomatis,
        time=datetime.now().replace(hour=8, minute=0, second=0).time()
    )

    print("🤖 Dompet AI aktif! Tekan Ctrl+C untuk berhenti.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
