import streamlit as st
from calendar import month_abbr
from datetime import datetime
import folium
from streamlit_folium import folium_static, st_folium
from calendar import month_name, monthrange
import json
START_LOCATION = [13.847332, 100.572258]
DEFAULT_ZOOM = 15


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
    st.session_state.drawn_polygons = [] # the format is the same as all_drawings in st_folium

if 'date_ranges' not in st.session_state:
    st.session_state.date_ranges = []

if 'centers' not in st.session_state:
    st.session_state.centers = []

if 'zoom_levels' not in st.session_state:
    st.session_state.zoom_levels = []

if 'selected_map_idx' not in st.session_state:
    st.session_state.selected_map_idx = None

# Function to get the number of days in a given month and year
def get_days_in_month(month, year=2023):
    month_idx = list(month_name).index(month)
    return list(range(1, monthrange(year, month_idx)[1] + 1))

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
            st.session_state.drawn_polygons = [item.get("all_drawings", None) for item in imported_data]
            st.session_state.centers = [item.get("center", START_LOCATION) for item in imported_data]
            st.session_state.zoom_levels = [item.get("zoom", DEFAULT_ZOOM) for item in imported_data]
            st.rerun()
    with col2:
        if st.button("ปิด"):
            st.rerun()



st.title("สร้างเขต")

# Button to open dialog for importing AREA.txt
if st.button("นำเข้าข้อมูลเขต"):
    upload_file()

# Container for all date ranges
date_ranges_container = st.container(border=True)

# add date range
if st.button("เพิ่มช่วงวันที่"):
    st.session_state.date_ranges.append({
        'start_date': datetime.now(),
        'end_date': datetime.now(),
        'start_day':datetime.now().day,
        'start_month':datetime.now().month,
        'end_day':datetime.now().day,
        'end_month':datetime.now().month
    })
    st.session_state.drawn_polygons.append(None)
    st.session_state.centers.append(START_LOCATION)
    st.session_state.zoom_levels.append(DEFAULT_ZOOM)


months = list(month_name)[1:]

# Display all date ranges
with date_ranges_container:
    for idx, date_range in enumerate(st.session_state.date_ranges):
        # idx-th date_range 
        col1, col2, col3, col4 = st.columns([2, 2, 1.05, 1],vertical_alignment="bottom")
        with col1:
            start_month = st.selectbox(
            f"เดือนเริ่มต้น #{idx + 1}",
            options=months,
            index=date_range['start_month'] - 1,
            key=f"start_month_{idx}"
            )
            start_day = st.selectbox(
            f"วันที่เริ่มต้น #{idx + 1}",
            options=get_days_in_month(start_month),
            index=date_range['start_day'] - 1,
            key=f"start_day_{idx}"
            )
            
        
        with col2:
            end_month = st.selectbox(
            f"เดือนสิ้นสุด #{idx + 1}",
            options=months,
            index=date_range['end_month'] - 1,
            key=f"end_month_{idx}"
            )
            end_day = st.selectbox(
            f"วันที่สิ้นสุด #{idx + 1}",
            options=get_days_in_month(end_month),
            index=date_range['end_day'] - 1,
            key=f"end_day_{idx}"
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
        #st.session_state.date_ranges[idx]['start_date'] = start_date
        #st.session_state.date_ranges[idx]['end_date'] = end_date
        st.session_state.date_ranges[idx]['start_day'] = start_day
        st.session_state.date_ranges[idx]['start_month'] = list(month_name).index(start_month)
        st.session_state.date_ranges[idx]['end_day'] = end_day
        st.session_state.date_ranges[idx]['end_month'] = list(month_name).index(end_month)
        st.divider()

# show map to draw polygon
if st.session_state.selected_map_idx is not None:
    st.divider()
    idx = st.session_state.selected_map_idx
    
  
    m = folium.Map(location=st.session_state.centers[idx], zoom_start=st.session_state.zoom_levels[idx])
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

                    # Update center and zoom level
                    st.session_state.centers[idx] = [map_data["center"]["lat"], map_data["center"]["lng"]]
                    st.session_state.zoom_levels[idx] = map_data["zoom"]
                    st.rerun()

    # clear button for polygon
    with col2:
        if st.button("ล้าง"):
            st.session_state.drawn_polygons[idx] = None
            st.rerun()

    #st.write(st.session_state.drawn_polygons[idx])



# export button for exporting AREA.txt
date_ranges = st.session_state.get('date_ranges', [])
drawn_polygons = st.session_state.get('drawn_polygons', [])

# Create a list to store paired date_ranges and drawn_polygons
paired_data = []
for idx in range(len(date_ranges)):
    paired_data.append({
        "start_day": date_ranges[idx]["start_day"],
        "start_month": date_ranges[idx]["start_month"],
        "end_day": date_ranges[idx]["end_day"],
        "end_month": date_ranges[idx]["end_month"],
        "center":[st.session_state.centers[idx][0], st.session_state.centers[idx][1]],
        "zoom":st.session_state.zoom_levels[idx],
        # "start_day": date_ranges[idx]["start_date"].day,
        # "start_month": date_ranges[idx]["start_date"].month,
        # "end_day": date_ranges[idx]["end_date"].day,
        # "end_month": date_ranges[idx]["end_date"].month,
        "all_drawings": drawn_polygons[idx]
    })

json_data = json.dumps(paired_data, ensure_ascii=False, indent=4)

st.text_area("ข้อมูลเขต", json_data, height=300)


# download button for AREA file
st.download_button(
    label="ดาวน์โหลด ข้อมูลเขต",
    data=json_data,
    file_name="AREA.txt",
    mime="application/json"
)


