import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Toko Hobi Pancing", page_icon="🎣", layout="wide")

# Custom CSS Tampilan
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# KONEKSI KE GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet(worksheet_name):
    """Membaca data dari tab Google Sheets secara realtime"""
    return conn.read(worksheet=worksheet_name, ttl=0)

def append_to_sheet(worksheet_name, new_data_dict):
    """Menambahkan baris data baru ke tab Google Sheets"""
    existing_df = load_sheet(worksheet_name)
    new_df = pd.DataFrame([new_data_dict])
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    conn.update(worksheet=worksheet_name, data=updated_df)

def update_sheet_full(worksheet_name, new_df):
    """Menimpa seluruh data di tab Google Sheets"""
    conn.update(worksheet=worksheet_name, data=new_df)

# Logika Waktu Reset Jam 02:00 Pagi
def get_tanggal_operasional():
    now = datetime.now()
    if now.hour < 2:
        return (now - timedelta(days=1)).strftime('%Y-%m-%d')
    return now.strftime('%Y-%m-%d')

# Login System
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['role'] = ''

if not st.session_state['logged_in']:
    st.title("🎣 Login Toko Utama - HOBI PANCING")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                if user == "admin" and pwd == "admin123":
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'admin'
                    st.rerun()
                elif user == "pegawai" and pwd == "pegawai123":
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'pegawai'
                    st.rerun()
                else:
                    st.error("Login Gagal!")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("🎣 HOBI PANCING")
    uploaded_logo = st.file_uploader("Custom Logo Toko", type=['png', 'jpg', 'jpeg'])
    if uploaded_logo:
        st.image(uploaded_logo, width=150)
        
    st.write(f"Login: **{st.session_state['role'].upper()}**")
    st.info(f"📅 Hari Operasional: **{get_tanggal_operasional()}**")
    
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

# Dynamic Menu
if st.session_state['role'] == 'pegawai':
    menu = st.sidebar.radio("Menu Kasir", ["🔍 Cari Harga & Kalkulator", "⚖️ Panduan Kemas Barang"])
else:
    menu = st.sidebar.radio("Menu Admin Utama", [
        "🔍 Cari Harga & Kalkulator",
        "💵 Master Harga & Modal",
        "⚖️ Panduan Kemas Barang",
        "💸 Input Pemasukan & Pengeluaran",
        "📊 Dashboard Peforma (Time-Series)"
    ])

# ==========================================
# 1. CARI HARGA & KALKULATOR
# ==========================================
if menu == "🔍 Cari Harga & Kalkulator":
    st.title("🔍 Pencarian Harga & Kalkulator Kasir")
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Daftar Harga Barang")
        try:
            df_b = load_sheet("barang_utama")
        except Exception as e:
            df_b = pd.DataFrame(columns=["nama_barang", "kategori_satuan", "harga_modal", "harga_jual", "url_foto"])

        search = st.text_input("🔍 Ketik Nama Barang / Pakan...")
        
        if not df_b.empty and 'nama_barang' in df_b.columns:
            if search:
                df_filtered = df_b[df_b['nama_barang'].astype(str).str.contains(search, case=False, na=False)]
            else:
                df_filtered = df_b
                
            if st.session_state['role'] == 'pegawai':
                cols_to_show = [c for c in ['nama_barang', 'kategori_satuan', 'harga_jual'] if c in df_filtered.columns]
                st.dataframe(df_filtered[cols_to_show], use_container_width=True, hide_index=True)
            else:
                cols_to_show = [c for c in ['nama_barang', 'kategori_satuan', 'harga_modal', 'harga_jual'] if c in df_filtered.columns]
                st.dataframe(df_filtered[cols_to_show], use_container_width=True, hide_index=True)
            
            # Preview Foto Barang
            st.markdown("---")
            st.subheader("🖼️ Preview Foto Produk")
            items = df_filtered['nama_barang'].dropna().tolist() if not df_filtered.empty else []
            selected_item = st.selectbox("Pilih Barang untuk Lihat Foto", items)
            if selected_item:
                item_data = df_filtered[df_filtered['nama_barang'] == selected_item].iloc[0]
                url_foto = item_data.get('url_foto', '')
                
                if pd.notna(url_foto) and str(url_foto).strip() != '':
                    st.image(str(url_foto), caption=selected_item, width=250)
                else:
                    st.image(f"https://source.unsplash.com/300x200/?fishing,{selected_item.replace(' ', '')}", caption=f"Foto Visual: {selected_item}", width=250)
        else:
            st.info("Data barang masih kosong di Google Sheets.")

    with col_right:
        st.subheader("🧮 Kalkulator Cepat")
        st.write("Hitung total belanjaan pembeli:")
        val1 = st.number_input("Item 1 (Rp)", min_value=0, step=500)
        val2 = st.number_input("Item 2 (Rp)", min_value=0, step=500)
        val3 = st.number_input("Item 3 (Rp)", min_value=0, step=500)
        val4 = st.number_input("Item 4 (Rp)", min_value=0, step=500)
        val5 = st.number_input("Item 5 (Rp)", min_value=0, step=500)
        
        total_kalkulator = val1 + val2 + val3 + val4 + val5
        st.markdown(f"### **Total: Rp {total_kalkulator:,.0f}**")
        
        bayar = st.number_input("Uang Dibayar (Rp)", min_value=0, step=1000)
        if bayar > 0:
            kembalian = bayar - total_kalkulator
            if kembalian >= 0:
                st.success(f"Kembalian: Rp {kembalian:,.0f}")
            else:
                st.error(f"Uang Kurang: Rp {abs(kembalian):,.0f}")

