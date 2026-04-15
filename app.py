import streamlit as st
import fitz  # PyMuPDF 套件
import base64
import os

st.set_page_config(page_title="PDF 服務紀錄表即時編輯器", layout="wide")

st.title("📄 PDF 服務紀錄表即時編輯器 (所見即所得版)")
st.markdown("左側編輯，右側直接看到**真實輸出的 PDF 畫面**，文字排版一目了然！")

# --- 版面佈局 ---
col1, col2 = st.columns([1, 1.5]) # 左邊設定，右邊預覽

with col1:
    st.subheader("1. 檔案與內容")
    pdf_file = st.file_uploader("上傳原始服務紀錄表 (PDF)", type=["pdf"])
    stamp_file = st.file_uploader("上傳服務人員印章 (PNG去背佳)", type=["png", "jpg"])
    
    # 使用 on_change 讓輸入文字時即刻觸發重新渲染
    service_text = st.text_area("輸入「服務經過及結果」內容", height=150, help="支援多行輸入，排版將真實反映在右側預覽中。")

    st.divider()
    
    st.subheader("2. 位置微調 (X, Y)")
    st.markdown("調整滑桿，右側 PDF 會即時更新真實位置。")
    
    # 文字位置滑桿
    text_x = st.slider("📝 文字 X (左右)", 0.0, 600.0, 60.0)
    text_y = st.slider("📝 文字 Y (上下)", 0.0, 800.0, 500.0)
    
    # 印章位置滑桿
    stamp_x = st.slider("🪪 印章 X (左右)", 0.0, 600.0, 400.0)
    stamp_y = st.slider("🪪 印章 Y (上下)", 0.0, 800.0, 700.0)
    stamp_size = st.slider("🪪 印章大小", 10, 200, 80)

# --- 核心：即時生成 PDF 函數 ---
def generate_pdf(pdf_file, stamp_file, service_text, tx, ty, sx, sy, ssize):
    if pdf_file is None:
        return None
    try:
        doc = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
        page = doc[0] 

        # 插入真實文字
        if service_text:
            text_rect = fitz.Rect(tx, ty, tx + 450, ty + 150)
            font_path = "NotoSansTC-VariableFont_wght.ttf"
            if os.path.exists(font_path):
                page.insert_font(fontname="custom_cjk", fontfile=font_path)
                page.insert_textbox(text_rect, service_text, fontsize=12, fontname="custom_cjk")

        # 插入真實印章
        if stamp_file is not None:
            img_rect = fitz.Rect(sx, sy, sx + ssize, sy + ssize)
            page.insert_image(img_rect, stream=stamp_file.getvalue())

        pdf_bytes = doc.write()
        doc.close()
        return pdf_bytes
    except Exception as e:
        st.error(f"生成 PDF 發生錯誤：{e}")
        return None

with col2:
    st.subheader("👀 真實 PDF 預覽")
    
    if pdf_file is not None:
        # 只要左邊有任何變動，就會重新呼叫生成函數
        live_pdf_bytes = generate_pdf(pdf_file, stamp_file, service_text, text_x, text_y, stamp_x, stamp_y, stamp_size)
        
        if live_pdf_bytes:
            # 將產生的 PDF 轉換為 base64 編碼，直接嵌在網頁的 iframe 裡顯示
            base64_pdf = base64.b64encode(live_pdf_bytes).decode('utf-8')
            # 調整高度讓整頁 A4 都可以顯示出來
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            # --- 3. 下載區 (移到預覽圖下方) ---
            st.divider()
            st.download_button(
                label=f"📥 滿意排版？點擊下載 {pdf_file.name}",
                data=live_pdf_bytes,
                file_name=pdf_file.name,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
    else:
        st.info("👉 上傳 PDF 後，這裡會顯示真實的排版結果。")
