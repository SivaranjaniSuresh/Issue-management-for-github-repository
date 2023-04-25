import os
from urllib.parse import urlparse

import pandas as pd
import requests
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

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
    """
    This function retrieves a list of distinct repository owners and their corresponding repository names from a database table
    named 'GITHUB_ISSUES.PUBLIC.REPO'. It uses a SQL query to fetch the required data, creates a pandas DataFrame from the
    returned data, and returns the resulting DataFrame.

    Returns:
    - df (pandas.DataFrame): A DataFrame with two columns: "REPO_OWNER" and "REPO_NAME", containing the distinct
    repository owner and repository name combinations in the 'GITHUB_ISSUES.PUBLIC.REPO' table.

    """

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
    """
    This function takes a pandas DataFrame as input and generates an HTML table that displays the contents of the DataFrame.

    Args:
        - df (pandas.DataFrame): The DataFrame to be displayed in the HTML table.

    Returns:
        - str: A string of HTML code that represents an HTML table displaying the contents of the input DataFrame.
    """

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
    """
    This function checks if a given GitHub URL is valid and accessible using a valid access token. It sends a GET request
    to the URL using the access token provided in the headers, and returns "Success" if the status code of the response
    is 200 (OK), indicating that the URL is valid and accessible, and "Fail" otherwise.

    Args:
        - url (str): The GitHub URL to be checked.
        - access_token (str): A valid access token to authenticate the request.

    Returns:
        - str: "Success" if the URL is valid and accessible using the access token, and "Fail" otherwise.
    """
    headers = {"Authorization": f"token {access_token}"}
    response = requests.get(url, headers=headers)
    print(response.status_code)
    if response.status_code == 200:
        return "Success"
    else:
        return "Fail"


def get_repo_info(github_link, access_token):
    """
    This function retrieves the owner login and name of a GitHub repository using its URL and a valid access token. It
    sends a GET request to the GitHub API using the URL and access token provided in the headers, and returns a tuple
    containing the owner login and name if the request is successful (status code 200), and None otherwise.

    Args:
        - github_link (str): The URL of the GitHub repository.
        - access_token (str): A valid access token to authenticate the request.

    Returns:
        - tuple or None: A tuple containing the owner login and name of the GitHub repository if the request is
        successful, and None otherwise.
    """
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
    """
    This function inserts a new record into the 'GITHUB_ISSUES.PUBLIC.REPO' table in the database, with the given
    repository owner and name.

    Args:
        - repo_owner (str): The owner of the repository.
        - repo_name (str): The name of the repository.

    Returns:
        - None
    """
    query = (
        "INSERT INTO GITHUB_ISSUES.PUBLIC.REPO (REPO_OWNER, REPO_NAME) VALUES (%s, %s)"
    )
    cursor = conn.cursor()
    cursor.execute(query, (repo_owner, repo_name))
    conn.commit()
    cursor.close()


def repo_exists(repo_owner, repo_name):
    """
    This function checks if a repository with a given owner and name exists in the database. It sends a SELECT query
    to the database using the owner and name as parameters, and returns True if there is at least one row in the result
    set, indicating that the repository exists, and False otherwise.

    Args:
        - repo_owner (str): The owner login of the GitHub repository.
        - repo_name (str): The name of the GitHub repository.

    Returns:
        - bool: True if the repository exists in the database, and False otherwise.
    """
    query = "SELECT COUNT(*) FROM GITHUB_ISSUES.PUBLIC.REPO WHERE REPO_OWNER = %s AND REPO_NAME = %s"
    cursor = conn.cursor()
    cursor.execute(query, (repo_owner, repo_name))
    result = cursor.fetchone()[0]
    cursor.close()
    return result > 0


def adminworkarea(access_token, user_id):
    """
    This function allows an admin user to add a new repository to the table of repositories. The function displays a table of existing repositories and provides an input field for the user to enter a new repository's GitHub link. If the user clicks the "Add repo" button, the function will validate the input link, retrieve the repository information from the GitHub API, and add the repository to the table if it does not already exist.

    Parameters:
        - access_token (str): GitHub access token for making API calls
        - user_id (str): ID of the admin user

    Returns:
        - None
    """
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
        if validity_check == "Success":
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
                st.error(
                    "Unable to extract repository information from the link. Please provide a valid link."
                )
        else:
            st.error("Invalid GitHub repo link. Please provide a valid link.")
