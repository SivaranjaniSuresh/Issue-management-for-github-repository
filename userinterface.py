import json
import os
import re

import requests
import streamlit as st
from core_helpers import decode_token
from jose import JWTError, jwt

from utils.database_helpers import DBUtil

SECRET_KEY = "KEY"
ALGORITHM = "ALGORITHM"

SNOWFLAKE_USER = (os.environ.get("SNOWFLAKE_USER"),)
SNOWFLAKE_PASSWORD = (os.environ.get("SNOWFLAKE_PASSWORD"),)
SNOWFLAKE_ACCOUNT = (os.environ.get("SNOWFLAKE_ACCOUNT"),)
SNOWFLAKE_WAREHOUSE = (os.environ.get("SNOWFLAKE_WAREHOUSE"),)
SNOWFLAKE_DATABASE = (os.environ.get("SNOWFLAKE_DATABASE"),)
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")

db = DBUtil(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA,
)


def signup(db, database, schema):
    st.title("Sign Up")
    col1, col2 = st.columns(2)
    # Define regular expressions
    password_regex = "^[a-zA-Z0-9]{8,}$"
    credit_card_regex = "^[0-9]{12}$"

    # Define input fields
    username = col1.text_input("Enter username")
    password = col1.text_input("Enter password", type="password")
    github_repo = col1.text_input("Enter Github Repository")
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

    # Validate Github Repo
    if not github_repo:
        st.error("Username is required.")
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
            "github_repo": github_repo,
            "credit_card": credit_card,
            "service": service,
            "calls_remaining": calls_remaining,
        }

        # Check if the entered username is unique
        cursor = db.conn.cursor()
        query = f"SELECT COUNT(*) FROM users WHERE username = '{username}'"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        cursor.close()

        if count > 0:
            st.error("Username already exists. Please choose a different username.")
        else:
            db.add_record(database, schema, "APP_USERS", user)
            st.success("Successfully signed up!")


# Define the Streamlit app
def main():
    st.set_page_config(page_title="AIssueFlow", page_icon=":satellite:", layout="wide")
    st.sidebar.title("Navigation")

    # Check if user is signed in
    token = st.session_state.get("token", None)
    user_id = decode_token(token)

    # Render the navigation sidebar
    if user_id is not None:
        selection = st.sidebar.radio(["Log Out"])
    else:
        selection = st.sidebar.radio("Go to", ["Sign In", "Sign Up", "Forget Password"])

    # Render the selected page or perform logout
    if selection == "Log Out":
        st.session_state.clear()
        st.sidebar.success("You have successfully logged out!")
        st.experimental_rerun()
    elif selection == "Sign Up":
        signup(db, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA)


if __name__ == "__main__":
    main()
