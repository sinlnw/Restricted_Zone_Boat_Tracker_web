# streamlit_app.py

import streamlit as st
import pymongo
from datetime import datetime

def is_date_in_day_month_range(
    date: datetime, start_day: int, start_month: int, end_day: int, end_month: int
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
        # day_month_range same year
        return (start_month <= date.month <= end_month) and (
            (date.month == start_month and date.day >= start_day)
            or (date.month == end_month and date.day <= end_day)
            or (start_month < date.month < end_month)
        )