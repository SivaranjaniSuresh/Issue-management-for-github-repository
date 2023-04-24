import os

import requests
import streamlit as st
from dotenv import load_dotenv

from utils.core_helpers import get_remaining_calls

load_dotenv()

GITHUB_ACCESS_TOKEN = os.environ.get("access_token")

PREFIX = os.environ.get("PREFIX")


def errorsearch(access_token, user_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    remaining_calls = get_remaining_calls(access_token)
    if remaining_calls is not None:
        calls_color = "#228B22" if remaining_calls > 5 else "#D2042D"
        st.markdown(
            f"""
            <style>
                .remaining-calls-container {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 100%;
                    padding: 10px;
                    background-color: #f0f0f0;
                    border-radius: 10px;
                }}
                .remaining-calls-text {{
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #333;
                    margin-right: 10px;
                }}
                .stMetricValue {{
                    color: {calls_color};
                    font-weight: bold;
                }}
            </style>
            <div class="remaining-calls-container">
                <div class="remaining-calls-text">API Calls Remaining:</div>
                <div class="stMetric">
                    <div class="stMetricValue">{remaining_calls}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    user_input = st.text_area("Briefly Describe What Issue you are Facing", height=200)
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
        elif response.status_code == 403:
            similar_issues = "None LOL"
            st.warning(
                "API call limit reached. Please consider upgrading your plan for continued access."
            )
        else:
            st.write(f"Error: {response.status_code}")
            similar_issues = "None LOL"
        if similar_issues != "None LOL" and similar_issues != []:
            similar_issues_html = "<div style='border: 1px solid #008000; padding: 10px; border-radius: 10px;'><h4>SIMILAR ISSUES</h4>"
            for similar_issue in similar_issues:
                title = similar_issue["title"]
                issue_id = similar_issue["id"]
                similarity = similar_issue["similarity"]
                similarity_html = (
                    f"<span style='color: #39FF14;'>{similarity:.2f}%</span>"
                )
                url = similar_issue["url"]
                link_text = f"({url})"
                link_html = f"<a href='{url}'>{link_text}</a>"
                issue_html = (
                    f"<p>- {title} (#{issue_id}) - {similarity_html} - {link_html}</p>"
                )
                similar_issues_html += issue_html
            similar_issues_html += "</div>"
            st.markdown(similar_issues_html, unsafe_allow_html=True)
            st.write("<p></p>", unsafe_allow_html=True)
        else:
            st.error("No similar closed issue found.")
            response = requests.post(
                f"{PREFIX}/get_possible_solution/",
                json={"text": user_input},
                headers=headers,
            )
            if response.status_code == 200:
                possible_solution = response.json()
            elif response.status_code == 403:
                possible_solution = "No Possible Solution"
                st.warning(
                    "API call limit reached. Please consider upgrading your plan for continued access."
                )
            else:
                st.write(f"Error: {response.status_code}")
                possible_solution = "No Possible Solution"
            if possible_solution:
                possible_solution_html = "<div style='border: 1px solid #D2042D; padding: 10px; border-radius: 10px;'><h4>Possible Solution</h4>"
                possible_solution_html += f"<p>{possible_solution}</p>"
                possible_solution_html += "</div>"
                st.markdown(possible_solution_html, unsafe_allow_html=True)
                st.write("<p></p>", unsafe_allow_html=True)


if __name__ == "__main__":
    errorsearch()
