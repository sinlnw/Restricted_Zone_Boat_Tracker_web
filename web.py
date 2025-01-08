import streamlit as st
from calendar import month_abbr
from datetime import datetime
import folium
from streamlit_folium import folium_static, st_folium
import json
START_LOCATION = [13.847332, 100.572258]
st.title("สร้างเขต")

drawing_options = {
    "polyline": False,
    "rectangle": False,
    "circle": False,
    "marker": False,
    "circlemarker": False,
    "polygon": True
}

# Initialize session state
if 'drawn_polygons' not in st.session_state:
    st.session_state.drawn_polygons = []

if 'date_ranges' not in st.session_state:
    st.session_state.date_ranges = []

if 'selected_map_idx' not in st.session_state:
    st.session_state.selected_map_idx = None

# Container for all date ranges
date_ranges_container = st.container(border=True)

# add date range
if st.button("เพิ่มช่วงวันที่"):
    st.session_state.date_ranges.append({
        'start_date': datetime.now(),
        'end_date': datetime.now()
    })
    st.session_state.drawn_polygons.append(None)  


# Display all date ranges
with date_ranges_container:
    for idx, date_range in enumerate(st.session_state.date_ranges):
        # idx-th date_range 
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1],vertical_alignment="bottom")
        
        with col1:
            start_date = st.date_input(
                f"วันที่เริ่มต้น #{idx + 1}",
                value=date_range['start_date'],
                key=f"start_{idx}"
            )
        
        with col2:
            end_date = st.date_input(
                f"วันที่สิ้นสุด #{idx + 1}",
                value=date_range['end_date'],
                key=f"end_{idx}"
            )
        
        with col3:
            if st.button("แสดงแผนที่", key=f"show_{idx}"):
                st.session_state.selected_map_idx = idx if st.session_state.selected_map_idx != idx else None
                st.rerun()
        
        with col4:
            if st.button("ลบ", key=f"delete_{idx}"):
                st.session_state.drawn_polygons.pop(idx)
                st.session_state.date_ranges.pop(idx)
                st.rerun()
        
        # Update date
        st.session_state.date_ranges[idx]['start_date'] = start_date
        st.session_state.date_ranges[idx]['end_date'] = end_date

# show map to draw polygon
if st.session_state.selected_map_idx is not None:
    st.divider()
    idx = st.session_state.selected_map_idx
    
  
    m = folium.Map(location=START_LOCATION, zoom_start=15)
    draw = folium.plugins.Draw(
        export=True,
        position='topleft',
        draw_options=drawing_options,
    )
    m.add_child(draw)
    
    # Show existing polygon if any
    if len(st.session_state.drawn_polygons) > idx and st.session_state.drawn_polygons[idx]:
        for polygon in st.session_state.drawn_polygons[idx]:
            if 'geometry' in polygon:
                folium.GeoJson(polygon['geometry']).add_to(m)
                
    # Display map
    st.subheader(f"วาดเขตของช่วงเวลา #{idx + 1}")
    map_data = st_folium(m, width=800, height=600, key=f"map_{idx}")
    
    col1, col2, col3 = st.columns([0.15,0.1,0.75])

    # save button for polygon
    with col1:
        if st.button("บันทึก"):
            # Save new/edited drawings
            if map_data is not None and "all_drawings" in map_data:
                if map_data["all_drawings"]:
                    st.session_state.drawn_polygons[idx] = map_data["all_drawings"]
                    st.rerun()

    # clear button for polygon
    with col2:
        if st.button("ล้าง"):
            st.session_state.drawn_polygons[idx] = None
            st.rerun()

    #st.write(st.session_state.drawn_polygons[idx])


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
                    "start_date": datetime(datetime.now().year, item["start_month"], item["start_day"]),
                    "end_date": datetime(datetime.now().year, item["end_month"], item["end_day"])
                }
                for item in imported_data
            ]
            st.session_state.drawn_polygons = [item["all_drawings"] for item in imported_data]
            st.rerun()
    with col2:
        if st.button("ปิด"):
            st.rerun()

# Button to open dialog for importing AREA.txt
if st.button("นำเข้าข้อมูลเขต"):
    upload_file()



# export button for exporting AREA.txt
date_ranges = st.session_state.get('date_ranges', [])
drawn_polygons = st.session_state.get('drawn_polygons', [])

# Create a list to store paired date_ranges and drawn_polygons
paired_data = []
for idx in range(len(date_ranges)):
    paired_data.append({
        "start_day": date_ranges[idx]["start_date"].day,
        "start_month": date_ranges[idx]["start_date"].month,
        "end_day": date_ranges[idx]["end_date"].day,
        "end_month": date_ranges[idx]["end_date"].month,
        "all_drawings": drawn_polygons[idx]
    })

json_data = json.dumps(paired_data, ensure_ascii=False, indent=4)

st.text_area("ข้อมูลเขต", json_data, height=300)

# Optionally, provide a download button
st.download_button(
    label="ดาวน์โหลด ข้อมูลเขต",
    data=json_data,
    file_name="AREA.txt",
    mime="application/json"
)