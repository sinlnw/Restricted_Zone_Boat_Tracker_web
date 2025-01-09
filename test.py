# streamlit_app.py

import streamlit as st
import pymongo

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(**st.secrets["mongo"])
st.write("start app")
client = init_connection()
st.write("connected to db")
# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_data():
    db = client["test"]
    items = db["coordinate"].find(projection={ "recorded_time": 1, "device": 1 , "lat": 1, "lon": 1,"vbat": 1})
    items = list(items)  # make hashable for st.cache_data
    return items

items = get_data()
st.write("got data")
# Print results.
i=0
for item in items:

    st.write(f"item: {item}")
    i+=1
    if i>10:
        break