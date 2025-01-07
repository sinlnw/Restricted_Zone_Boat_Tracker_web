import streamlit as st
from calendar import month_abbr
from datetime import datetime
import folium
from streamlit_folium import folium_static, st_folium
START_LOCATION = [13.847332, 100.572258]
st.title("สร้างเขต")

# Initialize map state if not exists
if 'drawn_polygons' not in st.session_state:
    st.session_state.drawn_polygons = []

# Initialize session state for date ranges if not exists
if 'date_ranges' not in st.session_state:
    st.session_state.date_ranges = []

# Initialize selected map index state
if 'selected_map_idx' not in st.session_state:
    st.session_state.selected_map_idx = None

# Container for all date ranges
date_ranges_container = st.container(border=True)
# Add new date range button
if st.button("เพิ่มช่วงวันที่"):
    st.session_state.date_ranges.append({
        'start_date': datetime.now(),
        'end_date': datetime.now()
    })
    st.session_state.drawn_polygons.append(None)  

drawing_options = {
    "polyline": False,
    "rectangle": False,
    "circle": False,
    "marker": False,
    "circlemarker": False,
    "polygon": True
}

# Display all date ranges with drawing buttons
with date_ranges_container:
    for idx, date_range in enumerate(st.session_state.date_ranges):
        # idx-th date_range 
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        
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
        
        # Update session state
        st.session_state.date_ranges[idx]['start_date'] = start_date
        st.session_state.date_ranges[idx]['end_date'] = end_date

# After the date ranges loop - show single map
if st.session_state.selected_map_idx is not None:
    st.divider()
    idx = st.session_state.selected_map_idx
    
    # Create map
    m = folium.Map(location=START_LOCATION, zoom_start=15)
    draw = folium.plugins.Draw(
        export=True,
        position='topleft',
        draw_options=drawing_options,
    )
    m.add_child(draw)
    
    # Show existing polygon if any
    if len(st.session_state.drawn_polygons) > idx and st.session_state.drawn_polygons[idx]:
        folium.GeoJson(st.session_state.drawn_polygons[idx]).add_to(m)
    
    # Display map and capture data
    st.subheader(f"วาดเขตของช่วงเวลา #{idx + 1}")
    map_data = st_folium(m, width=800, height=600, key=f"map_{idx}")
    
    # Save new drawings
    if map_data is not None and "all_drawings" in map_data:
        if map_data["all_drawings"]:
            st.session_state.drawn_polygons[idx] = map_data["all_drawings"][-1]
            st.rerun()
