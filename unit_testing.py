from unittest.mock import MagicMock
import pytest
import requests_mock
import os
import snowflake.connector

from utils.core_helpers import (
    get_issue_comments,
    get_open_issues,
    get_unique_owner_repo_pairs,
)

SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")

def test_get_open_issues_success():
    owner = "test_owner"
    repo = "test_repo"
    access_token = "fake_token"
    page = 1
    per_page = 2

    issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    issues_response = [
        {
            "id": 1,
            "title": "Test issue 1",
            "comments_url": f"{issues_url}/1/comments",
            "comments_data": [],
        },
        {
            "id": 2,
            "title": "Test issue 2",
            "comments_url": f"{issues_url}/2/comments",
            "comments_data": [],
        },
    ]

    with requests_mock.Mocker() as m:
        m.get(issues_url, json=issues_response)
        for issue in issues_response:
            m.get(issue["comments_url"], json=issue["comments_data"])

        result = get_open_issues(owner, repo, access_token, page, per_page)
        assert result == issues_response


def test_get_open_issues_failure():
    owner = "test_owner"
    repo = "test_repo"
    access_token = "fake_token"
    page = 1
    per_page = 2

    issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    with requests_mock.Mocker() as m:
        m.get(issues_url, status_code=404)

        result = get_open_issues(owner, repo, access_token, page, per_page)
        assert result == []


def test_get_open_issues_invalid_token():
    owner = "test_owner"
    repo = "test_repo"
    access_token = "invalid_token"
    page = 1
    per_page = 2

    issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    with requests_mock.Mocker() as m:
        m.get(issues_url, status_code=401)

        result = get_open_issues(owner, repo, access_token, page, per_page)
        assert result == []

def test_get_unique_owner_repo_pairs_success():
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_session.execute.return_value = mock_result
    mock_result.fetchall.return_value = [
        ("owner1", "repo1"),
        ("owner2", "repo2"),
        ("owner3", "repo3"),
    ]

    result = get_unique_owner_repo_pairs(mock_session)

    mock_session.execute.assert_called_once_with(
        "SELECT DISTINCT REPO_OWNER, REPO_NAME FROM GITHUB_ISSUES.PUBLIC.ISSUES"
    )
    mock_result.fetchall.assert_called_once()
    assert result == [
        ("owner1", "repo1"),
        ("owner2", "repo2"),
        ("owner3", "repo3"),
    ]

def test_get_unique_owner_repo_pairs_empty_result():
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_session.execute.return_value = mock_result
    mock_result.fetchall.return_value = []

    result = get_unique_owner_repo_pairs(mock_session)

    mock_session.execute.assert_called_once_with(
        "SELECT DISTINCT REPO_OWNER, REPO_NAME FROM GITHUB_ISSUES.PUBLIC.ISSUES"
    )
    mock_result.fetchall.assert_called_once()
    assert result == []


def test_get_issue_comments_success():
    issue_url = "https://api.github.com/repos/test_owner/test_repo/issues/1/comments"
    access_token = "fake_token"
    comments_response = [
        {"id": 1, "body": "Test comment 1"},
        {"id": 2, "body": "Test comment 2"},
    ]

    with requests_mock.Mocker() as m:
        m.get(issue_url, json=comments_response)

        result = get_issue_comments(issue_url, access_token)
        assert result == comments_response


def test_get_issue_comments_failure():
    issue_url = "https://api.github.com/repos/test_owner/test_repo/issues/1/comments"
    access_token = "fake_token"

    with requests_mock.Mocker() as m:
        m.get(issue_url, status_code=404)

        result = get_issue_comments(issue_url, access_token)
        assert result == []


def test_get_issue_comments_invalid_token():
    issue_url = "https://api.github.com/repos/test_owner/test_repo/issues/1/comments"
    access_token = "invalid_token"

    with requests_mock.Mocker() as m:
        m.get(issue_url, status_code=401)

        result = get_issue_comments(issue_url, access_token)
        assert result == []

def get_issue_url(issue_number, repo_owner=None, repo_name=None):
    conn = snowflake.connector.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA,
    )
    cursor = conn.cursor()
    query = f"SELECT ISSUE_URL, TITLE FROM GITHUB_ISSUES.PUBLIC.ISSUES WHERE ID = '{issue_number}'"
    result = cursor.execute(query)
    row = result.fetchone()
    cursor.close()
    conn.close()
    return (row[0], row[1]) if row else (None, None)

# Test data setup
test_data = [
    {
        "issue_number": 1647155662,
        "repo_owner": "openai",
        "repo_name": "openai-python",
        "issue_url": "https://github.com/openai/openai-python/issues/358",
        "title": "request_id is not work",
    },
    {
        "issue_number": 1669196666,
        "repo_owner": "twitter",
        "repo_name": "the-algorithm",
        "issue_url": "https://github.com/twitter/the-algorithm/issues/1784",
        "title": 'Sound of video from "For You" tab plays after switching to "Following" tab in Twitter Android app',
    },
    {
    "issue_number": 1665279685,
    "repo_owner": "facebook",
    "repo_name": "Rapid",
    "issue_url": "https://github.com/facebook/Rapid/issues/914",
    "title": "Selecting multiple alike elements, suddenly dissapear",
    },
]

# Define the test function
@pytest.mark.parametrize(
    "test_data_item",
    test_data,
    ids=[
        "Test with OpenAI issue",
        "Test with Twitter issue",
        "Test with Facebook issue",
    ],
)
def test_get_issue_url(test_data_item):
    issue_url, title = get_issue_url(test_data_item["issue_number"])
    assert issue_url == test_data_item["issue_url"]
    assert title == test_data_item["title"]

# Test with non-existent issue number
def test_get_issue_url_non_existent():
    issue_url, title = get_issue_url(9999)
    assert issue_url is None
    assert title is None


if __name__ == "__main__":
    pytest.main()
