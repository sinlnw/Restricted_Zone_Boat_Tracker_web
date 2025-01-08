import streamlit as st
st.set_page_config(
    page_title="Ex-stream-ly Cool App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)
def main_page():
    st.title("ehello")


pg = st.navigation([st.Page(main_page,title='หน้าหลัก'), st.Page("web.py", title='สร้างเขต')])
pg.run()