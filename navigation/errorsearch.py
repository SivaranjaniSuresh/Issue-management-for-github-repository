import os

import openai
import requests
import streamlit as st
from dotenv import load_dotenv

from utils.core_helpers import (
    get_embeddings,
    get_open_issues,
    get_possible_solution,
    get_summary,
    get_unique_owner_repo_pairs,
)

load_dotenv()

GITHUB_ACCESS_TOKEN = os.environ.get("access_token")
openai.api_key = os.environ.get("OPENAI_API_KEY")
PREFIX = os.environ.get("PREFIX")


def errorsearch(access_token, user_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    user_input = st.text_area("Describe What Issue you are Facing", height=200)
    if st.button("Search for similar Issue on Github"):
        embeddings = get_embeddings(user_input)
        response = requests.get(
            f"{PREFIX}/github_search",
            params={
                "embedded_issue_text_dict": str(embeddings),
            },
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
