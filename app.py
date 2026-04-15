import streamlit as st
import fitz  # PyMuPDF 套件
import io
import os
from PIL import Image, ImageDraw

st.set_page_config(page_title="PDF 服務紀錄表智慧編輯器", layout="wide")

st.title("📄 PDF 服務紀錄表智慧編輯器")
st.markdown("專為服務紀錄表設計，提供視覺化智慧預覽對位，免安裝付費軟體。")

# 初始化 Session State 用於儲存原始檔名
if "original_filename" not in st.session_state:
    st.session_state.original_filename = "service_record.pdf" # 預設

col1, col2 = st.columns([1, 1.5]) # 調整比例，預覽圖大一點

# 定義 PDF 頁面在 72 PPI 下的標準 A4 寬高 (點)
PAGE_WIDTH_PTS = 595.27
PAGE_HEIGHT_PTS = 841.89

with col1:
    st.subheader("1. 檔案與內容輸入")
    pdf_file = st.file_uploader("上傳原始服務紀錄表 (PDF)", type=["pdf"])
    
    # ✅ 修正：抓取並儲存原始檔名
    if pdf_file is not None:
        st.session_state.original_filename = pdf_file.name

    stamp_file = st.file_uploader("上傳服務人員印章 (PNG去背佳)", type=["png", "jpg"])
    service_text = st.text_area("輸入「服務經過及結果」內容", height=150)

    st.divider()

    # 執行合併處理
    st.subheader("3. 生成與下載")
    if st.button("✨ 生成簽核完成的 PDF", type="primary"):
        if pdf_file is not None:
            try:
                # 重新讀取 PDF 用於處理 (因為 file_uploader 的 stream 只能讀一次)
                doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
                page = doc[0] 

                # 插入文字
                if service_text and 'text_x' in st.session_state:
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
                if stamp_file is not None and 'stamp_x' in st.session_state:
                    sx, sy, ss = st.session_state.stamp_x, st.session_state.stamp_y, st.session_state.stamp_size
                    img_rect = fitz.Rect(sx, sy, sx + ss, sy + ss)
                    page.insert_image(img_rect, stream=stamp_file.read())

                # 輸出並提供下載
                pdf_bytes = doc.write()
                doc.close()

                st.success("✅ 處理完成！請點擊下方按鈕下載，並**選擇與原始檔案相同的路徑進行覆蓋。**")
                
                # ✅ 修正：下載時使用原始檔名
                st.download_button(
                    label=f"📥 下載 {st.session_state.original_filename}",
                    data=pdf_bytes,
                    file_name=st.session_state.original_filename, # 使用原始檔名
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"發生錯誤：{e}")
        else:
            st.warning("請先上傳 PDF 檔案！")

with col2:
    st.subheader("2. 位置微調與智慧預覽")
    
    # 📝 文字位置滑桿 (直接使用 session state 儲存)
    st.session_state.text_x = st.slider("📝 文字 X (左右)", 0.0, PAGE_WIDTH_PTS, 60.0)
    st.session_state.text_y = st.slider("📝 文字 Y (上下)", 0.0, PAGE_HEIGHT_PTS, 500.0)
    
    # 🪪 印章位置滑桿
    st.session_state.stamp_x = st.slider("🪪 印章 X (左右)", 0.0, PAGE_WIDTH_PTS, 400.0)
    st.session_state.stamp_y = st.slider("🪪 印章 Y (上下)", 0.0, PAGE_HEIGHT_PTS, 700.0)
    st.session_state.stamp_size = st.slider("🪪 印章大小", 10, 200, 80)

    st.divider()

    # --- 智慧預覽邏輯 ---
    if pdf_file is not None:
        try:
            # 1. 將 PDF 第 1 頁渲染為圖片 (放大 2 倍以提高清晰度)
            # 使用副本讀取以防干擾
            with fitz.open(stream=pdf_file.getvalue(), filetype="pdf") as preview_doc:
                page = preview_doc[0]
                mat = fitz.Matrix(2.0, 2.0) # 2x zoom
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")

            # 2. 使用 PIL (Pillow) 載入圖片並繪製標記
            pil_image = Image.open(io.BytesIO(img_data))
            draw = ImageDraw.Draw(pil_image)

            # 計算 PDF 座標點 -> 圖片像素的縮放比例
            scale_x = pil_image.width / PAGE_WIDTH_PTS
            scale_y = pil_image.height / PAGE_HEIGHT_PTS

            # 繪製文字區域標記 (藍色框)
            txt_marker_x1 = st.session_state.text_x * scale_x
            txt_marker_y1 = st.session_state.text_y * scale_y
            txt_box_w = 400 * scale_x # 假設一個文字框寬度作參考
            txt_box_h = 150 * scale_y # 假設一個文字框高度作參考
            draw.rectangle([txt_marker_x1, txt_marker_y1, txt_marker_x1 + txt_box_w, txt_marker_y1 + txt_box_h], outline="blue", width=4)

            # 繪製印章位置標記 (紅色圈)
            st_marker_x1 = st.session_state.stamp_x * scale_x
            st_marker_y1 = st.session_state.stamp_y * scale_y
            st_size = st.session_state.stamp_size * scale_x
            draw.ellipse([st_marker_x1, st_marker_y1, st_marker_x1 + st_size, st_marker_y1 + st_size], outline="red", width=4)

            # 3. 顯示預覽圖
            st.image(pil_image, caption=f"智慧預覽圖 ({st.session_state.original_filename}) - 藍框：文字區，紅圈：印章", use_container_width=True)

        except Exception as e:
            st.error(f"預覽生成發生錯誤：{e}")
    else:
        # 顯示一個提示圖片或文字
        st.info("請上傳原始 PDF 檔案以開啟智慧預覽。")
