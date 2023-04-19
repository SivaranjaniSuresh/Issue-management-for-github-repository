import os
import re

import requests
import streamlit as st
from dotenv import load_dotenv

from utils.core_helpers import decode_token

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")

SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")

PREFIX = os.environ.get("PREFIX")


def signup():
    st.title("Sign Up")
    col1, col2 = st.columns(2)
    # Define regular expressions
    password_regex = "^[a-zA-Z0-9]{8,}$"
    credit_card_regex = "^[0-9]{12}$"

    # Define input fields
    username = col1.text_input("Enter username")
    password = col1.text_input("Enter password", type="password")
    service = col2.selectbox(
        "Select a service",
        ["Platinum - (100$)", "Gold - (50$)", "Free - (0$)"],
    )
    credit_card = col2.text_input("Enter Credit Card Details")

    # Initialize flag variable
    has_error = False

    # Validate username
    if not username:
        st.error("Username is required.")
        has_error = True

    # Validate password
    if not re.match(password_regex, password):
        st.error(
            "Password must be at least 8 characters long and can only contain alphanumeric characters."
        )
        has_error = True

    # Validate credit card
    if not re.match(credit_card_regex, credit_card):
        st.error(
            "Credit card number must be 12 digits long and can only contain numeric characters."
        )
        has_error = True

    if not has_error and st.button("Sign up"):
        if service == "Free - (0$)":
            calls_remaining = 10
        elif service == "Gold - (50$)":
            calls_remaining = 15
        elif service == "Platinum - (100$)":
            calls_remaining = 20

        user = {
            "username": username,
            "password": password,
            "credit_card": credit_card,
            "service": service,
            "calls_remaining": calls_remaining,
        }
        response = requests.post(f"{PREFIX}/signup", json=user)

        if response.status_code == 200:
            user = response.json()
            st.success("You have successfully signed up!")
        elif response.status_code == 400:
            st.error(response.json()["detail"])
        else:
            st.error("Something went wrong")


def signin():
    st.title("Sign In")
    username = st.text_input("Enter username")
    password = st.text_input("Enter password", type="password")

    if st.button("Sign in"):
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": "openid profile email",
        }
        response = requests.post(
            f"{PREFIX}/signin",
            data=data,
            auth=("client_id", "client_secret"),
        )
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            st.success("You have successfully signed in!")
            return access_token
        elif response.status_code == 400:
            st.error(response.json()["detail"])
        else:
            st.error("Something went wrong")


# Define the Streamlit app
def main():
    st.set_page_config(page_title="AIssueFlow", page_icon=":satellite:", layout="wide")
    st.sidebar.title("Navigation")

    # Check if user is signed in
    token = st.session_state.get("token", None)
    user_id = decode_token(token, SECRET_KEY, ALGORITHM)

    # Render the navigation sidebar
    if user_id is not None:
        selection = st.sidebar.radio(["Log Out"])
    else:
        selection = st.sidebar.radio("Go to", ["Sign In", "Sign Up"])

    # Render the selected page or perform logout
    if selection == "Log Out":
        st.session_state.clear()
        st.sidebar.success("You have successfully logged out!")
        st.experimental_rerun()
    elif selection == "Sign Up":
        signup()
    elif selection == "Sign In":
        token = signin()
        if token is not None:
            st.session_state.token = token
            st.experimental_rerun()


if __name__ == "__main__":
    main()
