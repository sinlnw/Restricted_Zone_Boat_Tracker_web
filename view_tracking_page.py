import streamlit as st
import json
from datetime import datetime, date
import pymongo
import folium
from streamlit_folium import st_folium
from folium import IFrame
import pandas as pd


boat_data = {"เรือ 1": 1}  # add boat data here

if "date_ranges" not in st.session_state:
    st.session_state.date_ranges = []
if "all_areas" not in st.session_state:
    st.session_state.all_areas = []
if "centers" not in st.session_state:
    st.session_state.centers = []
if "zoom_levels" not in st.session_state:
    st.session_state.zoom_levels = []
if "active_area" not in st.session_state:
    st.session_state.active_area = []  # true if in date range
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
example_date_ranges = [
    {"start_day": 8, "start_month": 9, "end_day": 8, "end_month": 10},
    {"start_day": 8, "start_month": 1, "end_day": 8, "end_month": 1},
]
example_all_areas = [
    [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [100.566874, 13.849414],
                        [100.569062, 13.849497],
                        [100.56932, 13.846622],
                        [100.566058, 13.846372],
                        [100.566874, 13.849414],
                    ]
                ],
            },
        }
    ],
    [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [100.56756, 13.84858],
                        [100.56623, 13.846622],
                        [100.56859, 13.846205],
                        [100.56756, 13.84858],
                    ]
                ],
            },
        },
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [100.571208, 13.847789],
                        [100.569577, 13.845789],
                        [100.572753, 13.845997],
                        [100.571208, 13.847789],
                    ]
                ],
            },
        },
    ],
]
START_LOCATION = [13.847332, 100.572258]
DEFAULT_ZOOM = 15

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
                }
                for item in imported_data
            ]
            st.session_state.all_areas = [
                item["all_drawings"] for item in imported_data
            ]
            st.session_state.active_area = [False] * len(imported_data)
            st.session_state.centers = [
                item.get("center", START_LOCATION) for item in imported_data
            ]
            st.session_state.zoom_levels = [
                item.get("zoom", DEFAULT_ZOOM) for item in imported_data
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
                    "center": [
                        st.session_state.centers[idx][0],
                        st.session_state.centers[idx][1],
                    ],
                    "zoom": st.session_state.zoom_levels[idx],
                    # "start_day": date_ranges[idx]["start_date"].day,
                    # "start_month": date_ranges[idx]["start_date"].month,
                    # "end_day": date_ranges[idx]["end_date"].day,
                    # "end_month": date_ranges[idx]["end_date"].month,
                    "all_drawings": all_areas[idx],
                }
            )

        json_data = json.dumps(paired_data, ensure_ascii=False, indent=4)
        st.text_area("ข้อมูลเขต", json_data, height=300)

    st.text_area("date_range", st.session_state.date_ranges, height=300)
    st.text_area("all_areas", st.session_state.all_areas, height=300)


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

    # projection = {"recorded_time": 1, "device": 1, "lat": 1, "lon": 1, "vbat": 1}
    items = (
        db["coordinate"]
        .find(filter=query_filter)
        .sort("recorded_time", pymongo.ASCENDING)
    )

    items = list(items)  # make hashable for st.cache_data

    # add is_in_area field to each item
    for item in items:
        item["is_in_area"] = False
    return items


def is_point_in_area(test_lat: float, test_lon, area_index: int):
    # check if the point is in the area polygon using ray casting algorithm
    # lat = y   lon = x
    myareas = st.session_state.all_areas[area_index]
    for area in myareas:
        if area["geometry"]["type"] != "Polygon":
            # only support polygon type
            continue
        polygon = area["geometry"]["coordinates"][0]
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]  # previous point, start from first point
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if i == 0:
                continue
            if test_lat > min(p1y, p2y):
                if test_lat <= max(p1y, p2y):
                    if test_lon <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (test_lat - p2y) * (p1x - p2x) / (p1y - p2y) + p2x
                        if p1x == p2x or test_lon < xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

    return inside


