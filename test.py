# streamlit_app.py

import streamlit as st
import pymongo
from datetime import datetime

def is_date_in_day_month_range(
    test_day: int ,test_month: int  , start_day: int, start_month: int, end_day: int, end_month: int
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
        or test_month < 1
        or test_month > 12
        or test_day < 1
        or test_day > 31
    ):
        # invalid date range
        print("invalid date range")
        return False

    if start_month > end_month or (start_month == end_month and start_day > end_day):
        print("cross year")
        # day_month_range cross year
        return is_date_in_day_month_range(
            test_day,test_month, start_day, start_month, 31, 12
        ) or is_date_in_day_month_range(test_day,test_month, 1, 1, end_day, end_month)
    else:
        if (start_month <= test_month <= end_month):
            print("same year")
            if (test_month == start_month and test_day >= start_day):
                print("same start month")
            elif (test_month == end_month and test_day <= end_day):
                print("same end month")
            elif (start_month < test_month < end_month):
                print("between start and end month")
            else:
                print("error or not in range")
        # day_month_range same year
        return (start_month <= test_month <= end_month) and (
            (test_month == start_month and test_day >= start_day)
            or (test_month == end_month and test_day <= end_day)
            or (start_month < test_month < end_month)
        )