# ==========================================
# 2. MASTER HARGA & MODAL (ADMIN)
# ==========================================
elif menu == "💵 Master Harga & Modal":
    st.title("💵 Pengaturan Master Harga & Modal")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("➕ Tambah / Update Barang ke Google Sheets")
        with st.form("form_barang", clear_on_submit=True):
            nama = st.text_input("Nama Barang / Pakan")
            satuan = st.selectbox("Kategori Satuan", ["Pcs", "Per Kg", "Per Ons", "Pack / Bungkus", "Lainnya"])
            modal = st.number_input("Harga Modal / HPP (Rp)", min_value=0, step=500)
            jual = st.number_input("Harga Jual (Rp)", min_value=0, step=500)
            url = st.text_input("URL Link Foto Produk (Opsional)")
            
            if st.form_submit_button("Simpan ke Google Sheets"):
                df_b = load_sheet("barang_utama")
                if not df_b.empty and nama in df_b['nama_barang'].values:
                    df_b.loc[df_b['nama_barang'] == nama, ['kategori_satuan', 'harga_modal', 'harga_jual', 'url_foto']] = [satuan, modal, jual, url]
                    update_sheet_full("barang_utama", df_b)
                    st.success(f"Data **{nama}** berhasil diperbarui di Google Sheets!")
                else:
                    new_row = {"nama_barang": nama, "kategori_satuan": satuan, "harga_modal": modal, "harga_jual": jual, "url_foto": url}
                    append_to_sheet("barang_utama", new_row)
                    st.success(f"Barang **{nama}** berhasil disimpan ke Google Sheets!")

    with col2:
        st.subheader("🧮 Kalkulator Margin")
        m_awal = st.number_input("Modal Barang (Rp)", min_value=1, step=500, key="calc_m")
        j_awal = st.number_input("Rencana Harga Jual (Rp)", min_value=1, step=500, key="calc_j")
        if j_awal > m_awal:
            profit = j_awal - m_awal
            margin = (profit / j_awal) * 100
            st.metric("Estimasi Profit/Pcs", f"Rp {profit:,.0f}", f"{margin:.1f}% Margin")

# ==========================================
# 3. PANDUAN KEMAS BARANG
# ==========================================
elif menu == "⚖️ Panduan Kemas Barang":
    st.title("⚖️ Standar Kemasan Produk (Umpan/Pakan)")
    
    if st.session_state['role'] == 'admin':
        with st.expander("➕ Tambah Standar Kemasan"):
            with st.form("f_kemas", clear_on_submit=True):
                n_kemas = st.text_input("Nama Umpan / Barang Kemas")
                b_gram = st.number_input("Takaran Berat (Gram)", min_value=1.0, step=5.0)
                h_kemas = st.number_input("Harga Jual Per Bungkusan (Rp)", min_value=500, step=500)
                ket = st.text_input("Keterangan Kemasan (Misal: Plastik ukuran 12x20)")
                if st.form_submit_button("Simpan Standard"):
                    new_k = {"nama_kemasan": n_kemas, "berat_gram": b_gram, "harga_jual": h_kemas, "keterangan": ket}
                    append_to_sheet("barang_kemasan", new_k)
                    st.success("Standar kemasan tersimpan di Google Sheets!")

    st.subheader("📋 Daftar Takaran Timbangan Kasir / Pegawai")
    try:
        df_k = load_sheet("barang_kemasan")
        st.dataframe(df_k, use_container_width=True, hide_index=True)
    except:
        st.info("Belum ada data kemasan.")

