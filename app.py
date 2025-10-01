import streamlit as st
from PIL import Image
import io
import zipfile
import os

st.title("印刷用 高画質 画像リサイズ（DPI調整）アプリ")

# 保存用ディレクトリ
SAVE_DIR = "resized"
os.makedirs(SAVE_DIR, exist_ok=True)

# プレフィックス入力
prefix = st.text_input("保存ファイル名に付けるPrefix", value="resized")

# DPI指定
dpi_value = st.number_input("保存時のDPI", min_value=72, max_value=600, value=300)

# ファイルアップロード（複数可）
uploaded_files = st.file_uploader(
    "画像をアップロードしてください", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files and prefix.strip():
    processed_images = []
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)

        # ピクセル数はそのまま、DPIだけ設定
        base_name = os.path.splitext(uploaded_file.name)[0]
        new_filename = f"{prefix}_{base_name}.png"

        save_path = os.path.join(SAVE_DIR, new_filename)
        image.save(save_path, format="PNG", dpi=(dpi_value, dpi_value))

        # ダウンロード用に保持
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG", dpi=(dpi_value, dpi_value))
        img_bytes.seek(0)
        processed_images.append((new_filename, img_bytes))

    # ZIPにまとめる
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for filename, img_bytes in processed_images:
            zip_file.writestr(filename, img_bytes.getvalue())
    zip_buffer.seek(0)

    st.success(f"画像は `{SAVE_DIR}/` フォルダに保存されました ✅（DPI={dpi_value}）")

    st.download_button(
        label="DPI設定済み画像をまとめてダウンロード (ZIP)",
        data=zip_buffer,
        file_name="resized_images.zip",
        mime="application/zip"
    )
