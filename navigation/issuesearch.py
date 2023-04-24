import os
import re

import requests
import streamlit as st
from dotenv import load_dotenv
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from backend.database import SessionLocal
from utils.core_helpers import (
    get_open_issues,
    get_remaining_calls,
    get_unique_owner_repo_pairs,
)

load_dotenv()

GITHUB_ACCESS_TOKEN = os.environ.get("access_token")
PREFIX = os.environ.get("PREFIX")

session = SessionLocal()

# Set up the model
model_name = "Rami/multi-label-class-classification-on-github-issues"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def replace_image_tags_with_images(text):
    img_tags = re.findall(r'<img[^>]+>', text)

    for img_tag in img_tags:
        src = re.search(r'src="([^"]+)"', img_tag)
        if src:
            image_url = src.group(1)
            img_markdown = f'<img src="{image_url}" style="width:auto;height:auto;max-width:100%;" />'
            text = text.replace(img_tag, img_markdown)

    return text

# Classify an issue using the model
def classify_issue(issue_text):
    if not issue_text:
        return None
    inputs = tokenizer(issue_text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.sigmoid(logits)
    return probabilities.numpy().flatten()

def display_results(probabilities):
    if probabilities is None:
        return []
    label_list = [
    "accessibility", "android", "api", "app", "architecture", "assets", "authentication",
    "automated-tests", "backend", "blog", "bootstrap", "bug", "chat", "chrome-extension",
    "ci", "clean-code", "code-coverage", "community", "compliance", "console", "css", "data",
    "database", "dependencies", "design", "devops", "documentation", "docker", "e2e-testing",
    "easy-pick", "editor", "enhancement", "error-handling", "feature", "frontend", "git",
    "github-actions", "graphql", "hacktoberfest", "help-wanted", "html", "http", "i18n",
    "infrastructure", "installation", "integration-tests", "ios", "javascript", "jest",
    "jquery", "json", "linting", "logging", "macos", "machine-learning", "maintenance",
    "markdown", "mobile", "monitoring", "new-feature", "node.js", "optimization", "package",
    "performance", "php", "plugin", "pwa", "python", "question", "rails", "react", "reproducible-builds",
    "rest-api", "ruby", "scala", "search", "security", "serverless", "setup", "storybook",
    "testing", "translation", "typescript", "ui", "usability", "user-experience", "visualization",
    "vue.js", "windows", "workflow", "yaml"
    ]
    label_probs = list(zip(label_list, probabilities))
    label_probs.sort(key=lambda x: x[1], reverse=True)
    top_3_labels = label_probs[:3]
    return top_3_labels

def issuesearch(access_token, user_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    remaining_calls = get_remaining_calls(access_token)
    if remaining_calls is not None:
        calls_color = "#228B22" if remaining_calls > 5 else "#D2042D"

        st.write(
            """
            <style>
                .remaining-calls-container {
                    margin-bottom: 20px;
                }
                .remaining-calls-text {
                    font-size: 1.1em;
                    font-weight: bold;
                    color: #FFFFFF;
                    margin-right: 10px;
                }
                .stMetricValue {
                    color: """
            + calls_color
            + """;
                    font-weight: bold;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )

        remaining_calls_container = st.empty()
        remaining_calls_container.markdown(
            f"""
            <div class="remaining-calls-container">
                <div class="remaining-calls-text">API Calls Remaining:</div>
                <div class="stMetric">
                    <div class="stMetricValue">{remaining_calls}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.title("GitHub Issues Similarity Check")
    col1, col2 = st.columns(2)
    unique_pairs = get_unique_owner_repo_pairs(session)
    owner_repo_dict = {}
    for owner, repo in unique_pairs:
        if owner not in owner_repo_dict:
            owner_repo_dict[owner] = []
        owner_repo_dict[owner].append(repo)

    selected_owner = col1.selectbox("Select an owner", list(owner_repo_dict.keys()))

    if selected_owner:
        selected_repo = col2.selectbox(
            "Select a repository", owner_repo_dict[selected_owner]
        )

    page = st.number_input("Page", min_value=1, value=1, step=1)

    issues = get_open_issues(selected_owner, selected_repo, GITHUB_ACCESS_TOKEN, page)
    if issues:
        st.write(f"**Open Issues for {selected_owner}/{selected_repo} (Page {page}):**")
        # Initialize a dictionary to store labeled issues
        labeled_issues = {}
        for issue in issues:
            issue_id = issue["id"]
            issue_title = issue["title"]
            issue_body = issue["body"]
            issue_comments = issue["comments_data"]
            with st.expander(issue_title):
                # Check if the issue has already been labeled
                if issue_id not in labeled_issues:
                    probabilities = classify_issue(issue["body"])
                    if probabilities is not None:
                        top_3_labels = display_results(probabilities * 100)
                        labeled_issues[issue_id] = top_3_labels
                    else:
                        labeled_issues[issue_id] = None
                # Fetch the labels from the labeled_issues dictionary
                top_3_labels = labeled_issues[issue_id]
                
                if top_3_labels is not None:
                    label_text = " ".join([f"<code style='background-color: #191D20; color: #228B22; padding: 6px 12px;'>{label}</code>" for label, _ in top_3_labels])
                else:
                    label_text = ""
                st.markdown(f"Possible Labels: {label_text}", unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                if issue_body is not None:
                    issue_body_with_images = replace_image_tags_with_images(issue_body)
                else:
                    issue_body_with_images = ""
                st.markdown(f"<div style='overflow: auto;'>{issue_body_with_images}</div>", unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.write("Comments:")
                if issue_comments:
                    for comment in issue_comments:
                        st.markdown(f"<span style='color: #800080'>{comment['user']['login']}:</span>", unsafe_allow_html=True)
                        st.write(comment["body"])
                else:
                    st.write("No Comments.")
                st.markdown("<hr>", unsafe_allow_html=True)
                summary_key = f"summary_{issue['number']}"
                if st.session_state.get(summary_key):
                    st.markdown(
                        "<div style='border: 1px dotted #FFC000; padding: 10px; border-radius: 10px;'><h4>Summary</h4>"
                        + st.session_state[summary_key]
                        + "</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(
                        "Reveal the Essence.", key=f"summary_button_{issue['number']}"
                    ):
                        with st.spinner("Generating summary..."):
                            response = requests.post(
                                f"{PREFIX}/get_issue_summary/",
                                json={"text": issue_body, "comments": issue_comments},
                                headers=headers,
                            )
                            if response.status_code == 200:
                                summary = response.json()
                            elif response.status_code == 403:
                                summary = "API call limit reached. Please consider upgrading your plan for continued access."
                                st.warning(summary)
                            else:
                                st.write(f"Error: {response.status_code}")
                                summary = "No Summary Extracted"
                            st.session_state[summary_key] = summary
                            st.markdown(
                                f"<div style='border: 1px dotted #FFC000; padding: 10px; border-radius: 10px;'><h4>Summary</h4>{summary}</div>",
                                unsafe_allow_html=True,
                            )
                            st.experimental_rerun()

                st.write("<p></p>", unsafe_allow_html=True)

                similar_key = f"similar_{issue['number']}"
                if st.session_state.get(similar_key):
                    if isinstance(st.session_state[similar_key], list):
                        similar_issues = st.session_state[similar_key]
                        similar_issues_html = "<div style='border: 1px solid #008000; padding: 10px; border-radius: 10px;'><h4>Similar Issues</h4>"
                        for similar_issue in similar_issues:
                            title = similar_issue["title"]
                            issue_id = similar_issue["id"]
                            similarity = similar_issue["similarity"]
                            similarity_html = f"<span style='color: #39FF14;'>{similarity:.2f}%</span>"
                            url = similar_issue["url"]
                            link_text = f"({url})"
                            link_html = f"<a href='{url}'>{link_text}</a>"
                            issue_html = f"<p>- {title} (#{issue_id}) - {similarity_html} - {link_html}</p>"
                            similar_issues_html += issue_html
                        similar_issues_html += "</div>"
                        st.markdown(similar_issues_html, unsafe_allow_html=True)
                        st.write("<p></p>", unsafe_allow_html=True)
                    else:
                        st.error("No similar closed issue found.")
                        possible_solution = st.session_state[similar_key]
                        if possible_solution:
                            possible_solution_html = "<div style='border: 1px solid #D2042D; padding: 10px; border-radius: 10px;'><h4>Possible Solution</h4>"
                            possible_solution_html += f"<p>{possible_solution}</p>"
                            possible_solution_html += "</div>"
                            st.markdown(possible_solution_html, unsafe_allow_html=True)
                            st.write("<p></p>", unsafe_allow_html=True)
                else:
                    if st.button(f"Find similar issues for {issue_title}"):
                        json_data = {
                            "issue_body": issue_body,
                            "selected_owner": selected_owner,
                            "selected_repo": selected_repo,
                        }
                        response = requests.post(
                            f"{PREFIX}/get_similar_issues/",
                            json=json_data,
                            headers=headers,
                        )
                        if response.status_code == 200:
                            similar_issues = response.json()
                        elif response.status_code == 403:
                            similar_issues = "None LOL"
                            st.warning(
                                "API call limit reached. Please consider upgrading your plan for continued access."
                            )
                        else:
                            st.write(f"Error: {response.status_code}")
                            similar_issues = "None LOL"
                        if similar_issues != "None LOL" and similar_issues != []:
                            st.session_state[similar_key] = similar_issues
                            similar_issues_html = "<div style='border: 1px solid #008000; padding: 10px; border-radius: 10px;'><h4>Similar Issues</h4>"
                            for similar_issue in similar_issues:
                                title = similar_issue["title"]
                                issue_id = similar_issue["id"]
                                similarity = similar_issue["similarity"]
                                similarity_html = f"<span style='color: #39FF14;'>{similarity:.2f}%</span>"
                                url = similar_issue["url"]
                                link_text = f"({url})"
                                link_html = f"<a href='{url}'>{link_text}</a>"
                                issue_html = f"<p>- {title} (#{issue_id}) - {similarity_html} - {link_html}</p>"
                                similar_issues_html += issue_html
                            similar_issues_html += "</div>"
                            st.markdown(similar_issues_html, unsafe_allow_html=True)
                            st.write("<p></p>", unsafe_allow_html=True)
                            st.experimental_rerun()
                        else:
                            st.error("No similar closed issue found.")
                            response = requests.post(
                                f"{PREFIX}/get_possible_solution/",
                                json={"text": issue_body, "comments": issue_comments},
                                headers=headers,
                            )
                            if response.status_code == 200:
                                possible_solution = response.json()
                            elif response.status_code == 403:
                                possible_solution = "No Possible Solution"
                                st.warning(
                                    "API call limit reached. Please consider upgrading your plan for continued access."
                                )
                            else:
                                st.write(f"Error: {response.status_code}")
                                possible_solution = "No Possible Solution"

                            st.session_state[similar_key] = possible_solution
                            if possible_solution:
                                possible_solution_html = "<div style='border: 1px solid #D2042D; padding: 10px; border-radius: 10px;'><h4>Possible Solution</h4>"
                                possible_solution_html += f"<p>{possible_solution}</p>"
                                possible_solution_html += "</div>"
                                st.markdown(
                                    possible_solution_html, unsafe_allow_html=True
                                )
                                st.write("<p></p>", unsafe_allow_html=True)
                                st.experimental_rerun()
    else:
        st.write("No issues found.")


if __name__ == "__main__":
    issuesearch()