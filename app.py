import streamlit as st
from PIL import Image
import io
import zipfile
import os

st.title("画像リサイズアプリ")

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
        resized_image = image.resize((width, height))

        # 新しいファイル名（拡張子PNGに統一）
        base_name = os.path.splitext(uploaded_file.name)[0]  # 拡張子除去
        new_filename = f"{prefix}_{base_name}.png"

        # 保存（サーバー側）
        save_path = os.path.join(SAVE_DIR, new_filename)
        resized_image.save(save_path, format="PNG")

        # ダウンロード用にバッファへ
        resized_images.append((new_filename, resized_image))

    # ダウンロード用ZIPを作成
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for filename, img in resized_images:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            zip_file.writestr(filename, img_bytes.getvalue())
    zip_buffer.seek(0)

    st.success(f"リサイズ画像は `{SAVE_DIR}/` フォルダに保存されました ✅")

    st.download_button(
        label="リサイズ済み画像をまとめてダウンロード (ZIP)",
        data=zip_buffer,
        file_name="resized_images.zip",
        mime="application/zip"
    )
