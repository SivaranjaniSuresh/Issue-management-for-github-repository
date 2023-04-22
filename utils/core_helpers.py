import openai
import requests
from jose import JWTError, jwt


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


def get_summary(text):
    prompt = f"Please analyze the following GitHub issue body and provide a brief and concise summary of the problem. Please note that we are only looking for a summary and not a solution or any additional information. Thank you. ONLY SUMMARY.\n\nIssue Body: {text}\n\n"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.6,
    )
    return response.choices[0].message["content"].strip()


def get_possible_solution(text):
    prompt = f"What is a possible solution to the following GitHub issue? Please provide a detailed solution, or if there are no questions to answer in the issue, suggest some potential solutions or explain why a solution may not be feasible. If you are unsure, please provide any insights or suggestions that may be helpful in resolving the issue. Thank you for your contribution!.\n\n Github Issue:{text}\n\n"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.6,
    )
    return response.choices[0].message["content"].strip()
