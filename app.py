import streamlit as st
import pandas as pd
import os
import shutil
import zipfile
import io
from datetime import datetime, timedelta
from PIL import Image

# === Constants ===
CSV_FILE = "du_lieu_bat_dong_san.csv"
IMAGE_DIR = "anh_nha"
SHARED_DIR = "chia_se"
BACKUP_DIR = "backups"
IMAGE_WIDTH = 120

# === Ensure necessary directories ===
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(SHARED_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# === Auto Backup Every 3 Days ===
def auto_backup():
    today = datetime.today()
    for fname in os.listdir(BACKUP_DIR):
        if fname.endswith("_backup.csv"):
            last_backup = datetime.strptime(fname.split("_")[0], "%Y%m%d")
            if today - last_backup < timedelta(days=3):
                return  # already backed up within 3 days

    # Backup CSV
    csv_backup_path = os.path.join(BACKUP_DIR, f"{today.strftime('%Y%m%d')}_backup.csv")
    if os.path.exists(CSV_FILE):
        shutil.copy(CSV_FILE, csv_backup_path)

    # Backup images to ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(IMAGE_DIR):
            for filename in filenames:
                filepath = os.path.join(foldername, filename)
                arcname = os.path.relpath(filepath, IMAGE_DIR)
                zipf.write(filepath, arcname)
    with open(os.path.join(BACKUP_DIR, f"{today.strftime('%Y%m%d')}_images.zip"), "wb") as f:
        f.write(zip_buffer.getvalue())

auto_backup()

# === Load or initialize data ===
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["Loại hình", "Dự án", "Giá", "SĐT", "Lợi nhuận", "Notice", "Thư mục ảnh"])

def save_data():
    df.to_csv(CSV_FILE, index=False)

# === Streamlit UI ===
st.set_page_config(page_title="Quản lý BĐS", layout="wide")
st.title("🏘️ Ứng dụng Quản lý Bất động sản")

# === Session state ===
if "reset_form" not in st.session_state:
    st.session_state.reset_form = False
if "search_triggered" not in st.session_state:
    st.session_state.search_triggered = False
if "edit_trigger" not in st.session_state:
    st.session_state.edit_trigger = False
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# === Reset logic ===
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

# === Edit Form ===
if st.session_state.edit_trigger and st.session_state.edit_index is not None:
    st.header("✏️ Chỉnh sửa thông tin nhà")
    edit_idx = st.session_state.edit_index
    edit_row = df.loc[edit_idx]

    with st.form("edit_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_loai_hinh = st.text_input("Loại hình", value=edit_row["Loại hình"])
            new_price = st.text_input("Giá", value=str(edit_row["Giá"]))
            new_profit = st.text_input("Lợi nhuận", value=edit_row["Lợi nhuận"])
        with col2:
            new_du_an = st.text_input("Dự án", value=edit_row["Dự án"])
            new_phone = st.text_input("SĐT", value=edit_row["SĐT"])
            new_notice = st.text_area("Ghi chú", value=edit_row["Notice"], height=80)

        uploaded_edit_files = st.file_uploader(
            "Upload ảnh mới (nếu muốn ghi đè)", 
            accept_multiple_files=True, 
            type=['png', 'jpg', 'jpeg', 'tif'],
            key=f"edit_uploader_{edit_idx}"
        )

        submitted_edit = st.form_submit_button("💾 Lưu thay đổi")

        if submitted_edit:
            try:
                new_price_val = float(new_price)
                df.at[edit_idx, "Loại hình"] = new_loai_hinh
                df.at[edit_idx, "Dự án"] = new_du_an
                df.at[edit_idx, "Giá"] = new_price_val
                df.at[edit_idx, "SĐT"] = new_phone
                df.at[edit_idx, "Lợi nhuận"] = new_profit
                df.at[edit_idx, "Notice"] = new_notice

                edit_folder_path = df.at[edit_idx, "Thư mục ảnh"]
                if uploaded_edit_files:
                    for f in os.listdir(edit_folder_path):
                        os.remove(os.path.join(edit_folder_path, f))
                    for uploaded_file in uploaded_edit_files:
                        with open(os.path.join(edit_folder_path, uploaded_file.name), "wb") as f:
                            f.write(uploaded_file.read())

                save_data()
                st.success("✅ Đã cập nhật thành công!")
                st.session_state.edit_trigger = False
                st.session_state.edit_index = None
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

# === Display Results ===
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

            col1, col2, col3 = st.columns(3)
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

            with col3:
                if st.button("✏️ Chỉnh sửa", key=f"edit_{idx}"):
                    st.session_state["edit_index"] = idx
                    st.session_state["edit_trigger"] = True
                    st.rerun()

# === Backup Section ===
st.markdown("### 💾 Sao lưu và khôi phục")

csv_export = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Tải xuống dữ liệu (CSV)", data=csv_export, file_name="du_lieu_bat_dong_san.csv", mime="text/csv")

# Download image ZIP
def zip_all_images():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(IMAGE_DIR):
            for filename in filenames:
                filepath = os.path.join(foldername, filename)
                arcname = os.path.relpath(filepath, IMAGE_DIR)
                zipf.write(filepath, arcname)
    zip_buffer.seek(0)
    return zip_buffer

if os.listdir(IMAGE_DIR):
    image_zip = zip_all_images()
    st.download_button("🖼️ Tải xuống toàn bộ ảnh", data=image_zip, file_name="anh_bds.zip", mime="application/zip")

# Restore both CSV and ZIP
st.markdown("### 🔁 Phục hồi dữ liệu")

restore_csv = st.file_uploader("📤 Tải lên file CSV đã sao lưu", type=["csv"])
restore_zip = st.file_uploader("📤 Tải lên file ZIP ảnh đã sao lưu", type=["zip"])

if st.button("♻️ Phục hồi toàn bộ"):
    if restore_csv and restore_zip:
        try:
            df = pd.read_csv(restore_csv)
            save_data()
            with zipfile.ZipFile(restore_zip, 'r') as zipf:
                zipf.extractall(IMAGE_DIR)
            st.success("✅ Phục hồi dữ liệu thành công!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi khi phục hồi: {e}")
    else:
        st.warning("⚠️ Cần cả CSV và ZIP để phục hồi toàn bộ dữ liệu.")
