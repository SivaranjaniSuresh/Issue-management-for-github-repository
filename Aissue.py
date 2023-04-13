import streamlit as st
import requests
import os
from dotenv import load_dotenv
import re

load_dotenv()

github_token = os.getenv("GITHUB_API")

st.set_page_config(page_title="GitHub Issue Viewer", page_icon=":octocat:")

st.title("GitHub Issue Viewer 🐙")
st.markdown("Enter your GitHub ID and explore your repositories and their issues!")

github_id = st.text_input("Enter your GitHub ID:")
selected_repo = None
issues = None
selected_issue_number = None


def get_all_pages(url):
    headers = {"Authorization": f"token {github_token}"}
    page = 1
    items = []
    while True:
        response = requests.get(f"{url}?page={page}&per_page=100", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            items.extend(data)
            page += 1
        else:
            break
    return items


def get_repositories(github_id):
    user_url = f"https://api.github.com/users/{github_id}/repos"
    org_url = f"https://api.github.com/orgs/{github_id}/repos"

    user_repos = get_all_pages(user_url)
    org_repos = get_all_pages(org_url)

    repos = user_repos + org_repos

    return [repo["name"] for repo in repos]


if github_id:
    repositories = get_repositories(github_id)

    if repositories:
        selected_repo = st.selectbox("Select a repository:", repositories)
    else:
        st.error("No repositories found for the given GitHub ID. Please try again.")

if selected_repo:
    issue_url = f"https://api.github.com/repos/{github_id}/{selected_repo}/issues"
    issue_data = get_all_pages(issue_url)

    if issue_data:
        issues = [
            {"number": issue["number"], "title": issue["title"]} for issue in issue_data
        ]

if selected_repo:
    if issues:
        st.markdown(f"Issues in the **{selected_repo}** repository:")
        for issue in issues:
            if st.button(f"#{issue['number']} - {issue['title']}"):
                selected_issue_number = issue["number"]
                break
    else:
        st.warning("No issues found in the selected repository.")

if selected_issue_number:
    single_issue_url = f"https://api.github.com/repos/{github_id}/{selected_repo}/issues/{selected_issue_number}"
    single_issue_response = requests.get(
        single_issue_url, headers={"Authorization": f"token {github_token}"}
    )
    single_issue_data = single_issue_response.json()

    if single_issue_response.status_code == 200:
        issue_details = f"""
<div style='border: 1px solid gray; padding: 10px;'>
<h3>Issue #{single_issue_data['number']} - {single_issue_data['title']}</h3>

<p><strong>Status:</strong> {single_issue_data['state']}</p>

<p><strong>Created by:</strong> [<a href='{single_issue_data["user"]["html_url"]}' target='_blank'>{single_issue_data['user']['login']}</a>] </p>

<p><strong>Created at:</strong> {single_issue_data['created_at']}</p>

<p><strong>Updated at:</strong> {single_issue_data['updated_at']}</p>

<p><strong>Labels:</strong></p>
<ul>
"""
        for label in single_issue_data["labels"]:
            issue_details += f"<li>{label['name']}</li>\n"

        issue_details += f"""
</ul>

<p><strong>Description:</strong></p>

{single_issue_data["body"]}
"""

        # Add CSS to resize image and ensure it fits inside the border
        issue_details = issue_details.replace(
            "<img ", '<img style="max-width: 100%; height: auto; margin: 10px 0;" '
        )

        issue_details += "</div>"

        st.markdown(issue_details, unsafe_allow_html=True)
    else:
        st.error("Unable to fetch issue details. Please try again.")
