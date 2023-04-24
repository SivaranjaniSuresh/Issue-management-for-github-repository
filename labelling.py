import streamlit as st
import requests
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Set up the model
model_name = "Rami/multi-label-class-classification-on-github-issues"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Set up the GitHub API
base_url = "https://api.github.com"
headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"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"
}

# Get the repository list for a user/org
def get_repos(user):
    url = f"{base_url}/users/{user}/repos"
    response = requests.get(url, headers=headers)
    return json.loads(response.text)

# Get the issues for a repository
def get_issues(repo):
    url = f"{base_url}/repos/{repo}/issues"
    response = requests.get(url, headers=headers)
    return json.loads(response.text)

# Classify an issue using the model
def classify_issue(issue_text):
    inputs = tokenizer(issue_text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.sigmoid(logits)
    return probabilities.numpy().flatten()

# Display the results of the issue classification
def display_results(probabilities):
    labels = ["bug", "enhancement", "question", "documentation", "feature", "maintenance", "performance", "security", "testing", "design", "refactor", "discussion", "dependencies", "deprecation", "release"]

    for i, label in enumerate(labels):
            st.write(f"{label}: {probabilities[i]:.2f}")

# Set up the Streamlit app
st.title("GitHub Issue Tagger")

# Ask for the GitHub username/org
user = st.text_input("Enter a GitHub username or organization name", "")

if user:
    # Get the repositories for the user/org
    repos = get_repos(user)

    # Display a dropdown of the repositories
    repo_names = [repo["name"] for repo in repos]
    repo_index = st.selectbox("Select a repository", repo_names)

    # Get the issues for the selected repository
    issues = get_issues(f"{user}/{repo_index}")

    # Display the issues
    for issue in issues:
        st.write(f"[{issue['title']}]({issue['html_url']})")
        probabilities = classify_issue(issue["body"])
        display_results(probabilities*100)
