import os

import requests
import streamlit as st
from jose import JWTError, jwt

PREFIX = os.environ.get("PREFIX")


def decode_token(token, SECRET_KEY, ALGORITHM):
    """
    Decodes a JSON Web Token (JWT) and returns the 'sub' claim as the decoded user ID.

    Parameters:
        token (str): The JWT to decode.
        SECRET_KEY (str): The secret key used to sign the JWT.
        ALGORITHM (str): The algorithm used to sign the JWT.

    Returns:
        str: The decoded user ID from the 'sub' claim of the JWT. Returns None if decoding fails.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        return None


def get_unique_owner_repo_pairs(session):
    """
    Returns a list of unique owner/repo pairs from the 'GITHUB_ISSUES.PUBLIC.ISSUES' table in Snowflake.

    Args:
        session: A database session object.

    Returns:
        A list of tuples, each tuple containing the owner and repo name as strings.
    """
    result = session.execute(
        "SELECT DISTINCT REPO_OWNER, REPO_NAME FROM GITHUB_ISSUES.PUBLIC.ISSUES"
    )
    unique_pairs = result.fetchall()
    return unique_pairs


def get_issue_comments(issue_url, access_token):
    """
    Retrieves the comments for a GitHub issue.

    Args:
        issue_url (str): The URL of the GitHub issue.
        access_token (str): The access token to authenticate with the GitHub API.

    Returns:
        list: A list of comments for the GitHub issue.
    """
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
    """
    Fetches a page of open issues from the specified GitHub repository.

    Args:
        owner (str): The owner of the repository.
        repo (str): The name of the repository.
        access_token (str): The access token to use for authentication.
        page (int): The page number to fetch.
        per_page (int, optional): The number of issues to fetch per page. Defaults to 10.

    Returns:
        dict: A dictionary containing the JSON response from the GitHub API.
    """
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
    """
    Sends a GET request to the API to get the remaining number of calls the user can make to the API.
    Parameters:
        - access_token (str): Access token for authentication.
    Returns:
        - remaining_calls (int): The remaining number of calls the user can make to the API.
          If the request fails, returns None.
    """
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
