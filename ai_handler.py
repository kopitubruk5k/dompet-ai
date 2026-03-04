import google.generativeai as genai
import json
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """Kamu adalah asisten keuangan pribadi yang cerdas dan ramah bernama "Dompet AI".
Kamu berkomunikasi dalam Bahasa Indonesia yang santai dan mudah dipahami.

Tugasmu adalah menganalisis pesan pengguna dan mengekstrak informasi transaksi keuangan.

Jika pengguna menyebutkan transaksi (pengeluaran atau pemasukan), ekstrak:
- tipe: "pengeluaran" atau "pemasukan"
- jumlah: angka dalam Rupiah (tanpa titik/koma)
- kategori: pilih dari [Makanan, Transport, Belanja, Hiburan, Kesehatan, Pendidikan, Tagihan, Gaji, Bisnis, Investasi, Lainnya]
- deskripsi: deskripsi singkat transaksi

Untuk reminder tagihan, ekstrak:
- judul: nama tagihan
- jumlah: nominal tagihan
- tanggal: tanggal jatuh tempo dalam format YYYY-MM-DD

Balas HANYA dalam format JSON berikut, tanpa teks lain, tanpa backtick, tanpa markdown:
{
  "aksi": "catat_transaksi" | "tambah_reminder" | "tanya_laporan" | "percakapan",
  "data": { ... },
  "pesan": "pesan balasan yang ramah untuk pengguna"
}

Contoh:
- "tadi beli makan siang 25rb" → aksi: catat_transaksi
- "gajian 5 juta" → aksi: catat_transaksi (pemasukan)
- "ingatkan tagihan listrik 200rb tanggal 20" → aksi: tambah_reminder
- "berapa pengeluaran bulan ini?" → aksi: tanya_laporan
- "halo" → aksi: percakapan

Untuk percakapan biasa, jawab dengan ramah dan singkat."""


def parse_pesan(pesan_user: str, konteks_keuangan: str = "") -> dict:
    """Kirim pesan ke Gemini dan parse hasilnya."""
    try:
        prompt = SYSTEM_PROMPT + "\n\n"
        if konteks_keuangan:
            prompt += f"Konteks: {konteks_keuangan}\n\n"
        prompt += f"Pesan pengguna: {pesan_user}"

        response = model.generate_content(prompt)
        teks = response.text.strip()

        # Bersihkan jika Gemini tetap membungkus dengan markdown
        if "```" in teks:
            teks = teks.split("```")[1]
            if teks.startswith("json"):
                teks = teks[4:]
        teks = teks.strip()

        return json.loads(teks)

    except json.JSONDecodeError:
        return {
            "aksi": "percakapan",
            "data": {},
            "pesan": "Maaf, saya kurang mengerti. Bisa coba ulangi? Contoh: 'beli makan 25rb' atau 'gajian 5 juta'"
        }
    except Exception as e:
        return {
            "aksi": "error",
            "data": {},
            "pesan": f"Terjadi kesalahan: {str(e)}"
        }


def analisis_keuangan(ringkasan: dict) -> str:
    """Minta Gemini menganalisis kondisi keuangan pengguna."""
    try:
        transaksi_str = ""
        for t in ringkasan.get('transaksi', [])[:20]:
            transaksi_str += f"- {t.tipe}: {t.kategori} Rp{t.jumlah:,.0f} ({t.deskripsi})\n"

        prompt = f"""Analisis kondisi keuangan berikut dan berikan saran singkat (3-4 poin):

Bulan ini:
- Total Pemasukan: Rp{ringkasan['pemasukan']:,.0f}
- Total Pengeluaran: Rp{ringkasan['pengeluaran']:,.0f}
- Saldo: Rp{ringkasan['saldo']:,.0f}

20 Transaksi Terakhir:
{transaksi_str}

Berikan analisis singkat dan saran praktis dalam Bahasa Indonesia yang ramah."""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Tidak dapat menganalisis: {str(e)}"
