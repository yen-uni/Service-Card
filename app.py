import streamlit as st
import fitz  # PyMuPDF 套件
import os

st.set_page_config(page_title="專屬服務紀錄表編輯器", layout="wide")

st.title("📄 專屬 PDF 編輯器 (印章與文字填寫)")
st.markdown("專為服務紀錄表設計，免安裝付費軟體。")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 檔案與內容輸入")
    pdf_file = st.file_uploader("上傳原始服務紀錄表 (PDF)", type=["pdf"])
    stamp_file = st.file_uploader("上傳服務人員印章 (PNG 格式去背佳)", type=["png", "jpg"])
    service_text = st.text_area("輸入「服務經過及結果」內容", height=150)

with col2:
    st.subheader("2. 位置微調 (X, Y 座標)")
    st.markdown("請依據表單實際位置推拉滑桿")
    
    st.markdown("**📝 文字位置**")
    text_x = st.slider("文字 X 座標 (左右)", 0, 600, 60)
    text_y = st.slider("文字 Y 座標 (上下)", 0, 800, 500)
    
    st.markdown("**🪪 印章位置**")
    stamp_x = st.slider("印章 X 座標 (左右)", 0, 600, 400)
    stamp_y = st.slider("印章 Y 座標 (上下)", 0, 800, 700)
    stamp_size = st.slider("印章大小", 10, 200, 80)

st.divider()

# 執行合併處理
if st.button("✨ 生成更新後的 PDF", type="primary"):
    if pdf_file is not None:
        try:
            # 讀取 PDF
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            page = doc[0] # 預設處理第一頁

            # 插入文字
            if service_text:
                text_rect = fitz.Rect(text_x, text_y, text_x + 450, text_y + 150)
                
                # ✅ 修正：指定讀取 GitHub 上的字體檔案
                font_path = "NotoSansTC-VariableFont_wght.ttf"
                if os.path.exists(font_path):
                    # 將字體註冊進 PDF 並命名為 custom_cjk
                    page.insert_font(fontname="custom_cjk", fontfile=font_path)
                    # 使用剛註冊的字體寫入文字
                    page.insert_textbox(text_rect, service_text, fontsize=12, fontname="custom_cjk")
                else:
                    st.error("找不到字體檔案！請確認 NotoSansTC-Regular.ttf 已上傳至 GitHub 的同一層目錄下。")
                    st.stop()

            # 插入印章圖片
            if stamp_file is not None:
                img_rect = fitz.Rect(stamp_x, stamp_y, stamp_x + stamp_size, stamp_y + stamp_size)
                page.insert_image(img_rect, stream=stamp_file.read())

            # 輸出並提供下載
            pdf_bytes = doc.write()
            st.success("✅ 處理完成！請點擊下方按鈕下載。")
            st.download_button(
                label="📥 下載簽核完成的 PDF",
                data=pdf_bytes,
                file_name="signed_service_record.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"發生錯誤：{e}")
    else:
        st.warning("請先上傳原始的 PDF 表單檔案！")
