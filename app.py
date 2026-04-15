st.subheader("3. 生成與下載")
    
    # ✅ 修正 1：建立一個空間來暫存生成的 PDF
    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = None

    if st.button("✨ 生成簽核完成的 PDF", type="primary", use_container_width=True):
        if pdf_file is not None:
            try:
                # ✅ 修正 2：改用 getvalue()，確保每次都能正確讀取檔案內容
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

                # ✅ 修正 3：把生成的 PDF 存進我們剛剛建立的暫存空間
                st.session_state.pdf_bytes = doc.write()
                doc.close()

                st.success("✅ 處理完成！請點擊下方出現的按鈕下載。")
                
            except Exception as e:
                st.error(f"發生錯誤：{e}")
        else:
            st.warning("請先上傳 PDF 檔案！")

    # ✅ 修正 4：把下載按鈕移到「生成按鈕」的外面！
    # 只要暫存空間有東西，這個按鈕就會一直顯示，點擊也不會出錯了
    if st.session_state.pdf_bytes is not None:
        st.download_button(
            label=f"📥 下載 {st.session_state.original_filename}",
            data=st.session_state.pdf_bytes,
            file_name=st.session_state.original_filename,
            mime="application/pdf",
            use_container_width=True
        )
