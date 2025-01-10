import streamlit as st
import json
from datetime import datetime, date
import pymongo
import folium
from streamlit_folium import st_folium
from folium import IFrame

boat_data = {"เรือ 1": 1}

if "date_ranges" not in st.session_state:
    st.session_state.date_ranges = []
if "all_areas" not in st.session_state:
    st.session_state.all_areas = []
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
                }
                for item in imported_data
            ]
            st.session_state.all_areas = [
                item["all_drawings"] for item in imported_data
            ]
            st.session_state.active_area = [False] * len(imported_data)
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
    projection = {"recorded_time": 1, "device": 1, "lat": 1, "lon": 1, "vbat": 1}
    items = (
        db["coordinate"]
        .find(filter=query_filter, projection=projection)
        .sort("recorded_time", pymongo.ASCENDING)
    )

    items = list(items)  # make hashable for st.cache_data

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
        p1x, p1y = polygon[0] # previous point, start from first point
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
    m = folium.Map(location=START_LOCATION, zoom_start=ZOOM_START)
    polyline_coords = []
    # Add markers to the map
    for coord in gps_coords:

        # check if the coordinate is in the active area polygon

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
        folium.CircleMarker(
            location=[coord["lat"], coord["lon"]],
            radius=3,  # Size of the dot
            color="blue",
            fill=True,
            fill_color="blue",
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

    # Add areas polygon to the map
    for idx, areas in enumerate(st.session_state.all_areas):
        if st.session_state.active_area[idx]:
            for area in areas:
                folium.GeoJson(area).add_to(m)
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

    # might not need the code below if we check when find when checking if point in area
    # but polygon would not show if there is no point in the same date range as area

    i = 0
    # mark area polygons to show on map
    print("start", filter_date_range[0], "end", filter_date_range[1])
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
