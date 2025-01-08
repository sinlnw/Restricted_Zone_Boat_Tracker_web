import streamlit as st
import json
from datetime import datetime

if 'date_ranges' not in st.session_state:
    st.session_state.date_ranges = []

if 'all_areas' not in st.session_state:
    st.session_state.all_areas = []

# Dialog for importing AREA.txt
@st.dialog("นำเข้าข้อมูลเขต")
def upload_file():
    uploaded_file = st.file_uploader("Import AREA.txt", type="txt")
    col1, col2, col3 = st.columns([0.2,0.2,0.6])
    with col1:
        if st.button("ยืนยัน") and uploaded_file is not None:
            # Read the file content
            content = uploaded_file.read().decode("utf-8")
            imported_data = json.loads(content)
            
            # Update date_ranges and drawn_polygons in session state
            st.session_state.date_ranges = [
                {
                    "start_day": item["start_day"],
                    "start_month": item["start_month"],
                    "end_day": item["end_day"],
                    "end_month": item["end_month"],
                    "start_date": datetime(datetime.now().year, item["start_month"], item["start_day"]),
                    "end_date": datetime(datetime.now().year, item["end_month"], item["end_day"])
                }
                for item in imported_data
            ]
            st.session_state.all_areas = [item["all_drawings"] for item in imported_data]
            st.rerun()
    with col2:
        if st.button("ปิด"):
            st.rerun()

if st.button("นำเข้าข้อมูลเขต"):
    upload_file()



date_ranges = st.session_state.get('date_ranges', [])
all_areas = st.session_state.get('all_areas', [])

# Create a list to store paired date_ranges and drawn_polygons
if date_ranges and all_areas:
    paired_data = []
    for idx in range(len(date_ranges)):
        paired_data.append({
            "start_day": date_ranges[idx]["start_day"],
            "start_month": date_ranges[idx]["start_month"],
            "end_day": date_ranges[idx]["end_day"],
            "end_month": date_ranges[idx]["end_month"],

            # "start_day": date_ranges[idx]["start_date"].day,
            # "start_month": date_ranges[idx]["start_date"].month,
            # "end_day": date_ranges[idx]["end_date"].day,
            # "end_month": date_ranges[idx]["end_date"].month,
            "all_drawings": all_areas[idx]
        })

    json_data = json.dumps(paired_data, ensure_ascii=False, indent=4)
    st.text_area("ข้อมูลเขต", json_data, height=300)


