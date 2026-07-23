import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
import base64

st.set_page_config(page_title="Toko Hobi Pancing", page_icon="🎣", layout="wide")

# Custom CSS Tampilan & Kalkulator Android
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    /* Styling Kalkulator Android */
    .calc-screen {
        background-color: #222222;
        color: #00ffcc;
        font-size: 28px;
        font-family: monospace;
        text-align: right;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        min-height: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# KONEKSI KE GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet(worksheet_name):
    return conn.read(worksheet=worksheet_name, ttl=0)

def append_to_sheet(worksheet_name, new_data_dict):
    existing_df = load_sheet(worksheet_name)
    new_df = pd.DataFrame([new_data_dict])
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    conn.update(worksheet=worksheet_name, data=updated_df)

def update_sheet_full(worksheet_name, new_df):
    conn.update(worksheet=worksheet_name, data=new_df)

# Helper Convert Upload Gambar ke Base64 (Simpan ke Sheets)
def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode('utf-8')
        return f"data:image/png;base64,{base64_str}"
    return ""

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
# 1. CARI HARGA & KALKULATOR ANDROID
# ==========================================
if menu == "🔍 Cari Harga & Kalkulator":
    st.title("🔍 Pencarian Harga & Kalkulator Kasir")
    col_left, col_right = st.columns([1.8, 1.2])
    
    with col_left:
        st.subheader("Daftar Harga Barang")
        try:
            df_b = load_sheet("barang_utama")
        except:
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
            
            # Preview Foto Barang (Upload Langsung)
            st.markdown("---")
            st.subheader("🖼️ Preview Foto Produk")
            items = df_filtered['nama_barang'].dropna().tolist() if not df_filtered.empty else []
            selected_item = st.selectbox("Pilih Barang untuk Lihat Foto", items)
            if selected_item:
                item_data = df_filtered[df_filtered['nama_barang'] == selected_item].iloc[0]
                url_foto = item_data.get('url_foto', '')
                
                if pd.notna(url_foto) and str(url_foto).strip() != '':
                    if str(url_foto).startswith("data:image"):
                        st.image(str(url_foto), caption=selected_item, width=280)
                    else:
                        st.image(str(url_foto), caption=selected_item, width=280)
                else:
                    st.info("Barang ini belum ada fotonya. Admin bisa upload file foto di menu Master Harga.")
        else:
            st.info("Data barang masih kosong di Google Sheets.")

    # --- KALKULATOR HP ANDROID ---
    with col_right:
        st.subheader("📱 Kalkulator Kasir Android")
        if 'calc_expr' not in st.session_state:
            st.session_state['calc_expr'] = "0"

        def press(val):
            if st.session_state['calc_expr'] == "0" or st.session_state['calc_expr'] == "Error":
                st.session_state['calc_expr'] = str(val)
            else:
                st.session_state['calc_expr'] += str(val)

        def clear():
            st.session_state['calc_expr'] = "0"

        def evaluate():
            try:
                # Ganti simbol visual ke operator python
                expr = st.session_state['calc_expr'].replace('×', '*').replace('÷', '/')
                res = eval(expr)
                st.session_state['calc_expr'] = str(int(res) if isinstance(res, float) and res.is_integer() else res)
            except:
                st.session_state['calc_expr'] = "Error"

        # Layar Kalkulator
        st.markdown(f"<div class='calc-screen'>{st.session_state['calc_expr']}</div>", unsafe_allow_html=True)

        # Keypad Grid
        k1, k2, k3, k4 = st.columns(4)
        if k1.button("C", use_container_width=True): clear(); st.rerun()
        if k2.button("÷", use_container_width=True): press("÷"); st.rerun()
        if k3.button("×", use_container_width=True): press("×"); st.rerun()
        if k4.button("-", use_container_width=True): press("-"); st.rerun()

        b7, b8, b9, b_add = st.columns(4)
        if b7.button("7", use_container_width=True): press("7"); st.rerun()
        if b8.button("8", use_container_width=True): press("8"); st.rerun()
        if b9.button("9", use_container_width=True): press("9"); st.rerun()
        if b_add.button("+", use_container_width=True): press("+"); st.rerun()

        b4, b5, b6, b_eq = st.columns(4)
        if b4.button("4", use_container_width=True): press("4"); st.rerun()
        if b5.button("5", use_container_width=True): press("5"); st.rerun()
        if b6.button("6", use_container_width=True): press("6"); st.rerun()
        if b_eq.button("=", use_container_width=True): evaluate(); st.rerun()

        b1, b2, b3, b0 = st.columns(4)
        if b1.button("1", use_container_width=True): press("1"); st.rerun()
        if b2.button("2", use_container_width=True): press("2"); st.rerun()
        if b3.button("3", use_container_width=True): press("3"); st.rerun()
        if b0.button("0", use_container_width=True): press("0"); st.rerun()

# ==========================================
# 2. MASTER HARGA & MODAL (ADMIN)
# ==========================================
elif menu == "💵 Master Harga & Modal":
    st.title("💵 Pengaturan Master Harga & Modal")
    
    t1, t2 = st.tabs(["📋 Upload Foto / Input Satuan", "📋 Copy-Paste Massal dari Sheets"])
    
    with t1:
        st.subheader("➕ Tambah / Update Barang Satuan (Upload Gambar)")
        with st.form("form_barang", clear_on_submit=True):
            nama = st.text_input("Nama Barang / Pakan")
            satuan = st.selectbox("Kategori Satuan", ["Pcs", "Per Kg", "Per Ons", "Pack / Bungkus", "Lainnya"])
            modal = st.number_input("Harga Modal / HPP (Rp)", min_value=0, step=500)
            jual = st.number_input("Harga Jual (Rp)", min_value=0, step=500)
            img_file = st.file_uploader("Upload File Foto Produk (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("Simpan Barang"):
                base64_img = image_to_base64(img_file)
                df_b = load_sheet("barang_utama")
                if not df_b.empty and nama in df_b['nama_barang'].values:
                    df_b.loc[df_b['nama_barang'] == nama, ['kategori_satuan', 'harga_modal', 'harga_jual', 'url_foto']] = [satuan, modal, jual, base64_img]
                    update_sheet_full("barang_utama", df_b)
                    st.success(f"Data **{nama}** berhasil diperbarui di Google Sheets!")
                else:
                    new_row = {"nama_barang": nama, "kategori_satuan": satuan, "harga_modal": modal, "harga_jual": jual, "url_foto": base64_img}
                    append_to_sheet("barang_utama", new_row)
                    st.success(f"Barang **{nama}** berhasil disimpan ke Google Sheets!")

    with t2:
        st.subheader("📋 Input Massal (Copy-Paste Langsung dari Excel / Google Sheets)")
        st.write("Copy tabel kamu dari Google Sheets, lalu Paste (`Ctrl + V`) ke tabel interaktif di bawah ini:")
        
        df_template = pd.DataFrame(columns=["nama_barang", "kategori_satuan", "harga_modal", "harga_jual"])
        edited_df = st.data_editor(df_template, num_rows="dynamic", use_container_width=True)
        
        if st.button("Simpan Semua Baris ke Google Sheets"):
            if not edited_df.empty:
                df_b_exist = load_sheet("barang_utama")
                edited_df['url_foto'] = "" # default kosong
                
                # Gabungkan data lama dan baru
                df_final = pd.concat([df_b_exist, edited_df], ignore_index=True).drop_duplicates(subset=['nama_barang'], keep='last')
                update_sheet_full("barang_utama", df_final)
                st.success("✅ Semua data barang berhasil di-import massal ke Google Sheets!")

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