# ==========================================
# 4. INPUT PEMASUKAN & PENGELUARAN (ADMIN)
# ==========================================
elif menu == "💸 Input Pemasukan & Pengeluaran":
    st.title("💸 Catat Keuangan Operasional Harian")
    st.caption(f"📅 Transaksi dicatat untuk Tanggal Operasional: **{get_tanggal_operasional()}** (Reset jam 02:00 Pagi)")
    
    t1, t2 = st.tabs(["📥 Input Pemasukan (Omset Kasir)", "📤 Input Pengeluaran Berkategori"])
    
    with t1:
        with st.form("f_in", clear_on_submit=True):
            nom_in = st.number_input("Total Pemasukan / Setoran (Rp)", min_value=1000, step=10000)
            ket_in = st.text_input("Catatan Pemasukan (Opsional)", value="Omset Kas")
            if st.form_submit_button("Simpan Pemasukan"):
                data_in = {
                    "tanggal_operasional": get_tanggal_operasional(),
                    "jam_input": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "nominal": nom_in,
                    "keterangan": ket_in
                }
                append_to_sheet("pemasukan_harian", data_in)
                st.success("Pemasukan berhasil tersimpan di Google Sheets!")
                
    with t2:
        with st.form("f_out", clear_on_submit=True):
            kat_out = st.selectbox("Kategori Pengeluaran", ["Bayar Supplier", "Makan / Konsumsi", "Gaji Karyawan", "Operasional Toko", "Lainnya"])
            nom_out = st.number_input("Nominal Pengeluaran (Rp)", min_value=1000, step=5000)
            ket_out = st.text_input("Keterangan Detail Pengeluaran")
            if st.form_submit_button("Simpan Pengeluaran"):
                data_out = {
                    "tanggal_operasional": get_tanggal_operasional(),
                    "kategori": kat_out,
                    "keterangan": ket_out,
                    "nominal": nom_out
                }
                append_to_sheet("pengeluaran_utama", data_out)
                st.success("Pengeluaran berhasil tersimpan di Google Sheets!")

# ==========================================
# 5. DASHBOARD PEFORMA TIME-SERIES (ADMIN)
# ==========================================
elif menu == "📊 Dashboard Peforma (Time-Series)":
    st.title("📊 Analisis Peforma Toko Utama (Live GSheets)")
    
    try:
        df_in = load_sheet("pemasukan_harian")
        df_out = load_sheet("pengeluaran_utama")
        
        if not df_in.empty and 'nominal' in df_in.columns:
            df_in['nominal'] = pd.to_numeric(df_in['nominal'], errors='coerce').fillna(0)
            df_in_grouped = df_in.groupby('tanggal_operasional')['nominal'].sum().reset_index().rename(columns={'nominal': 'total_pemasukan'})
            
            if not df_out.empty and 'nominal' in df_out.columns:
                df_out['nominal'] = pd.to_numeric(df_out['nominal'], errors='coerce').fillna(0)
                df_out_grouped = df_out.groupby('tanggal_operasional')['nominal'].sum().reset_index().rename(columns={'nominal': 'total_pengeluaran'})
            else:
                df_out_grouped = pd.DataFrame(columns=['tanggal_operasional', 'total_pengeluaran'])
                
            df_merged = pd.merge(df_in_grouped, df_out_grouped, on='tanggal_operasional', how='outer').fillna(0)
            df_merged['laba_bersih'] = df_merged['total_pemasukan'] - df_merged['total_pengeluaran']
            
            # Line Chart Time-Series
            st.subheader("📈 Time-Series Pemasukan vs Pengeluaran Harian")
            fig = px.line(df_merged, x='tanggal_operasional', y=['total_pemasukan', 'total_pengeluaran', 'laba_bersih'],
                          labels={'value': 'Rupiah', 'variable': 'Kategori', 'tanggal_operasional': 'Tanggal'},
                          title="Grafik Tren Keuangan Toko Utama", markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📊 Breakdown Kategori Pengeluaran")
            if not df_out.empty and 'kategori' in df_out.columns:
                df_kat = df_out.groupby('kategori')['nominal'].sum().reset_index()
                fig_pie = px.pie(df_kat, values='nominal', names='kategori', title="Porsi Pengeluaran Toko")
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Belum ada data pemasukan harian yang dicatat.")
    except Exception as e:
        st.warning("Menunggu data transaksi diisi...")