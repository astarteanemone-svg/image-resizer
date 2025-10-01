import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile
import os

APP_TITLE = "印刷向け 画像変換ツール（cm指定 / DPI計算 / JPEG・PNG選択 / 最大幅指定対応）"
st.title(APP_TITLE)

# 保存用ディレクトリ
SAVE_DIR = "resized"
os.makedirs(SAVE_DIR, exist_ok=True)

# 定数
CM_PER_INCH = 2.54

def cm_to_inches(cm):
    return cm / CM_PER_INCH

def inches_to_cm(inch):
    return inch * CM_PER_INCH

def px_to_cm(px, dpi):
    return inches_to_cm(px / dpi)

def cm_to_px(cm, dpi):
    return round(cm_to_inches(cm) * dpi)

def describe_size(px_w, px_h, dpi):
    w_cm = px_to_cm(px_w, dpi)
    h_cm = px_to_cm(px_h, dpi)
    return w_cm, h_cm

# ========= 入力UI =========
prefix = st.text_input("保存ファイル名に付けるPrefix", value="resized")

mode = st.selectbox(
    "サイズ指定モード",
    [
        "① DPIを直接指定（ピクセルはそのまま）",
        "② 幅（cm）だけ指定 → DPIを自動計算（ピクセルはそのまま）",
        "③ 高さ（cm）だけ指定 → DPIを自動計算（ピクセルはそのまま）",
        "④ 幅×高さ（cm）とDPIを指定 → そのピクセル数にリサンプリング（ピクセルを変更）"
    ],
    index=0
)

col1, col2, col3 = st.columns(3)
with col1:
    dpi_input = st.number_input("DPI", min_value=50, max_value=1200, value=300)
with col2:
    width_cm_input = st.number_input("幅 (cm)", min_value=0.0, value=0.0)
with col3:
    height_cm_input = st.number_input("高さ (cm)", min_value=0.0, value=0.0)

# 保存形式の選択
format_choice = st.selectbox("保存形式を選んでください", ["JPEG", "PNG"])

# 最大幅指定
max_width = st.number_input("出力画像の最大幅(px)", min_value=500, max_value=8000, value=1200,
                            help="ここで指定した幅を超える画像は自動で縮小されます")

preview = st.checkbox("処理後のプレビューを表示する", value=True)

uploaded_files = st.file_uploader(
    "画像をアップロードしてください",
    type=["jpg", "jpeg", "png", "tif", "tiff", "bmp", "webp"],
    accept_multiple_files=True
)

st.caption("ヒント：②③はピクセル数を変えずに印刷サイズを調整します。④はピクセル数も変えます。最大幅を超える画像は自動で縮小されます。")

# ========= メイン処理 =========
if uploaded_files and prefix.strip():
    processed_items = []

    for uploaded_file in uploaded_files:
        img = Image.open(uploaded_file)
        img = img.convert("RGB") if format_choice == "JPEG" else img
        orig_w, orig_h = img.size

        out_img = img
        out_dpi = dpi_input

        if mode == "① DPIを直接指定（ピクセルはそのまま）":
            out_dpi = dpi_input

        elif mode == "② 幅（cm）だけ指定 → DPIを自動計算（ピクセルはそのまま）":
            if width_cm_input <= 0:
                st.error("幅(cm)を入力してください。")
                st.stop()
            out_dpi = round(orig_w / cm_to_inches(width_cm_input))

        elif mode == "③ 高さ（cm）だけ指定 → DPIを自動計算（ピクセルはそのまま）":
            if height_cm_input <= 0:
                st.error("高さ(cm)を入力してください。")
                st.stop()
            out_dpi = round(orig_h / cm_to_inches(height_cm_input))

        elif mode == "④ 幅×高さ（cm）とDPIを指定 → そのピクセル数にリサンプリング（ピクセルを変更）":
            if width_cm_input <= 0 or height_cm_input <= 0:
                st.error("幅(cm)と高さ(cm)を入力してください。")
                st.stop()
            target_w = cm_to_px(width_cm_input, dpi_input)
            target_h = cm_to_px(height_cm_input, dpi_input)
            out_img = img.resize((target_w, target_h), Image.LANCZOS)
            if max(orig_w, orig_h) > max(target_w, target_h):
                out_img = out_img.filter(ImageFilter.SHARPEN)
            out_dpi = dpi_input

        # 最大幅制御（縮小のみ）
        if out_img.width > max_width:
            new_height = int(out_img.height * (max_width / out_img.width))
            out_img = out_img.resize((max_width, new_height), Image.LANCZOS)

        # 保存ファイル名
        ext = "jpg" if format_choice == "JPEG" else "png"
        new_filename = f"{prefix}_{os.path.splitext(uploaded_file.name)[0]}.{ext}"
        save_path = os.path.join(SAVE_DIR, new_filename)

        # 保存
        img_bytes = io.BytesIO()
        if format_choice == "JPEG":
            out_img.save(
                save_path,
                format="JPEG",
                quality=90,
                subsampling=0,
                dpi=(out_dpi, out_dpi)
            )
            out_img.save(
                img_bytes,
                format="JPEG",
                quality=90,
                subsampling=0,
                dpi=(out_dpi, out_dpi)
            )
        else:
            out_img.save(
                save_path,
                format="PNG",
                dpi=(out_dpi, out_dpi),
                compress_level=0
            )
            out_img.save(
                img_bytes,
                format="PNG",
                dpi=(out_dpi, out_dpi),
                compress_level=0
            )
        img_bytes.seek(0)

        # 出力情報
        out_w, out_h = out_img.size
        print_w_cm, print_h_cm = describe_size(out_w, out_h, out_dpi)
        info_text = (
            f"元サイズ: {orig_w}×{orig_h}px → 出力: {out_w}×{out_h}px, "
            f"DPI={out_dpi}（印刷時およそ {print_w_cm:.1f}×{print_h_cm:.1f} cm）"
        )

        if preview:
            st.image(out_img, caption=f"{new_filename}\n{info_text}", use_column_width=True)
        else:
            st.caption(f"{new_filename} | {info_text}")

        processed_items.append((new_filename, img_bytes, info_text))

    # ZIPまとめ
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for filename, img_bytes, _ in processed_items:
            zipf.writestr(filename, img_bytes.getvalue())
    zip_buffer.seek(0)

    st.success(f"処理済み画像は `{SAVE_DIR}/` に保存されました。")

    st.download_button(
        label="処理済み画像をまとめてダウンロード (ZIP)",
        data=zip_buffer,
        file_name="processed_images.zip",
        mime="application/zip"
    )

    with st.expander("処理結果の詳細"):
        for filename, _, info in processed_items:
            st.write(f"- **{filename}** — {info}")
