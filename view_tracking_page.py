import streamlit as st
import json
from datetime import datetime
import pymongo
import folium
from streamlit_folium import st_folium

boat_data = {"เรือ 1": 1}

if "date_ranges" not in st.session_state:
    st.session_state.date_ranges = []
if "all_areas" not in st.session_state:
    st.session_state.all_areas = []
if "filter_date_range" not in st.session_state:
    st.session_state.filter_date_range = (datetime.now(), datetime.now())
if "filter_boat" not in st.session_state:
    st.session_state.filter_boat = list(boat_data.keys())[0]
if "gps_coords" not in st.session_state:
    st.session_state.gps_coords = []


example_gps_coords = {
    "_id": {"$oid": "6777a8dadabd12fbd3985eac"},
    "recorded_time": {"$date": "2024-12-13T10:12:28.000Z"},
    "received_time": {"$date": "2025-01-03T16:07:37.368Z"},
    "device": 1,
    "lat": 13.8468624,
    "lon": 100.5686336,
    "vbat": 2.81,
    "quality": 1,
    "satellites": 3,
    "temperature": 231,
    "ttf": 78.976,
    "rssi": -70,
}
START_LOCATION = [13.847332, 100.572258]
ZOOM_START = 15

st.title("ประวัติตำแหน่ง")


# Dialog for importing AREA.txt
@st.dialog("นำเข้าข้อมูลเขต")
def upload_file():
    uploaded_file = st.file_uploader("Import AREA.txt", type="txt")
    col1, col2, col3 = st.columns([0.2, 0.2, 0.6])
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
                    "start_date": datetime(
                        datetime.now().year, item["start_month"], item["start_day"]
                    ),
                    "end_date": datetime(
                        datetime.now().year, item["end_month"], item["end_day"]
                    ),
                }
                for item in imported_data
            ]
            st.session_state.all_areas = [
                item["all_drawings"] for item in imported_data
            ]
            st.rerun()
    with col2:
        if st.button("ปิด"):
            st.rerun()


def display_areas_data():
    date_ranges = st.session_state.get("date_ranges", [])
    all_areas = st.session_state.get("all_areas", [])

    # Create a list to store paired date_ranges and drawn_polygons
    if date_ranges and all_areas:
        paired_data = []
        for idx in range(len(date_ranges)):
            paired_data.append(
                {
                    "start_day": date_ranges[idx]["start_day"],
                    "start_month": date_ranges[idx]["start_month"],
                    "end_day": date_ranges[idx]["end_day"],
                    "end_month": date_ranges[idx]["end_month"],
                    # "start_day": date_ranges[idx]["start_date"].day,
                    # "start_month": date_ranges[idx]["start_date"].month,
                    # "end_day": date_ranges[idx]["end_date"].day,
                    # "end_month": date_ranges[idx]["end_date"].month,
                    "all_drawings": all_areas[idx],
                }
            )

        json_data = json.dumps(paired_data, ensure_ascii=False, indent=4)
        st.text_area("ข้อมูลเขต", json_data, height=300)


@st.cache_resource
def init_connection():
    return pymongo.MongoClient(**st.secrets["mongo"])


# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_data(filter_date_range: tuple[datetime], device: str):
    start_date, end_date = filter_date_range
    db = client["test"]
    query_filter = {
        "recorded_time": {
            "$gte": datetime.combine(start_date, datetime.min.time()),
            "$lte": datetime.combine(end_date, datetime.max.time()),
        },
        "device": boat_data[device],
    }
    projection = {"recorded_time": 1, "device": 1, "lat": 1, "lon": 1, "vbat": 1}
    items = (
        db["coordinate"]
        .find(filter=query_filter, projection=projection)
        .sort("recorded_time", pymongo.ASCENDING)
    )

    items = list(items)  # make hashable for st.cache_data

    return items


def plot_gps_coords(gps_coords):
    # Create a Folium map
    m = folium.Map(location=START_LOCATION, zoom_start=ZOOM_START)

    # Add markers to the map
    for coord in gps_coords:
        #continue
        folium.CircleMarker(
            location=[coord["lat"], coord["lon"]],
            radius=3,  # Size of the dot
            color="blue",
            fill=True,
            fill_color="blue",
            popup=f"Recorded Time: {coord['recorded_time']}<br>Device: {coord['device']}",
        ).add_to(m)

    # Add a PolyLine to connect the points
    if gps_coords:
        folium.PolyLine(
            locations=[[coord["lat"], coord["lon"]] for coord in gps_coords],
            color="blue",
            weight=2.5,
            opacity=1,
        ).add_to(m)

    return m


client = init_connection()


if st.button("นำเข้าข้อมูลเขต"):
    upload_file()


display_areas_data()


col1, col2 = st.columns([0.2, 0.8])

with col1:
    filter_boat = st.selectbox(
        "เลือกเรือ",
        index=list(boat_data.keys()).index(st.session_state.filter_boat),
        options=list(boat_data.keys()),
    )
    st.session_state.filter_boat = filter_boat
with col2:
    filter_date_range = st.date_input(
        "เลือกช่วงเวลา",
        value=(
            st.session_state.filter_date_range
            if "filter_date_range" in st.session_state
            else (datetime.now(), datetime.now())
        ),
        format="DD/MM/YYYY",
        key="date_range_picker",
    )
    if len(filter_date_range) == 2:
        st.session_state.filter_date_range = filter_date_range
        # st.rerun()


if st.button("ดึงข้อมูล") and filter_boat and filter_date_range:
    if len(filter_date_range) != 2:
        st.warning("กรุณาเลือกช่วงเวลาให้ถูกต้อง")
        st.stop()
    st.session_state.gps_coords = get_data(
        filter_date_range=filter_date_range, device=filter_boat
    )

 
    # Plot GPS coordinates on a map


# Plot GPS coordinates on a map

m = plot_gps_coords(st.session_state.gps_coords)
st_folium(m, width=800, height=600)