def plot_gps_coords(gps_coords):
    # Create a Folium map

    no_active_area = True
    # Find the first active area and use it as the map center and zoom level
    for idx, areas in enumerate(st.session_state.all_areas):
        if st.session_state.active_area[idx]:
            m = folium.Map(
                location=st.session_state.centers[idx],
                zoom_start=st.session_state.zoom_levels[idx],
            )
            no_active_area = False
            break
    if no_active_area:
        m = folium.Map(location=START_LOCATION, zoom_start=DEFAULT_ZOOM)
    polyline_coords = []

    # Add areas polygon to the map
    for idx, areas in enumerate(st.session_state.all_areas):
        if st.session_state.active_area[idx]:
            for area in areas:
                folium.GeoJson(area).add_to(m)

    # Add markers to the map
    for coord in gps_coords:
        is_coord_in_area = False
        # check if the coordinate is in the active area polygon
        for idx, areas in enumerate(st.session_state.all_areas):
            this_area_start_day = st.session_state.date_ranges[idx]["start_day"]
            this_area_start_month = st.session_state.date_ranges[idx]["start_month"]
            this_area_end_day = st.session_state.date_ranges[idx]["end_day"]
            this_area_end_month = st.session_state.date_ranges[idx]["end_month"]
            if is_date_in_day_month_range(
                coord["recorded_time"],
                this_area_start_day,
                this_area_start_month,
                this_area_end_day,
                this_area_end_month,
            ):
                if is_point_in_area(coord["lat"], coord["lon"], idx):
                    # point is in the area
                    is_coord_in_area = True
                    break

        popup_content = f"""
        <div style="width: 200px;">
            <b>Recorded Time:</b> {coord['recorded_time']}<br>
            <b>Lat:</b> {coord['lat']}<br>
            <b>Lon:</b> {coord['lon']}
        </div>
        """
        tooltip_content = f"Recorded Time: {coord['recorded_time']}<br>Lat: {coord['lat']}<br>Lon: {coord['lon']}"
        iframe = IFrame(popup_content, width=210, height=100)
        popup = folium.Popup(iframe, max_width=300)
        if is_coord_in_area:
            color = "red"
            coord["is_in_area"] = True
        else:
            color = "blue"
            coord["is_in_area"] = False
        folium.CircleMarker(
            location=[coord["lat"], coord["lon"]],
            radius=3,  # Size of the dot
            color=color,
            fill=True,
            fill_color=color,
            popup=popup,
            tooltip=tooltip_content,
        ).add_to(m)

        # Add the coordinates to make polyline
        polyline_coords.append([coord["lat"], coord["lon"]])

    # Add a PolyLine to connect the points
    if gps_coords:
        folium.PolyLine(
            locations=polyline_coords,
            color="blue",
            weight=2.5,
            opacity=1,
        ).add_to(m)

    return m


def is_date_in_day_month_range(
    date: date, start_day: int, start_month: int, end_day: int, end_month: int
):

    if (
        start_month < 1
        or start_month > 12
        or end_month < 1
        or end_month > 12
        or start_day < 1
        or start_day > 31
        or end_day < 1
        or end_day > 31
    ):
        # invalid date range
        return False

    if start_month > end_month or (start_month == end_month and start_day > end_day):
        # day_month_range cross year
        return is_date_in_day_month_range(
            date, start_day, start_month, 31, 12
        ) or is_date_in_day_month_range(date, 1, 1, end_day, end_month)
    else:
        date = datetime(date.year, date.month, date.day)
        test_start_date = datetime(date.year, start_month, start_day)
        test_end_date = datetime(date.year, end_month, end_day)
        # day_month_range same year
        return test_start_date <= date <= test_end_date


def display_gps_coords():
    # Display the GPS coordinates in a table
    st.subheader("ข้อมูลตำแหน่ง")
    if st.session_state.gps_coords:
        coords_df = pd.DataFrame(st.session_state.gps_coords)
        coords_df = coords_df.drop("_id", axis=1)
        column_order = ["recorded_time", "lat", "lon", "vbat", "is_in_area"]
        if st.toggle("แสดงทุกคอลัมน์"):
            column_order = None

        # show only rows that is_in_area is True
        if st.toggle("แสดงเฉพาะตำแหน่งที่อยู่ในเขต"):
            coords_df = coords_df[coords_df["is_in_area"]]
        st.dataframe(data=coords_df, column_order=column_order)


# Web display starts here
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
    if not st.session_state.date_ranges or not st.session_state.all_areas:
        st.warning("กรุณานำเข้าข้อมูลเขต")
        st.stop()
    if len(filter_date_range) != 2:
        st.warning("กรุณาเลือกช่วงเวลาให้ถูกต้อง")
        st.stop()

    # might not need the code below if we check when find when checking if point in area
    # but polygon would not show if there is no point in the same date range as area

    i = 0
    # mark area polygons to show on map
    # print("start", filter_date_range[0], "end", filter_date_range[1])
    for date_range in st.session_state.date_ranges:
        # is date range in the selected filter_date_range
        st.session_state.active_area[i] = False
        if is_date_in_day_month_range(
            filter_date_range[0],
            date_range["start_day"],
            date_range["start_month"],
            date_range["end_day"],
            date_range["end_month"],
        ):
            # print(f"start {date_range['start_day']}/{date_range['start_month']} - end {date_range['end_day']}/{date_range['end_month']}")
            # print(f"{filter_date_range[0]} area {i} is in filter date range")
            st.session_state.active_area[i] = True
        if is_date_in_day_month_range(
            filter_date_range[1],
            date_range["start_day"],
            date_range["start_month"],
            date_range["end_day"],
            date_range["end_month"],
        ):
            # print(f"start {date_range['start_day']}/{date_range['start_month']} - end {date_range['end_day']}/{date_range['end_month']}")
            # print(f"{filter_date_range[1]} area {i} is in filter date range")
            st.session_state.active_area[i] = True

        i += 1
    st.session_state.gps_coords = get_data(
        filter_date_range=filter_date_range, device=filter_boat
    )


# Plot GPS coordinates on a map

m = plot_gps_coords(st.session_state.gps_coords)
st_folium(m, width=800, height=600)
display_gps_coords()
