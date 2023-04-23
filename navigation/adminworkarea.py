import os
import requests
import streamlit as st
from dotenv import load_dotenv
import snowflake.connector
from urllib.parse import urlparse
import pandas as pd

load_dotenv()

SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")
git_access_token = os.environ.get("access_token")

conn = snowflake.connector.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA,
)

def get_repo_table():
    query = "SELECT DISTINCT(REPO_OWNER), REPO_NAME FROM GITHUB_ISSUES.PUBLIC.REPO"
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(data, columns=["REPO_OWNER", "REPO_NAME"])
    return df


def center_table_style():
    return """
        <style>
            table {
                margin-left: auto;
                margin-right: auto;
                border-collapse: separate;
                border-spacing: 0;
                width: 60%;
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid #D2042D;
            }
            th {
                background-color: transparent;
                color: #D2042D;
                text-align: center;
                padding: 8px;
                border-bottom: 1px solid #D2042D;
            }
            td {
                background-color: transparent;
                text-align: center;
                padding: 8px;
                border-bottom: 1px solid #D2042D;
            }
            tr:nth-child(even) {
                background-color: transparent;
            }
            tr:nth-child(odd) {
                background-color: transparent;
            }
            tr:hover {
                background-color: rgba(255, 99, 71, 0.15);
            }
        </style>
    """

def generate_html_table(df):
    table_start = "<table>"
    table_end = "</table>"
    table_header = "<tr>" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"
    table_body = "".join(
        [
            "<tr>" + "".join([f"<td>{value}</td>" for value in row]) + "</tr>"
            for _, row in df.iterrows()
        ]
    )
    return table_start + table_header + table_body + table_end

def is_valid_github_link(url, access_token):
    headers = {"Authorization": f"token {access_token}"}
    response = requests.get(url, headers=headers)
    print(response.status_code)
    if response.status_code == 200:
        return 'Success'
    else:
        return 'Fail'

def get_repo_info(github_link, access_token):
    api_url = "https://api.github.com/repos/"
    repo_path = github_link.replace("https://github.com/", "")
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json",
    }
    
    full_path = api_url + repo_path
    response = requests.get(full_path, headers=headers)
    print(response.status_code)
    if response.status_code == 200:
        repo_info = response.json()
        print(repo_info)
        return repo_info["owner"]["login"], repo_info["name"]
    else:
        return None

def insert_repo(repo_owner, repo_name):
    query = "INSERT INTO GITHUB_ISSUES.PUBLIC.REPO (REPO_OWNER, REPO_NAME) VALUES (%s, %s)"
    cursor = conn.cursor()
    cursor.execute(query, (repo_owner, repo_name))
    conn.commit()
    cursor.close()

def repo_exists(repo_owner, repo_name):
    query = "SELECT COUNT(*) FROM GITHUB_ISSUES.PUBLIC.REPO WHERE REPO_OWNER = %s AND REPO_NAME = %s"
    cursor = conn.cursor()
    cursor.execute(query, (repo_owner, repo_name))
    result = cursor.fetchone()[0]
    cursor.close()
    return result > 0

def adminworkarea(access_token, user_id):
    st.title("Knowledge Base")
    
    # Add the center table style
    st.markdown(center_table_style(), unsafe_allow_html=True)
    
    # Get the dataframe
    repo_df = get_repo_table()
    
    # Display the table without the index column
    st.markdown(generate_html_table(repo_df), unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Input field for the GitHub repo link
    github_link = st.text_input("Enter the GitHub repo link:")

    # Button to add the repo to the table
    if st.button("Add repo"):
        validity_check = is_valid_github_link(github_link, git_access_token)
        print(validity_check)
        if validity_check=='Success':
            repo_info = get_repo_info(github_link, git_access_token)
            if repo_info:
                repo_owner, repo_name = repo_info
                if not repo_exists(repo_owner, repo_name):
                    insert_repo(repo_owner, repo_name)
                    st.success("Repository added to the table.")
                    st.experimental_rerun()
                else:
                    st.error("Repository already exists in the table.")
            else:
                st.error("Unable to extract repository information from the link. Please provide a valid link.")
        else:
            st.error("Invalid GitHub repo link. Please provide a valid link.")

