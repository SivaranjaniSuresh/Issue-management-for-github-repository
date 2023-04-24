import os

import requests
import streamlit as st
from jose import JWTError, jwt

PREFIX = os.environ.get("PREFIX")


def decode_token(token, SECRET_KEY, ALGORITHM):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        return None


def get_unique_owner_repo_pairs(session):
    result = session.execute(
        "SELECT DISTINCT REPO_OWNER, REPO_NAME FROM GITHUB_ISSUES.PUBLIC.ISSUES"
    )
    unique_pairs = result.fetchall()
    return unique_pairs


def get_issue_comments(issue_url, access_token):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {access_token}",
    }
    response = requests.get(issue_url, headers=headers)
    if response.status_code == 200:
        comments = response.json()
        return comments
    else:
        print(f"Error {response.status_code}: Failed to fetch comments")
        return []


def get_open_issues(owner, repo, access_token, page, per_page=10):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {"state": "open", "page": page, "per_page": per_page}
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {access_token}",
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        issues = response.json()
        # Fetch comments for each issue
        for issue in issues:
            issue["comments_data"] = get_issue_comments(
                issue["comments_url"], access_token
            )
        return issues
    else:
        print(f"Error {response.status_code}: Failed to fetch issues")
        return []


def get_remaining_calls(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{PREFIX}/remaining_api_calls/",
        headers=headers,
    )

    if response.status_code == 200:
        remaining_calls = response.json()["remaining_calls"]
        return remaining_calls
    else:
        st.write(f"Error: {response.status_code}")
        return None
