from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# Cek apakah ada URL database dari environment (untuk Cloud/Railway)
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Jika tidak ada (lokal), pakai SQLite
engine = create_engine(db_url or 'sqlite:///keuangan.db', echo=False)
Session = sessionmaker(bind=engine)

class Transaksi(Base):
    __tablename__ = 'transaksi'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    tipe = Column(String, nullable=False)        # 'pemasukan' atau 'pengeluaran'
    jumlah = Column(Float, nullable=False)
    kategori = Column(String, nullable=False)
    deskripsi = Column(Text)
    tanggal = Column(DateTime, default=datetime.now)

class Reminder(Base):
    __tablename__ = 'reminder'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    judul = Column(String, nullable=False)
    jumlah = Column(Float)
    tanggal_jatuh_tempo = Column(DateTime)
    sudah_diingatkan = Column(Integer, default=0)

class Budget(Base):
    __tablename__ = 'budget'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    kategori = Column(String, nullable=False)
    batas = Column(Float, nullable=False)
    bulan = Column(String, nullable=False)   # format: "2024-01"

def init_db():
    Base.metadata.create_all(engine)

# ── CRUD Transaksi ──────────────────────────────────────────────────────────

def tambah_transaksi(user_id, tipe, jumlah, kategori, deskripsi=""):
    db = Session()
    try:
        t = Transaksi(user_id=str(user_id), tipe=tipe, jumlah=jumlah,
                      kategori=kategori, deskripsi=deskripsi)
        db.add(t)
        db.commit()
        return True
    finally:
        db.close()

def get_transaksi(user_id, bulan=None, tahun=None):
    db = Session()
    try:
        q = db.query(Transaksi).filter(Transaksi.user_id == str(user_id))
        if bulan and tahun:
            q = q.filter(
                Transaksi.tanggal >= datetime(tahun, bulan, 1),
                Transaksi.tanggal < datetime(tahun, bulan % 12 + 1, 1)
                if bulan < 12 else Transaksi.tanggal < datetime(tahun + 1, 1, 1)
            )
        return q.order_by(Transaksi.tanggal.desc()).all()
    finally:
        db.close()

def get_ringkasan(user_id, bulan=None, tahun=None):
    transaksi = get_transaksi(user_id, bulan, tahun)
    pemasukan = sum(t.jumlah for t in transaksi if t.tipe == 'pemasukan')
    pengeluaran = sum(t.jumlah for t in transaksi if t.tipe == 'pengeluaran')
    return {
        'pemasukan': pemasukan,
        'pengeluaran': pengeluaran,
        'saldo': pemasukan - pengeluaran,
        'transaksi': transaksi
    }

def get_per_kategori(user_id, bulan=None, tahun=None):
    transaksi = get_transaksi(user_id, bulan, tahun)
    hasil = {}
    for t in transaksi:
        key = (t.tipe, t.kategori)
        hasil[key] = hasil.get(key, 0) + t.jumlah
    return hasil

# ── Reminder ────────────────────────────────────────────────────────────────

def tambah_reminder(user_id, judul, jumlah, tanggal_jatuh_tempo):
    db = Session()
    try:
        r = Reminder(user_id=str(user_id), judul=judul, jumlah=jumlah,
                     tanggal_jatuh_tempo=tanggal_jatuh_tempo)
        db.add(r)
        db.commit()
        return True
    finally:
        db.close()

def get_reminder(user_id):
    db = Session()
    try:
        return db.query(Reminder).filter(
            Reminder.user_id == str(user_id),
            Reminder.sudah_diingatkan == 0
        ).order_by(Reminder.tanggal_jatuh_tempo).all()
    finally:
        db.close()

def get_reminder_jatuh_tempo(hari_ke_depan=3):
    db = Session()
    try:
        from datetime import timedelta
        batas = datetime.now() + timedelta(days=hari_ke_depan)
        return db.query(Reminder).filter(
            Reminder.tanggal_jatuh_tempo <= batas,
            Reminder.sudah_diingatkan == 0
        ).all()
    finally:
        db.close()

def tandai_reminder_selesai(reminder_id):
    db = Session()
    try:
        r = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if r:
            r.sudah_diingatkan = 1
            db.commit()
    finally:
        db.close()
