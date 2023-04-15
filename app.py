import streamlit as st
import requests
import json
import snowflake.connector
from dotenv import load_dotenv
import os
import datetime


load_dotenv()

SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")
SNOWFLAKE_TABLE = os.environ.get("SNOWFLAKE_TABLE")


access_token = os.environ.get("access_token")

conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        table=SNOWFLAKE_TABLE
    )

def get_all_issues(owner, repo, access_token):
    cursor = conn.cursor()
    result = cursor.execute("SELECT MAX(UPDATED_AT) FROM GITHUB_ISSUES.PUBLIC.ISSUES")
    last_updated_at = result.fetchone()[0]
    # Increment last_updated_at by 1 second
    if last_updated_at is not None:
        last_updated_at = datetime.datetime.fromisoformat(last_updated_at.replace('Z', '+00:00'))
        last_updated_at += datetime.timedelta(seconds=1)
        last_updated_at = last_updated_at.isoformat().replace('+00:00', 'Z')
    
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"}
    issues = []
    page = 1
    per_page = 100

    while True:
        params = {"state": "all", "since":last_updated_at, "per_page": 100, "page": page}
        response = requests.get(url, headers=headers, params=params)
        new_issues = response.json()

        if not new_issues:
            break

        for issue in new_issues:
            issue_number = issue["number"]
            comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
            reactions_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/reactions"
            comments_response = requests.get(comments_url, headers=headers)
            reactions_response = requests.get(reactions_url, headers=headers)

            if comments_response.status_code == 200 and reactions_response.status_code == 200:
                comments_data = comments_response.json()
                reactions_data = reactions_response.json()
                issue["comments"] = comments_data
                issue["reactions"] = reactions_data
                issues.append(issue)
            else:
                print(f"Error fetching comments or reactions for issue {issue_number}")

        page += 1

    return issues

def store_issues_in_snowflake(issues, owner, repo):
    cursor = conn.cursor()

    for issue in issues:
        comments_dict = {}
        for comment in issue['comments']:
            comment_id = comment['id']
            comments_dict[f'comment {comment_id}'] = comment['body']
        
        reactions_dict = []
        for reaction in issue["reactions"]:
            reaction_dict = {
                "id": reaction["id"],
                "user_login": reaction["user"]["login"],
                "user_id": reaction["user"]["id"],
                "content": reaction["content"],
                "created_at": reaction["created_at"]
            }
            reactions_dict.append(reaction_dict)

        body_json = json.dumps({
            'body': issue['body'],
            'comments': comments_dict,
            'reactions': reactions_dict,
        })
        
        assignees = ', '.join([assignee['login'] for assignee in issue['assignees']])
        labels = ', '.join([label['name'] for label in issue['labels']])
        milestone = issue['milestone']['title'] if issue['milestone'] else 'None'

        query = """
            MERGE INTO GITHUB_ISSUES.PUBLIC.ISSUES USING (
                SELECT %(id)s AS id, %(repo_owner)s AS repo_owner, %(repo_name)s AS repo_name,
                %(issue_number)s AS issue_number, %(created_by)s AS created_by, %(title)s AS title,
                %(body)s AS body, %(assignees)s AS assignees, %(labels)s AS labels, %(milestone)s AS milestone,
                %(state)s AS state, %(updated_at)s AS updated_at
            ) S
            ON ISSUES.ID = S.ID
            WHEN MATCHED THEN
                UPDATE SET ISSUES.REPO_OWNER = S.REPO_OWNER, ISSUES.REPO_NAME = S.REPO_NAME,
                ISSUES.ISSUE_NUMBER = S.ISSUE_NUMBER, ISSUES.CREATED_BY = S.CREATED_BY, ISSUES.TITLE = S.TITLE,
                ISSUES.BODY = S.BODY, ISSUES.ASSIGNEES = S.ASSIGNEES, ISSUES.LABELS = S.LABELS, ISSUES.MILESTONE = S.MILESTONE,
                ISSUES.STATE = S.STATE, ISSUES.UPDATED_AT = S.UPDATED_AT
            WHEN NOT MATCHED THEN
                INSERT (ID, REPO_OWNER, REPO_NAME, ISSUE_NUMBER, CREATED_BY, TITLE, BODY, ASSIGNEES, LABELS, MILESTONE, STATE, UPDATED_AT)
                VALUES (S.ID, S.REPO_OWNER, S.REPO_NAME, S.ISSUE_NUMBER, S.CREATED_BY, S.TITLE, S.BODY, S.ASSIGNEES, S.LABELS, S.MILESTONE, S.STATE, S.UPDATED_AT);
        """
        cursor.execute(query, {
            'id': issue['id'],
            'repo_owner': owner,
            'repo_name': repo,
            'issue_number': issue['number'],
            'created_by': issue['user']['login'],
            'title': issue['title'],
            'body': body_json,
            'assignees': assignees,
            'labels': labels,
            'milestone': milestone,
            'state': issue['state'],
            'updated_at': issue['updated_at']
        })
        conn.commit()

    cursor.close()
    conn.close()

def main():
    st.title("GitHub Issues to Snowflake")

    st.write("Enter the GitHub repository information and access token:")

    owner = st.text_input("Repository Owner")
    repo = st.text_input("Repository Name")

    get_issues_button = st.button("Get Issues")
    if get_issues_button:
        with st.spinner("Retrieving issues..."):
            issues = get_all_issues(owner, repo, access_token)
            st.warning(f"Retrieved {len(issues)} issues.")

        with st.spinner("Storing issues in Snowflake..."):
            store_issues_in_snowflake(issues, owner, repo)
            st.success("Issues stored successfully in Snowflake.")

if __name__ == "__main__":
    main()

