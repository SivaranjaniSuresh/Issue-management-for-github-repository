import os
import pytest
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()

SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")

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
