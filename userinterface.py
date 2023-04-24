import os
import re

import requests
import streamlit as st
from dotenv import load_dotenv

from navigation.adminworkarea import adminworkarea
from navigation.analytics import analytics
from navigation.errorsearch import errorsearch
from navigation.issuesearch import issuesearch
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


def remaining_api_calls(headers):
    """
    Sends a GET request to the server to retrieve the remaining number of API calls that can be made with the current API token.

    Parameters:
    headers (dict): A dictionary containing the headers to be sent with the request, including the API token.

    Returns:
    int: The remaining number of API calls as reported by the server.
    """
    response = requests.get(f"{PREFIX}/remaining_api_calls", headers=headers).json()
    remaining_calls = response["remaining_calls"]
    return remaining_calls


def signup():
    """Presents a user interface to sign up for a service, validates user input, and sends the signup data to the server API.

    Returns:
        None
    """
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


def forget_password():
    """
    Displays a Sign In form and sends the user credentials to the authentication API to obtain an access token.

    Returns:
        str: The access token obtained from the authentication API, or None if the user authentication fails.
    """
    st.write("Update Password Here")
    password_regex = "^[a-zA-Z0-9]{8,}$"
    username = st.text_input("Enter username")
    password = st.text_input(
        "Enter new password", type="password"
    )  # Validate credit card
    if not re.match(password_regex, password):
        st.error(
            "Password must be at least 8 characters long and can only contain alphanumeric characters."
        )
    if st.button("Update Password"):
        url = f"{PREFIX}/forget-password?username={username}&password={password}"
        response = requests.put(url)
        if response.status_code == 200:
            st.write("Password Updated Successfully")
        elif response.status_code == 404:
            st.error("User not found.")
        else:
            st.error("Error updating password.")


def upgrade_subscription(token):
    """
    Updates a user's subscription by sending a PUT request to the server.

    Parameters:
    token : str
        A string representing the user's authentication token.

    Returns:
    None
    """
    headers = {"Authorization": f"Bearer {token}"}
    calls_remaining = remaining_api_calls(headers)
    service = st.selectbox(
        "Select a service",
        ["Platinum - (100$)", "Gold - (50$)", "Free - (0$)"],
    )
    if service == "Free - (0$)":
        calls_remaining += 10
    elif service == "Gold - (50$)":
        calls_remaining += 15
    elif service == "Platinum - (100$)":
        calls_remaining += 20

    if st.button("Upgrade Subscription"):
        url = f"{PREFIX}/update_subscription?service={service}&calls_remaining={calls_remaining}"
        response = requests.put(url, headers=headers)
        if response.status_code == 200:
            st.success("Subscription Updated Successfully")
        elif response.status_code == 404:
            st.error("User not found.")
        else:
            st.error("Error updating Subscription.")


# Define the Streamlit pages
pages = {
    "Git-Magnet": issuesearch,
    "Git-Cognizant": errorsearch,
    "Analytics": analytics,
    "Admin Workarea": adminworkarea,
}


# Define the Streamlit app
def main():
    st.set_page_config(page_title="AIssueFlow", page_icon=":satellite:", layout="wide")
    st.sidebar.title("Navigation")

    # Check if user is signed in
    token = st.session_state.get("token", None)
    user_id = decode_token(token, SECRET_KEY, ALGORITHM)

    # Render the navigation sidebar
    if user_id is not None and user_id != "damg7245":
        filtered_pages = [page for page in pages.keys() if page != "Admin Workarea"]
        selection = st.sidebar.radio(
            "Go to", filtered_pages + ["Upgrade Subscription", "Log Out"]
        )
    elif user_id == "damg7245":
        selection = st.sidebar.radio(
            "Go to", ["Admin Workarea", "Analytics", "Log Out"]
        )
    else:
        selection = st.sidebar.radio("Go to", ["Sign In", "Sign Up", "Forget Password"])

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
    elif selection == "Forget Password":
        forget_password()
    elif selection == "Upgrade Subscription":
        upgrade_subscription(token)
    else:
        page = pages[selection]
        page(token, user_id)


if __name__ == "__main__":
    main()
