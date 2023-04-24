import os

import altair as alt
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

PREFIX = os.environ.get("PREFIX")


def analytics(access_token, user_id):
    """
    Generates analytics based on user activity data retrieved from an API using the provided access token and user ID.

    Parameters:
    access_token (str): The access token used to authenticate with the API.
    user_id (str): The user ID associated with the user whose activity data is being retrieved.

    Returns:
    None: The function generates visualizations of the user activity data using the Streamlit library.

    Raises:
    HTTPError: An error occurred while retrieving data from the API.

    """
    url = PREFIX + "/user_activity"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    json_data = response.json()
    if len(json_data) != 0:
        data = pd.DataFrame.from_records(json_data)
        # convert timestamps to datetime objects
        data["timestamp"] = pd.to_datetime(data["timestamp"])

        # define date range for filtering
        today = pd.Timestamp.today().normalize()
        yesterday = today - pd.Timedelta(days=1)
        day_before_yesterday = today - pd.Timedelta(days=2)
        last_week = today - pd.Timedelta(weeks=1)

        # filter data by date range
        data_today = data[data["timestamp"].dt.date == today]
        data_yesterday = data[data["timestamp"].dt.date == yesterday]
        data_last_week = data[
            (data["timestamp"].dt.date > last_week)
            & (data["timestamp"].dt.date <= today)
        ]

        # count number of requests by user and date
        count_by_user_and_date = (
            data.groupby([data["username"], data["timestamp"].dt.date])
            .size()
            .reset_index(name="count")
        )

        # plot line chart of count by user and date
        chart = (
            alt.Chart(count_by_user_and_date)
            .mark_line()
            .encode(
                x=alt.X(
                    "timestamp:T",
                    axis=alt.Axis(title="Date"),
                    timeUnit="utcyearmonthdatehoursminutes",
                ),
                y=alt.Y("count:Q", axis=alt.Axis(title="Number of requests")),
                color="username:N",
            )
            .properties(
                width=800, height=400, title="Count of requests by user and date"
            )
        )

        # filter data by date range
        data_day_before_yesterday = data[
            data["timestamp"].dt.date == day_before_yesterday
        ]
        # calculate total API calls the previous day
        total_calls_yesterday = len(data_yesterday)
        total_calls_day_before_yesterday = len(data_day_before_yesterday)
        delta_calls_yesterday = total_calls_yesterday - total_calls_day_before_yesterday

        # calculate total API calls the previous day
        total_calls_today = len(data_today)
        delta_calls_today = total_calls_today - total_calls_yesterday

        # calculate total average calls during the last week
        total_calls_last_week = len(data_last_week)
        average_calls_last_week = total_calls_last_week / 7
        total_average_calls_last_two_weeks = round(average_calls_last_week * 2, 1)

        # replace response_code values with Success or Failure
        data["response_code"] = data["response_code"].replace(
            {200: "Success", 204: "No Data Returned", 404: "Failure"}
        )
        # create bar chart of success and failed request counts
        bar_chart_sucess_or_failure = (
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("response_code:N", axis=alt.Axis(title="Response code")),
                y=alt.Y("count()", axis=alt.Axis(title="Count")),
                color=alt.Color(
                    "response_code:N",
                    scale=alt.Scale(
                        domain=["Success", "No Data Returned", "Failure"],
                        range=["green", "yellow", "red"],
                    ),
                    legend=None,
                ),
            )
            .properties(
                width=600, height=400, title="Success and failed request counts"
            )
            .transform_filter(
                alt.FieldOneOfPredicate(
                    field="response_code",
                    oneOf=["Success", "No Data Returned", "Failure"],
                )
            )
        )

        # create bar chart of success and failed request counts
        bar_chart_per_endpoint = (
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("count()", axis=alt.Axis(title="Count")),
                y=alt.Y("api_endpoint:N", axis=alt.Axis(title="Endpoint")),
                color=alt.condition(
                    alt.datum.response_code == "200",
                    alt.value("green"),
                    alt.value("blue"),
                ),
            )
            .properties(
                width=800, height=400, title="Total number of calls per endpoint"
            )
        )

        # display results
        st.title("API Metrics")
        col1, col2, col3 = st.columns(3)

        col1.metric(
            label="API calls Today",
            value=total_calls_today,
            delta=delta_calls_today,
        )

        col2.metric(
            label="API calls Yesterday",
            value=total_calls_yesterday,
            delta=delta_calls_yesterday,
        )

        col3.metric(
            label="Average Calls Last Week",
            value=round(average_calls_last_week, 2),
            delta=round(
                total_average_calls_last_two_weeks - average_calls_last_week, 2
            ),
        )

        st.subheader("Count of requests by user and date")
        st.altair_chart(chart)

        st.subheader("Success and failed request counts")
        st.altair_chart(bar_chart_sucess_or_failure)

        st.subheader("Total number of calls per endpoint")
        st.altair_chart(bar_chart_per_endpoint)
    else:
        st.header("No Analytics to Show")
