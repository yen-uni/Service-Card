import streamlit as st
import fitz  # PyMuPDF 套件
import os

st.set_page_config(page_title="PDF 服務紀錄表即時編輯器", layout="wide")

st.title("📄 PDF 服務紀錄表即時編輯器 (所見即所得版)")
st.markdown("左側編輯，右側直接看到**真實輸出的高畫質排版**，不再受限於瀏覽器！")

# --- 版面佈局 ---
col1, col2 = st.columns([1, 1.5]) 

with col1:
    st.subheader("1. 檔案與內容")
    pdf_file = st.file_uploader("上傳原始服務紀錄表 (PDF)", type=["pdf"])
    stamp_file = st.file_uploader("上傳服務人員印章 (PNG去背佳)", type=["png", "jpg"])
    
    service_text = st.text_area("輸入「服務經過及結果」內容", height=150, help="支援多行輸入，排版將真實反映在右側預覽中。")

    st.divider()
    
    st.subheader("2. 位置微調 (X, Y)")
    st.markdown("調整滑桿，右側預覽圖會即時更新真實位置。")
    
    text_x = st.slider("📝 文字 X (左右)", 0.0, 600.0, 60.0)
    text_y = st.slider("📝 文字 Y (上下)", 0.0, 800.0, 500.0)
    
    stamp_x = st.slider("🪪 印章 X (左右)", 0.0, 600.0, 400.0)
    stamp_y = st.slider("🪪 印章 Y (上下)", 0.0, 800.0, 700.0)
    stamp_size = st.slider("🪪 印章大小", 10, 200, 80)

# --- 核心：同時生成 PDF 與高畫質預覽圖 ---
def process_pdf(pdf_file, stamp_file, service_text, tx, ty, sx, sy, ssize):
    if pdf_file is None:
        return None, None
    try:
        # 讀取 PDF
        doc = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
        page = doc[0] 

        # 1. 寫入真實文字
        if service_text:
            text_rect = fitz.Rect(tx, ty, tx + 450, ty + 150)
            font_path = "NotoSansTC-VariableFont_wght.ttf"
            if os.path.exists(font_path):
                page.insert_font(fontname="custom_cjk", fontfile=font_path)
                page.insert_textbox(text_rect, service_text, fontsize=12, fontname="custom_cjk")

        # 2. 貼上真實印章
        if stamp_file is not None:
            img_rect = fitz.Rect(sx, sy, sx + ssize, sy + ssize)
            page.insert_image(img_rect, stream=stamp_file.getvalue())

        # 3. 輸出高畫質圖片作為預覽 (放大兩倍確保文字清晰)
        mat = fitz.Matrix(2.0, 2.0) 
        pix = page.get_pixmap(matrix=mat)
        preview_img_bytes = pix.tobytes("png")

        # 4. 輸出最終 PDF 檔案給用戶下載
        final_pdf_bytes = doc.write()
        doc.close()
        
        return preview_img_bytes, final_pdf_bytes
    except Exception as e:
        st.error(f"發生錯誤：{e}")
        return None, None

with col2:
    st.subheader("👀 真實排版預覽")
    
    if pdf_file is not None:
        # 呼叫處理函數，同時取得「預覽圖」和「要下載的 PDF」
        preview_img, final_pdf = process_pdf(pdf_file, stamp_file, service_text, text_x, text_y, stamp_x, stamp_y, stamp_size)
        
        if preview_img and final_pdf:
            # 顯示高畫質圖片預覽，絕對不會被瀏覽器擋住
            st.image(preview_img, caption="這是最終產出的真實樣貌", use_container_width=True)
            
            st.divider()
            
            # 顯示下載按鈕
            st.download_button(
                label=f"📥 滿意排版？點擊下載 {pdf_file.name}",
                data=final_pdf,
                file_name=pdf_file.name,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
    else:
        st.info("👉 上傳 PDF 後，這裡會顯示高畫質的排版結果。")
