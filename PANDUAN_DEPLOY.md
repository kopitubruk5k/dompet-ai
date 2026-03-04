# 🚀 PANDUAN DEPLOY DOMPET AI KE RAILWAY (GRATIS)

## Apa itu Railway?
Railway adalah platform hosting gratis yang bisa menjalankan bot kamu 24/7 di cloud.
Link: https://railway.app

---

## LANGKAH 1 — Persiapan GitHub

1. Daftar akun GitHub di https://github.com (gratis)
2. Buat repository baru bernama `dompet-ai`
3. Upload semua file proyek ke repository tersebut
   - main.py
   - database.py
   - ai_handler.py
   - chart.py
   - requirements.txt
   - (JANGAN upload file .env !)

---

## LANGKAH 2 — Tambah File Khusus Railway

Buat file `Procfile` (tanpa ekstensi) di folder proyek:
```
worker: python main.py
```

Buat file `runtime.txt`:
```
python-3.11.0
```

---

## LANGKAH 3 — Deploy ke Railway

1. Buka https://railway.app dan login dengan akun GitHub
2. Klik **"New Project"**
3. Pilih **"Deploy from GitHub repo"**
4. Pilih repository `dompet-ai`
5. Klik **"Deploy Now"**

---

## LANGKAH 4 — Atur Environment Variables

Di Railway, masuk ke tab **Variables** dan tambahkan:

| Key | Value |
|-----|-------|
| TELEGRAM_TOKEN | token dari BotFather |
| ANTHROPIC_API_KEY | key dari console.anthropic.com |

---

## LANGKAH 5 — Selesai! 🎉

Bot kamu sekarang berjalan 24/7 di cloud secara gratis!

---

## Alternatif Hosting Lain
- **Render.com** — Gratis, mirip Railway
- **Fly.io** — Gratis tier tersedia
- **VPS Lokal** — Bisa pakai Raspberry Pi atau PC lama

---

## Troubleshooting

**Bot tidak merespons?**
- Cek log di Railway dashboard
- Pastikan TELEGRAM_TOKEN benar
- Pastikan ANTHROPIC_API_KEY aktif dan ada credit

**Error "module not found"?**
- Pastikan semua library ada di requirements.txt

**Grafik tidak muncul?**
- Library matplotlib sudah terpasang otomatis dari requirements.txt
