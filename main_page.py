import streamlit as st

def main_page():
    st.title("Hello")
    st.title("Plase select a page on the left")


pg = st.navigation([st.Page(main_page,title='หน้าหลัก'), st.Page("web.py", title='สร้างเขต')])
pg.run()