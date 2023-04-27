# AIssue Flow :zap:

## Abstract :memo: 
Project Goals:

1. Scrape issue-related data from various GitHub repositories using the GitHub API and store it in a Snowflake database along with associated metadata.
2. Use the BERT model to convert issue bodies into vector embeddings and store them in a Milvus database for efficient similarity search.
3. Develop two main functions, Git Magnet and Git Cognizant, to make the project more user-friendly.
4. Use the ChatGPT model to summarize issues and leverage Milvus to find similar issues for the selected issue.
5. If no similar issues are found, provide assistance to the user through the GPT Intelligent Chatbot to find potential solutions to the issue.


