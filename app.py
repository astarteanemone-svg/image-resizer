import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile
import os

st.title("高画質 画像リサイズアプリ")

# 保存用ディレクトリ
SAVE_DIR = "resized"
os.makedirs(SAVE_DIR, exist_ok=True)

# プレフィックス入力
prefix = st.text_input("リサイズ画像のファイル名に付けるPrefix", value="resized")

# サイズ指定
width = st.number_input("横サイズ(px)", min_value=1, value=256)
height = st.number_input("縦サイズ(px)", min_value=1, value=256)

# ファイルアップロード（複数可）
uploaded_files = st.file_uploader(
    "画像をアップロードしてください", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files and prefix.strip():
    resized_images = []
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)

        # 高品質リサイズ（縮小に強い）
        resized_image = image.resize((width, height), Image.LANCZOS)

        # 追加のシャープ処理でクッキリさせる
        resized_image = resized_image.filter(ImageFilter.SHARPEN)

        # 新しいファイル名（PNG統一）
        base_name = os.path.splitext(uploaded_file.name)[0]
        new_filename = f"{prefix}_{base_name}.png"

        # サーバー側に保存（圧縮劣化を抑える設定）
        save_path = os.path.join(SAVE_DIR, new_filename)
        resized_image.save(save_path, format="PNG", optimize=True, compress_level=0)

        # ダウンロード用に保持
        resized_images.append((new_filename, resized_image))

    # ダウンロード用ZIPを作成
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for filename, img in resized_images:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG", optimize=True, compress_level=0)
            zip_file.writestr(filename, img_bytes.getvalue())
    zip_buffer.seek(0)

    st.success(f"リサイズ画像は `{SAVE_DIR}/` フォルダに保存されました ✅")

    st.download_button(
        label="リサイズ済み画像をまとめてダウンロード (ZIP)",
        data=zip_buffer,
        file_name="resized_images.zip",
        mime="application/zip"
    )
