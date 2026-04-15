import streamlit as st
import fitz  # PyMuPDF 套件
import os

st.set_page_config(page_title="PDF 服務紀錄表編輯器", layout="wide")

st.title("📄 PDF 服務紀錄表即時編輯器 (視覺優化版)")
st.markdown("左側編輯，右側預覽。預覽區已加入**固定大小滾動視窗**，排版不再大暴走！")

# --- 版面佈局 ---
col1, col2 = st.columns([1, 1.2]) # 微調左右比例

with col1:
    st.subheader("1. 檔案與內容")
    pdf_file = st.file_uploader("上傳原始服務紀錄表 (PDF)", type=["pdf"])
    stamp_file = st.file_uploader("上傳服務人員印章 (PNG去背佳)", type=["png", "jpg"])
    
    service_text = st.text_area("輸入「服務經過及結果」內容", height=150)

    st.divider()
    
    st.subheader("2. 位置微調 (X, Y)")
    st.markdown("調整滑桿，右側預覽圖會即時更新。")
    
    text_x = st.slider("📝 文字 X (左右)", 0.0, 600.0, 60.0)
    text_y = st.slider("📝 文字 Y (上下)", 0.0, 800.0, 500.0)
    
    stamp_x = st.slider("🪪 印章 X (左右)", 0.0, 600.0, 400.0)
    stamp_y = st.slider("🪪 印章 Y (上下)", 0.0, 800.0, 700.0)
    stamp_size = st.slider("🪪 印章大小", 10, 200, 80)

# --- 核心：同時生成 PDF 與高畫質預覽圖 ---
def process_pdf(pdf_file, stamp_file, service_text, tx, ty, sx, sy, ssize):
    if pdf_file is None:
        return None, None, None
    
    error_msg = None
    try:
        # 讀取 PDF
        doc = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
        page = doc[0] 

        # 1. 寫入真實文字
        if service_text:
            text_rect = fitz.Rect(tx, ty, tx + 450, ty + 150)
            font_path = "NotoSansTC-VariableFont_wght.ttf"
            
            # 檢查字體是否存在，若不存在則回傳錯誤訊息
            if os.path.exists(font_path):
                page.insert_font(fontname="custom_cjk", fontfile=font_path)
                page.insert_textbox(text_rect, service_text, fontsize=12, fontname="custom_cjk")
            else:
                error_msg = f"⚠️ 警告：找不到字體檔案 '{font_path}'，文字將無法顯示！請確認 GitHub 上有這個檔案。"

        # 2. 貼上真實印章
        if stamp_file is not None:
            img_rect = fitz.Rect(sx, sy, sx + ssize, sy + ssize)
            page.insert_image(img_rect, stream=stamp_file.getvalue())

        # 3. 輸出預覽圖片 (改回 1.5 倍縮放，兼顧清晰度與處理速度)
        mat = fitz.Matrix(1.5, 1.5) 
        pix = page.get_pixmap(matrix=mat)
        preview_img_bytes = pix.tobytes("png")

        # 4. 輸出最終 PDF 檔案給用戶下載
        final_pdf_bytes = doc.write()
        doc.close()
        
        return preview_img_bytes, final_pdf_bytes, error_msg
    except Exception as e:
        return None, None, f"處理時發生錯誤：{e}"

with col2:
    st.subheader("👀 真實排版預覽")
    
    if pdf_file is not None:
        # 取得處理結果
        preview_img, final_pdf, error_message = process_pdf(
            pdf_file, stamp_file, service_text, text_x, text_y, stamp_x, stamp_y, stamp_size
        )
        
        # 如果有錯誤訊息 (例如缺字體)，顯示在最上方
        if error_message:
            st.error(error_message)
        
        if preview_img and final_pdf:
            # ✅ 視覺優化核心：把圖片裝進一個高度為 700px 的可滾動視窗中
            with st.container(height=700, border=True):
                st.image(preview_img, use_container_width=True)
            
            st.divider()
            
            # 下載按鈕
            st.download_button(
                label=f"📥 滿意排版？點擊下載 {pdf_file.name}",
                data=final_pdf,
                file_name=pdf_file.name,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
    else:
        st.info("👉 上傳 PDF 後，這裡會顯示預覽結果。")
