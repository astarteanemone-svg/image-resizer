import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile
import os
from math import isnan

APP_TITLE = "印刷向けサイズ指定（cm / DPI）対応 画像ツール"
st.title(APP_TITLE)

# 保存用ディレクトリ
SAVE_DIR = "resized"
os.makedirs(SAVE_DIR, exist_ok=True)

# ========= ユーティリティ =========
CM_PER_INCH = 2.54

def inches_to_cm(inch):
    return inch * CM_PER_INCH

def cm_to_inches(cm):
    return cm / CM_PER_INCH

def px_to_cm(px, dpi):
    return inches_to_cm(px / dpi)

def cm_to_px(cm, dpi):
    return round(cm_to_inches(cm) * dpi)

def describe_size(px_w, px_h, dpi):
    """ピクセル・DPI から印刷時の物理サイズ(cm)を返す"""
    w_cm = px_to_cm(px_w, dpi)
    h_cm = px_to_cm(px_h, dpi)
    return w_cm, h_cm

# ========= 画面上の入力 =========
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
    dpi_input = st.number_input("DPI", min_value=50, max_value=1200, value=300,
                                help="①と④で使用。②③では自動計算します。")

with col2:
    width_cm_input = st.number_input("幅 (cm)", min_value=0.0, value=0.0,
                                     help="②④で使用（②は幅のみ必須、④は幅・高さが必須）")

with col3:
    height_cm_input = st.number_input("高さ (cm)", min_value=0.0, value=0.0,
                                      help="③④で使用（③は高さのみ必須、④は幅・高さが必須）")

preview = st.checkbox("処理後のプレビューを表示する", value=True)

uploaded_files = st.file_uploader(
    "画像をアップロードしてください",
    type=["jpg", "jpeg", "png", "tif", "tiff", "bmp", "webp"],
    accept_multiple_files=True
)

st.caption("ヒント：②③はピクセル数を変えずに印刷サイズを調整します。④はピクセル数も変えます（AI用データや厳密な版面指定向け）。")

# ========= メイン処理 =========
if uploaded_files and prefix.strip():
    processed_items = []  # (filename, img_bytes, info_text)

    for uploaded_file in uploaded_files:
        img = Image.open(uploaded_file)
        img = img.convert("RGB") if img.mode in ("P", "RGBA") else img  # 余計な劣化を避けつつ互換性確保
        orig_w, orig_h = img.size

        # モード別の処理
        out_img = img
        out_dpi = dpi_input

        if mode == "① DPIを直接指定（ピクセルはそのまま）":
            # ピクセルはそのまま、DPIだけ設定
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
                st.error("幅(cm) と 高さ(cm) を入力してください。")
                st.stop()
            # 目標ピクセル数を算出
            target_w = cm_to_px(width_cm_input, dpi_input)
            target_h = cm_to_px(height_cm_input, dpi_input)
            # 高品質リサンプリング（縮小・拡大の両方に強い）
            out_img = img.resize((target_w, target_h), Image.LANCZOS)
            # 過度なボケを避けるために軽くシャープ（必要に応じて）
            if max(orig_w, orig_h) > max(target_w, target_h):
                out_img = out_img.filter(ImageFilter.SHARPEN)
            out_dpi = dpi_input

        # 保存用ファイル名（PNG統一）
        base_name = os.path.splitext(uploaded_file.name)[0]
        new_filename = f"{prefix}_{base_name}.png"

        # 保存（PNG、非劣化、DPI埋め込み）
        save_path = os.path.join(SAVE_DIR, new_filename)
        out_img.save(save_path, format="PNG", dpi=(out_dpi, out_dpi), compress_level=0)

        # ダウンロード用にメモリへ
        img_bytes = io.BytesIO()
        out_img.save(img_bytes, format="PNG", dpi=(out_dpi, out_dpi), compress_level=0)
        img_bytes.seek(0)

        # 情報テキスト
        out_w, out_h = out_img.size
        print_w_cm, print_h_cm = describe_size(out_w, out_h, out_dpi)
        info_text = (
            f"元サイズ: {orig_w}×{orig_h}px  →  出力: {out_w}×{out_h}px, DPI={out_dpi}  "
            f"(印刷時およそ {print_w_cm:.1f}×{print_h_cm:.1f} cm)"
        )

        if preview:
            st.image(out_img, caption=f"{new_filename}\n{info_text}", use_column_width=True)
        else:
            st.caption(f"{new_filename} | {info_text}")

        processed_items.append((new_filename, img_bytes, info_text))

    # ZIP まとめ
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

    # 一覧をテキストでも出しておく
    with st.expander("処理結果の詳細（印刷時の物理サイズなど）"):
        for filename, _, info in processed_items:
            st.write(f"- **{filename}** — {info}")
