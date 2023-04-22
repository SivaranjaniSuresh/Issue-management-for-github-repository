import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

GITHUB_ACCESS_TOKEN = os.environ.get("access_token")

PREFIX = os.environ.get("PREFIX")


def errorsearch(access_token, user_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    user_input = st.text_area("Describe What Issue you are Facing", height=200)
    if st.button("Search for similar Issue on Github"):
        json_data = {
            "user_input": user_input,
        }
        response = requests.post(
            f"{PREFIX}/get_github_solutions/",
            json=json_data,
            headers=headers,
        )
        if response.status_code == 200:
            similar_issues = response.json()
            st.write(similar_issues)
        else:
            st.write(f"Error: {response.status_code}")
            similar_issues = "None LOL"


if __name__ == "__main__":
    errorsearch()
