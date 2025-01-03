import streamlit as st
from calendar import month_abbr
from datetime import datetime
import folium
from streamlit_folium import folium_static, st_folium

# Initialize map state if not exists
if 'drawn_polygons' not in st.session_state:
    st.session_state.drawn_polygons = {}

# Initialize session state for date ranges if not exists
if 'date_ranges' not in st.session_state:
    st.session_state.date_ranges = []

# Container for all date ranges
date_ranges_container = st.container()
# Add new date range button
if st.button("เพิ่มช่วงวันที่"):
    st.session_state.date_ranges.append({
        'start_date': datetime.now(),
        'end_date': datetime.now()
    })

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
            if st.button("วาดพื้นที่", key=f"draw_{idx}"):
                if map_data.get("last_active_drawing"):
                    st.session_state.drawn_polygons[idx] = map_data["last_active_drawing"]
        
        with col4:
            if st.button("ลบ", key=f"delete_{idx}"):
                if idx in st.session_state.drawn_polygons:
                    del st.session_state.drawn_polygons[idx]
                st.session_state.date_ranges.pop(idx)
                st.rerun()
        
        # Update session state
        st.session_state.date_ranges[idx]['start_date'] = start_date
        st.session_state.date_ranges[idx]['end_date'] = end_date
        
        # Create a new map for this date range
        m = folium.Map(location=[13.7563, 100.5018], zoom_start=10)
        draw = folium.plugins.Draw(
            export=True,
            position='topleft',
            draw_options=drawing_options,
        )
        m.add_child(draw)
        
        # Display saved polygon for this date range
        if idx in st.session_state.drawn_polygons:
            folium.GeoJson(st.session_state.drawn_polygons[idx]).add_to(m)
            st.write(f"พื้นที่ที่วาดสำหรับช่วงวันที่ {idx + 1}:", st.session_state.drawn_polygons[idx])
        
        # Display map for this date range
        map_data = st_folium(m, width=800, height=600, key=f"map_{idx}")
