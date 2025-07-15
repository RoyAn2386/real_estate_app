import streamlit as st
import pandas as pd
import os
import shutil
from PIL import Image

# Constants
CSV_FILE = "du_lieu_bat_dong_san.csv"
IMAGE_DIR = "anh_nha"
SHARED_DIR = "chia_se"
IMAGE_WIDTH = 120

# Ensure necessary directories exist
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(SHARED_DIR, exist_ok=True)

# Load or create dataframe
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["Loại hình", "Dự án", "Giá", "SĐT", "Lợi nhuận", "Notice", "Thư mục ảnh"])

def save_data():
    df.to_csv(CSV_FILE, index=False)

# Page setup
st.set_page_config(page_title="Quản lý BĐS", layout="wide")
st.title("🏘️ Ứng dụng Quản lý Bất động sản")

# === Reset logic ===
if "reset_form" not in st.session_state:
    st.session_state.reset_form = False
if "search_triggered" not in st.session_state:
    st.session_state.search_triggered = False

if st.session_state.reset_form:
    for key in ["loai_hinh", "du_an", "price", "phone", "profit", "notice"]:
        st.session_state[key] = ""
    st.session_state.reset_form = False

# === Add Form ===
st.header("➕ Thêm dữ liệu")
with st.form("add_form"):
    col1, col2 = st.columns(2)
    with col1:
        loai_hinh = st.text_input("Loại hình", key="loai_hinh", max_chars=50)
        price = st.text_input("Giá", key="price", max_chars=20)
        profit = st.text_input("Lợi nhuận", key="profit", max_chars=20)
    with col2:
        du_an = st.text_input("Dự án", key="du_an", max_chars=50)
        phone = st.text_input("SĐT", key="phone", max_chars=20)
        notice = st.text_area("Ghi chú", key="notice", height=80)

    uploader_key = f"uploader_{len(df)}" if st.session_state.reset_form else "uploader"
    uploaded_files = st.file_uploader("Upload images", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'tif'], key=uploader_key)

    submitted = st.form_submit_button("📥 Thêm nhà")

    if submitted:
        try:
            price_val = float(price)
            folder_name = f"{loai_hinh}_{len(df)}"
            folder_path = os.path.join(IMAGE_DIR, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    with open(os.path.join(folder_path, uploaded_file.name), "wb") as f:
                        f.write(uploaded_file.read())

            new_data = {
                "Loại hình": loai_hinh,
                "Dự án": du_an,
                "Giá": price_val,
                "SĐT": phone,
                "Lợi nhuận": profit,
                "Notice": notice,
                "Thư mục ảnh": folder_path
            }

            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            save_data()
            st.success("✅ Đã thêm dữ liệu!")
            st.session_state.reset_form = True
            st.rerun()

        except ValueError:
            st.error("❌ Vui lòng nhập đúng định dạng giá.")

# === Search Section ===
st.header("🔍 Tìm kiếm nhà")

col1, col2, col3, col4 = st.columns(4)
with col1:
    loai_hinh_search = st.text_input("Loại hình (tìm)", max_chars=50, key="loai_hinh_search")
with col2:
    du_an_search = st.text_input("Dự án (tìm)", max_chars=50, key="du_an_search")
with col3:
    min_price = st.text_input("Giá tối thiểu", max_chars=20, key="min_price")
with col4:
    max_price = st.text_input("Giá tối đa", max_chars=20, key="max_price")

# Search button
if st.button("🔎 Tìm kiếm"):
    st.session_state.search_triggered = True

def filter_data(df):
    filtered = df.copy()
    try:
        min_p = float(min_price) if min_price else 0
        max_p = float(max_price) if max_price else float('inf')
    except:
        st.error("❌ Giá không hợp lệ")
        return pd.DataFrame()

    if loai_hinh_search:
        filtered = filtered[filtered["Loại hình"].astype(str).str.contains(loai_hinh_search, case=False, na=False)]
    if du_an_search:
        filtered = filtered[filtered["Dự án"].astype(str).str.contains(du_an_search, case=False, na=False)]

    filtered = filtered[(filtered["Giá"] >= min_p) & (filtered["Giá"] <= max_p)]
    return filtered

filtered = filter_data(df) if st.session_state.search_triggered else df.copy()

# === Display Results (ALWAYS VISIBLE) ===
st.header("📋 Danh sách nhà")

if filtered.empty:
    st.warning("⚠️ Không tìm thấy kết quả.")
else:
    for idx, row in filtered.iterrows():
        st.markdown("---")
        cols = st.columns([1, 2])
        with cols[0]:
            folder_path = row["Thư mục ảnh"]
            if os.path.exists(folder_path):
                images = []
                for file in os.listdir(folder_path):
                    try:
                        image = Image.open(os.path.join(folder_path, file))
                        images.append(image)
                    except:
                        continue
                if images:
                    st.image(images, width=IMAGE_WIDTH)

        with cols[1]:
            st.markdown(f"""
                **🏠 Loại hình:** {row['Loại hình']}  
                **📦 Dự án:** {row['Dự án']}  
                **💰 Giá:** {row['Giá']}  
                **📞 SĐT:** {row['SĐT']}  
                **📈 Lợi nhuận:** {row['Lợi nhuận']}  
                **📝 Ghi chú:** {row['Notice']}
            """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📤 Chia sẻ", key=f"share_{idx}"):
                    share_folder = os.path.join(SHARED_DIR, f"{row['Loại hình']}_{idx}")
                    os.makedirs(share_folder, exist_ok=True)
                    info_text = (
                        f"🏠 Loại hình: {row['Loại hình']}\n"
                        f"📦 Dự án: {row['Dự án']}\n"
                        f"💰 Giá: {row['Giá']}\n"
                        f"📝 Ghi chú: {row['Notice']}"
                    )
                    with open(os.path.join(share_folder, "thong_tin.txt"), "w", encoding="utf-8") as f:
                        f.write(info_text)
                    for file in os.listdir(folder_path):
                        shutil.copy(os.path.join(folder_path, file), share_folder)
                    st.success(f"✅ Đã chia sẻ tại: {share_folder}")

            with col2:
                if st.button("🗑️ Xóa", key=f"delete_{idx}"):
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)
                    df = df.drop(idx).reset_index(drop=True)
                    save_data()
                    st.success("✅ Đã xóa mục thành công!")
                    st.rerun()


