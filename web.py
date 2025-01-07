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
        'start_day': datetime.now().day,
        'start_month': datetime.now().month,
        'end_day': datetime.now().day,
        'end_month': datetime.now().month
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
        
        # Update session state
        st.session_state.date_ranges[idx]['start_day'] = start_date.day
        st.session_state.date_ranges[idx]['start_month'] = start_date.month
        st.session_state.date_ranges[idx]['end_day'] = end_date.day
        st.session_state.date_ranges[idx]['end_month'] = end_date.month

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
        for polygon in st.session_state.drawn_polygons[idx]:
            if 'geometry' in polygon:
                folium.GeoJson(polygon['geometry']).add_to(m)
                
    # Display map
    st.subheader(f"วาดเขตของช่วงเวลา #{idx + 1}")
    map_data = st_folium(m, width=800, height=600, key=f"map_{idx}")
    
    # Create two columns for buttons
    col1, col2, col3 = st.columns([0.15,0.1,0.75])

    # Add save button in the first column
    with col1:
        if st.button("บันทึก"):
            # Save new/edited drawings
            if map_data is not None and "all_drawings" in map_data:
                if map_data["all_drawings"]:
                    st.session_state.drawn_polygons[idx] = map_data["all_drawings"]
                    st.rerun()

    # Add clear button in the second column
    with col2:
        if st.button("ล้าง"):
            st.session_state.drawn_polygons[idx] = None
            st.rerun()

    #st.write(st.session_state.drawn_polygons[idx])