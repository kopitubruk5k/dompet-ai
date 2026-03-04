import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io
from datetime import datetime

# Tema warna
WARNA_PEMASUKAN = '#2ecc71'
WARNA_PENGELUARAN = '#e74c3c'
WARNA_SALDO = '#3498db'
WARNA_KATEGORI = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
]
BG_COLOR = '#1a1a2e'
TEXT_COLOR = '#eaeaea'

def set_style():
    plt.rcParams.update({
        'figure.facecolor': BG_COLOR,
        'axes.facecolor': '#16213e',
        'axes.edgecolor': '#0f3460',
        'axes.labelcolor': TEXT_COLOR,
        'xtick.color': TEXT_COLOR,
        'ytick.color': TEXT_COLOR,
        'text.color': TEXT_COLOR,
        'grid.color': '#0f3460',
        'grid.linestyle': '--',
        'grid.alpha': 0.5,
        'font.family': 'DejaVu Sans',
    })

def format_rupiah(x, pos=None):
    if x >= 1_000_000:
        return f'Rp{x/1_000_000:.1f}jt'
    elif x >= 1_000:
        return f'Rp{x/1_000:.0f}rb'
    return f'Rp{x:.0f}'

def buat_chart_ringkasan(ringkasan: dict, nama_bulan: str) -> bytes:
    """Bar chart pemasukan vs pengeluaran + saldo."""
    set_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor(BG_COLOR)
    fig.suptitle(f'📊 Ringkasan Keuangan — {nama_bulan}',
                 color=TEXT_COLOR, fontsize=16, fontweight='bold', y=1.02)

    # Bar chart
    labels = ['Pemasukan', 'Pengeluaran']
    values = [ringkasan['pemasukan'], ringkasan['pengeluaran']]
    colors = [WARNA_PEMASUKAN, WARNA_PENGELUARAN]
    bars = ax1.bar(labels, values, color=colors, width=0.5, edgecolor='none',
                   zorder=3)
    ax1.set_title('Pemasukan vs Pengeluaran', color=TEXT_COLOR, pad=12)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(format_rupiah))
    ax1.grid(axis='y', zorder=0)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                 format_rupiah(val), ha='center', va='bottom', fontsize=11,
                 fontweight='bold', color=TEXT_COLOR)

    # Gauge-style saldo
    saldo = ringkasan['saldo']
    saldo_color = WARNA_PEMASUKAN if saldo >= 0 else WARNA_PENGELUARAN
    ax2.set_xlim(-1.5, 1.5)
    ax2.set_ylim(-1.5, 1.5)
    ax2.set_aspect('equal')
    ax2.axis('off')
    circle = plt.Circle((0, 0), 1.0, color='#16213e', ec='#0f3460', lw=3)
    ax2.add_patch(circle)
    ring = plt.Circle((0, 0), 1.0, color='none', ec=saldo_color, lw=10, alpha=0.8)
    ax2.add_patch(ring)
    ax2.text(0, 0.15, 'SALDO', ha='center', va='center',
             color=TEXT_COLOR, fontsize=12, alpha=0.7)
    ax2.text(0, -0.15, format_rupiah(abs(saldo)), ha='center', va='center',
             color=saldo_color, fontsize=14, fontweight='bold')
    status = '✅ Surplus' if saldo >= 0 else '⚠️ Defisit'
    ax2.text(0, -0.5, status, ha='center', va='center',
             color=saldo_color, fontsize=11)
    ax2.set_title('Saldo Akhir', color=TEXT_COLOR, pad=12)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=BG_COLOR)
    plt.close()
    buf.seek(0)
    return buf.read()

def buat_chart_kategori(per_kategori: dict) -> bytes:
    """Donut chart pengeluaran per kategori."""
    set_style()
    pengeluaran = {k[1]: v for k, v in per_kategori.items() if k[0] == 'pengeluaran'}
    if not pengeluaran:
        return None

    labels = list(pengeluaran.keys())
    values = list(pengeluaran.values())
    colors = WARNA_KATEGORI[:len(labels)]
    total = sum(values)

    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor(BG_COLOR)

    wedges, texts, autotexts = ax.pie(
        values, labels=None, colors=colors,
        autopct=lambda p: f'{p:.1f}%' if p > 3 else '',
        startangle=140, pctdistance=0.75,
        wedgeprops=dict(width=0.55, edgecolor=BG_COLOR, linewidth=2)
    )
    for at in autotexts:
        at.set_color(TEXT_COLOR)
        at.set_fontsize(9)

    ax.text(0, 0, f'Total\n{format_rupiah(total)}', ha='center', va='center',
            color=TEXT_COLOR, fontsize=12, fontweight='bold')

    legend = ax.legend(
        wedges, [f'{l} — {format_rupiah(v)}' for l, v in zip(labels, values)],
        loc='lower center', bbox_to_anchor=(0.5, -0.18),
        ncol=2, frameon=False, labelcolor=TEXT_COLOR, fontsize=9
    )
    ax.set_title('🍩 Pengeluaran per Kategori', color=TEXT_COLOR,
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=BG_COLOR)
    plt.close()
    buf.seek(0)
    return buf.read()

def buat_chart_tren(transaksi_list: list) -> bytes:
    """Line chart tren pemasukan vs pengeluaran harian."""
    set_style()
    if not transaksi_list:
        return None

    dari_tanggal = {}
    for t in transaksi_list:
        tgl = t.tanggal.strftime('%d/%m')
        if tgl not in dari_tanggal:
            dari_tanggal[tgl] = {'pemasukan': 0, 'pengeluaran': 0}
        dari_tanggal[tgl][t.tipe] += t.jumlah

    tanggal = sorted(dari_tanggal.keys())
    pemasukan_vals = [dari_tanggal[t]['pemasukan'] for t in tanggal]
    pengeluaran_vals = [dari_tanggal[t]['pengeluaran'] for t in tanggal]

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(BG_COLOR)

    x = range(len(tanggal))
    ax.fill_between(x, pemasukan_vals, alpha=0.2, color=WARNA_PEMASUKAN)
    ax.fill_between(x, pengeluaran_vals, alpha=0.2, color=WARNA_PENGELUARAN)
    ax.plot(x, pemasukan_vals, color=WARNA_PEMASUKAN, linewidth=2.5,
            marker='o', markersize=5, label='Pemasukan')
    ax.plot(x, pengeluaran_vals, color=WARNA_PENGELUARAN, linewidth=2.5,
            marker='o', markersize=5, label='Pengeluaran')

    ax.set_xticks(x)
    ax.set_xticklabels(tanggal, rotation=45, ha='right', fontsize=8)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_rupiah))
    ax.legend(facecolor='#16213e', edgecolor='#0f3460',
              labelcolor=TEXT_COLOR, fontsize=10)
    ax.set_title('📈 Tren Keuangan Harian', color=TEXT_COLOR,
                 fontsize=14, fontweight='bold')
    ax.grid(True, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=BG_COLOR)
    plt.close()
    buf.seek(0)
    return buf.read()
