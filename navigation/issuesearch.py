import os

import openai
import requests
import streamlit as st
from dotenv import load_dotenv

from backend.database import SessionLocal
from utils.core_helpers import (
    get_embeddings,
    get_open_issues,
    get_possible_solution,
    get_summary,
    get_unique_owner_repo_pairs,
)

load_dotenv()

GITHUB_ACCESS_TOKEN = os.environ.get("access_token")
openai.api_key = os.environ.get("OPENAI_API_KEY")
PREFIX = os.environ.get("PREFIX")

session = SessionLocal()


def issuesearch(access_token, user_id):
    headers = {"Authorization": f"Bearer {access_token}"}

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
        for issue in issues:
            issue_title = issue["title"]
            issue_body = issue["body"]
            issue_comments = issue["comments_data"]
            with st.expander(issue_title):
                st.write(issue_body)
                st.write("Comments:")
                if issue_comments:
                    for comment in issue_comments:
                        st.write(comment["user"]["login"] + ":")
                        st.write(comment["body"])
                else:
                    st.write("No Comments.")

                summary_key = f"summary_{issue['number']}"
                if st.session_state.get(summary_key):
                    st.markdown(
                        f"<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Summary</h4>{st.session_state[summary_key]}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(
                        "Reveal the Essence.", key=f"summary_button_{issue['number']}"
                    ):
                        with st.spinner("Generating summary..."):
                            summary = get_summary(issue_body)
                            st.session_state[summary_key] = summary
                            st.markdown(
                                f"<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Summary</h4>{summary}</div>",
                                unsafe_allow_html=True,
                            )
                            st.experimental_rerun()

                st.write("<p></p>", unsafe_allow_html=True)

                similar_key = f"similar_{issue['number']}"
                if st.session_state.get(similar_key):
                    if isinstance(st.session_state[similar_key], list):
                        similar_issues = st.session_state[similar_key]
                        similar_issues_html = "<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Similar Issues</h4>"
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
                            possible_solution_html = "<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Possible Solution</h4>"
                            possible_solution_html += f"<p>{possible_solution}</p>"
                            possible_solution_html += "</div>"
                            st.markdown(possible_solution_html, unsafe_allow_html=True)
                            st.write("<p></p>", unsafe_allow_html=True)
                else:
                    if st.button(f"Find similar issues for {issue_title}"):
                        embeddings = get_embeddings(issue_body)
                        response = requests.get(
                            f"{PREFIX}/similar_issues",
                            params={
                                "embedded_issue_text_dict": str(embeddings),
                                "selected_owner": selected_owner,
                                "selected_repo": selected_repo,
                            },
                            headers=headers,
                        )
                        if response.status_code == 200:
                            similar_issues = response.json()
                        else:
                            st.write(f"Error: {response.status_code}")
                            similar_issues = "None LOL"
                        if similar_issues != "None LOL" and similar_issues != []:
                            st.session_state[similar_key] = similar_issues
                            similar_issues_html = "<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Similar Issues</h4>"
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
                            possible_solution = get_possible_solution(issue_body)
                            st.session_state[similar_key] = possible_solution
                            if possible_solution:
                                possible_solution_html = "<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Possible Solution</h4>"
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
