import streamlit as st

def main_page():
    st.title("อุปกรณ์ตรวจสอบการเข้าเขตห้ามจับสัตว์นํ้า ")
    st.subheader("กรุณาเลือกหน้าด้านล่าง")

    col1, col2 = st.columns([1, 1])
    st.write("\n")
    st.write("\n")
    st.write("\n")
    with col1:
        st.page_link(page="web.py",label="สร้างเขต")
    with col2:
        st.page_link(page="view_tracking_page.py",label="ประวัติตำแหน่ง")


pg = st.navigation([st.Page(main_page,title='หน้าหลัก'), st.Page("web.py", title='สร้างเขต'),st.Page("view_tracking_page.py", title='ประวัติตำแหน่ง')])
pg.run()