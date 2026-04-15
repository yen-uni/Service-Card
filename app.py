import streamlit as st
import fitz  # PyMuPDF 套件
import io
import os
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF 服務紀錄表編輯器", layout="wide")

st.title("📄 PDF 服務紀錄表編輯器 (點擊定位版)")
st.markdown("免拉滑桿！直接點擊右側預覽圖即可精準放置印章與文字。")

# --- 1. 初始化 Session State ---
if "original_filename" not in st.session_state:
    st.session_state.original_filename = "service_record.pdf"
if "text_x" not in st.session_state:
    st.session_state.text_x = 60.0
if "text_y" not in st.session_state:
    st.session_state.text_y = 500.0
if "stamp_x" not in st.session_state:
    st.session_state.stamp_x = 400.0
if "stamp_y" not in st.session_state:
    st.session_state.stamp_y = 700.0
# 新增：用於暫存生成的 PDF 檔案，解決下載錯誤
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

PAGE_WIDTH_PTS = 595.27
PAGE_HEIGHT_PTS = 841.89

# --- 2. 版面佈局 ---
col1, col2 = st.columns([1, 2]) 

with col1:
    st.subheader("1. 檔案與設定")
    pdf_file = st.file_uploader("上傳原始服務紀錄表 (PDF)", type=["pdf"])
    
    if pdf_file is not None:
        st.session_state.original_filename = pdf_file.name

    stamp_file = st.file_uploader("上傳服務人員印章 (PNG去背佳)", type=["png", "jpg"])
    service_text = st.text_area("輸入「服務經過及結果」內容", height=150)
    stamp_size = st.slider("🪪 印章大小微調", 10, 200, 80)

    st.divider()
    
    st.subheader("2. 選擇定位目標")
    st.info("💡 請先選擇下方按鈕，然後點擊右側的 PDF 圖片。")
    click_mode = st.radio("滑鼠點擊將會移動：", ["📝 文字區塊 (左上角)", "🪪 印章位置 (中心點)"])

    st.divider()

    st.subheader("3. 生成與下載")
    # 點擊生成按鈕
    if st.button("✨ 生成簽核完成的 PDF", type="primary", use_container_width=True):
        if pdf_file is not None:
            try:
                # 讀取檔案
                doc = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
                page = doc[0] 

                # 插入文字
                if service_text:
                    tx, ty = st.session_state.text_x, st.session_state.text_y
                    text_rect = fitz.Rect(tx, ty, tx + 450, ty + 150)
                    
                    font_path = "NotoSansTC-VariableFont_wght.ttf"
                    if os.path.exists(font_path):
                        page.insert_font(fontname="custom_cjk", fontfile=font_path)
                        page.insert_textbox(text_rect, service_text, fontsize=12, fontname="custom_cjk")
                    else:
                        st.error("找不到字體檔案！")
                        st.stop()

                # 插入印章圖片
                if stamp_file is not None:
                    sx, sy = st.session_state.stamp_x, st.session_state.stamp_y
                    half_size = stamp_size / 2
                    img_rect = fitz.Rect(sx - half_size, sy - half_size, sx + half_size, sy + half_size)
                    page.insert_image(img_rect, stream=stamp_file.read())

                # 將結果存入暫存區
                st.session_state.pdf_bytes = doc.write()
                doc.close()

                st.success("✅ 處理完成！請點擊下方出現的按鈕下載。")
            except Exception as e:
                st.error(f"發生錯誤：{e}")
        else:
            st.warning("請先上傳 PDF 檔案！")

    # 獨立的下載按鈕 (只要暫存區有東西就會顯示)
    if st.session_state.pdf_bytes is not None:
        st.download_button(
            label=f"📥 下載 {st.session_state.original_filename}",
            data=st.session_state.pdf_bytes,
            file_name=st.session_state.original_filename,
            mime="application/pdf",
            use_container_width=True
        )

with col2:
    st.subheader("👀 點擊定位預覽區")
    if pdf_file is not None:
        try:
            with fitz.open(stream=pdf_file.getvalue(), filetype="pdf") as preview_doc:
                page = preview_doc[0]
                mat = fitz.Matrix(1.5, 1.5) 
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")

            pil_image = Image.open(io.BytesIO(img_data))
            draw = ImageDraw.Draw(pil_image)

            scale_x = pil_image.width / PAGE_WIDTH_PTS
            scale_y = pil_image.height / PAGE_HEIGHT_PTS

            # 繪製文字標記
            txt_marker_x1 = st.session_state.text_x * scale_x
            txt_marker_y1 = st.session_state.text_y * scale_y
            draw.rectangle([txt_marker_x1, txt_marker_y1, txt_marker_x1 + 300, txt_marker_y1 + 100], outline="blue", width=3)
            draw.text((txt_marker_x1, txt_marker_y1 - 15), "📝 文字區", fill="blue")

            # 繪製印章標記
            st_marker_x = st.session_state.stamp_x * scale_x
            st_marker_y = st.session_state.stamp_y * scale_y
            half_st = (stamp_size * scale_x) / 2
            draw.ellipse([st_marker_x - half_st, st_marker_y - half_st, st_marker_x + half_st, st_marker_y + half_st], outline="red", width=3)
            draw.text((st_marker_x - half_st, st_marker_y - half_st - 15), "🪪 印章", fill="red")

            # 顯示可點擊的圖片
            value = streamlit_image_coordinates(pil_image, key="interactive_pdf")

            if value is not None:
                pdf_click_x = value['x'] / scale_x
                pdf_click_y = value['y'] / scale_y

                if click_mode == "📝 文字區塊 (左上角)":
                    st.session_state.text_x = pdf_click_x
                    st.session_state.text_y = pdf_click_y
                    st.rerun() 
                else:
                    st.session_state.stamp_x = pdf_click_x
                    st.session_state.stamp_y = pdf_click_y
                    st.rerun()

        except Exception as e:
            st.error(f"預覽生成發生錯誤：{e}")
    else:
        st.info("👉 上傳 PDF 後，預覽圖會顯示在這裡。")
