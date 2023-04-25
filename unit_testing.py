from unittest.mock import MagicMock

import pytest
import requests_mock

from utils.core_helpers import (
    get_issue_comments,
    get_open_issues,
    get_unique_owner_repo_pairs,
)


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


if __name__ == "__main__":
    pytest.main()
