# AIssue Flow :zap: [![Continuous Integration - Unit Testing](https://github.com/BigDataIA-Spring2023-Team-04/Final-Project-Playground/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/BigDataIA-Spring2023-Team-04/Final-Project-Playground/actions/workflows/pytest.yml)

## Live application Links :octopus:

- Please use this application responsibly, as we have limited free credits remaining.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](http://34.148.167.159:8051/)

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white)](http://34.148.167.159:8050/docs)

[![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-007A88?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)](http://34.138.127.169:8080/)

[![Great Expectations](https://img.shields.io/badge/Great_Expectations-FF5733?style=for-the-badge)](http://getest1.s3-website-us-east-1.amazonaws.com)

[![codelabs](https://img.shields.io/badge/codelabs-4285F4?style=for-the-badge&logo=codelabs&logoColor=white)](https://codelabs-preview.appspot.com/?file_id=1blarGD_LQ5o5aGcJWiKKbhDBissQSL9qfs28dx5HyFk#11)

[![Demo Link](https://img.shields.io/badge/Demo_Link-808080?style=for-the-badge&logo=YouTube&logoColor=white)](https://youtu.be/DnmAYNL0kcI)







## Abstract :memo: 

The rapid growth of software development projects on GitHub necessitates efficient and intelligent issue management solutions. AIssueFlow is a novel, real-time adaptive intelligence system designed to streamline the process of managing GitHub issues. The system retrieves open issues in real-time and employs a pre-trained BERT model to generate embeddings, which are then stored in a Snowflake database. By leveraging the Milvus similarity search engine, AIssueFlow identifies and returns similar issues, enabling the scrum master to make informed assignment decisions based on developers' domain expertise.

Furthermore, AIssueFlow features an analytics page, providing users with insights into their API usage history, and an admin page, allowing administrators to add repositories to the system. This comprehensive solution not only enhances issue management efficiency but also promotes better collaboration and productivity within software development teams. Through the integration of state-of-the-art technologies, such as BERT embeddings, Milvus similarity search, and Snowflake storage, AIssueFlow represents the next generation of intelligent GitHub issue management.

## Project Goals :dart:

1. Scrape issue-related data from various GitHub repositories using the GitHub API and store it in a Snowflake database along with associated metadata.
2. Use the BERT model to convert issue bodies into vector embeddings and store them in a Milvus database for efficient similarity search.
3. Develop two main functions, Git Magnet and Git Cognizant, to make the project more user-friendly.
4. Use the GPT 3.5 Turbo model to summarize issues and leverage Milvus to find similar issues for the selected issue.
5. If no similar issues are found, provide assistance to the user through the GPT 3.5 Turbo to find potential solutions to the issue, using prompt enginerring.

## Use case :bookmark_tabs:

The use case for this project could be to help software developers and teams better manage their projects on GitHub. By using the GitHub API to scrape issue-related data, storing it in a database, and leveraging advanced NLP and vector similarity algorithms, developers can more easily search for and find relevant issues, as well as summarize them for quicker understanding. This can lead to faster issue resolution and more efficient project management overall.

## Technologies Used :computer:

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/)
[![FastAPI](https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white)](https://fastapi.tiangolo.com/)
[![Amazon AWS](https://img.shields.io/badge/Amazon_AWS-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/HTML5)
[![Pandas](https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/Numpy-777BB4?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Apache Airflow](https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)](https://airflow.apache.org/)
[![GitHub Actions](https://img.shields.io/badge/Github%20Actions-282a2e?style=for-the-badge&logo=githubactions&logoColor=367cfe)](https://github.com/features/actions)

## Data Source :flashlight:

The data source for this project is the GitHub API, which provides access to all the issue-related data for public repositories. 

## Process Outline

**1. Data Collection:** Use GitHub API to extract issue-related data from various repositories and store it in a Snowflake database.

**2. Data Preprocessing:** Clean and preprocess the collected data to make it suitable for analysis.

**3. Feature Extraction:** Use the BERT model to extract vector embeddings from the issue body text.

**4. Data Validation:** Use Great Expectations to validate the collected data and ensure it meets the expected format and values.

**5. Vector Embedding:** Use the BERT model to convert issue bodies into vector embeddings and store them in a Milvus database.

**6. Similarity Search:** Use Milvus to search for similar issues based on the generated vector embeddings.

**7. User Interface:** Build a web application using Streamlit to provide an intuitive interface for users to search and explore the collected issue data and its embeddings.

**8. Testing:** Use pytest for unit testing to ensure the functionality of the application and its components.

**9. Deployment:** Host the application in cloud and deploy it using Airflow and a GCP instance.

## Project Setup

<img width="607" alt="image" src="https://user-images.githubusercontent.com/114537365/234988315-a9f89c76-b0ac-413c-9f4b-977eb7c5eab9.png">


## Requirements
```
fastapi==0.92.0

passlib==1.7.4

pydantic==1.10.4

python-dotenv==1.0.0

:snake: python-jose==3.3.0

snowflake-connector-python==3.0.2

snowflake-sqlalchemy==1.4.7

:open_file_folder: SQLAlchemy==1.4.47

gunicorn==20.1.0

uvicorn==0.20.0

python-multipart

🔢 numpy==1.23.5

openai==0.27.0

pymilvus==2.2.6

transformers==4.27.4

🖼streamlit==1.18.1
```

## Project Folder Structure

```
📦 Final-Project-Playground
├─ .github
│  └─ workflows
│     └─ pytest.yml
├─ .gitignore
├─ Airflow
│  └─ Dags
│     ├─ README.md
│     ├─ db_update.py
│     ├─ ge_report.py
│     └─ issue_embedding_and_storing.py
├─ Dockerfile
├─ README.md
├─ __init__.py
├─ backend
│  ├─ .DS_Store
│  ├─ Dockerfile
│  ├─ __init__.py
│  ├─ database.py
│  ├─ hashing.py
│  ├─ main.py
│  ├─ models.py
│  ├─ requirements.txt
│  └─ schema.py
├─ bert_download.py
├─ docker-compose.yml
├─ great_expectations
│  ├─ .gitignore
│  ├─ README.md
│  ├─ checkpoints
│  │  ├─ github_issues_checkpoint_v0.yml
│  │  └─ github_issues_checkpoint_v1.yml
│  ├─ expectations
│  │  ├─ .ge_store_backend_id
│  │  └─ github_issues_suite.json
│  ├─ great_expectations.yml
│  └─ plugins
│     └─ custom_data_docs
│        └─ styles
│           └─ data_docs_custom_styles.css
├─ navigation
│  ├─ __init__.py
│  ├─ adminworkarea.py
│  ├─ analytics.py
│  ├─ errorsearch.py
│  └─ issuesearch.py
├─ pyrequirements.txt
├─ requirements.txt
├─ unit_testing.py
├─ userinterface.py
└─ utils
   ├─ __init__.py
   └─ core_helpers.py
```
©generated by [Project Tree Generator](https://woochanleee.github.io/project-tree-generator)


## How to run Application locally

To run the application locally, follow these steps:

1. Clone the repository to get all the source code on your machine.

2. Create a virtual environment and install all requirements from the requirements.txt file present.

3. Create a .env file in the root directory with the following variables:

    GITHUB_API_TOKEN: your GitHub API token.

    SNOWFLAKE_USER: your Snowflake username.

    SNOWFLAKE_PASSWORD: your Snowflake password.

    SNOWFLAKE_ACCOUNT: your Snowflake account name.

    SNOWFLAKE_DATABASE: the name of the Snowflake database to use.

    SNOWFLAKE_SCHEMA: the name of the Snowflake schema to use.

    ACESS_TOKEN: Your Github Acess token

    SECRET_KEY: "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" - for JWT Hashing

    ALGORITHM: "HS256" - - for JWT Hashing

    ACCESS_TOKEN_EXPIRE_MINUTES: The expiration time of the access token in minutes

    OPENAI_API_KEY: Your OpenAI API key for accessing the GPT model.

4. Once you have set up your environment variables, start Airflow by running the following command from the root directory:

docker-compose up airflow-init && docker-compose up -d

5. Access the Airflow UI by navigating to http://localhost:8080/ in your web browser.

6. To run the DAGs in Airflow, click on the dags links on the Airflow UI and toggle the switch to enable the DAGs.

7. Once the DAGs have run successfully, start the Streamlit application by running the following command from the streamlit-app directory:

docker-compose up

8. Access the Streamlit UI by navigating to http://localhost:8501/ in your web browser.

9. Enter GitHub username and select a repository from the dropdown menu to view the issues associated with that repository. You can summarize or find similar issues using the options provided on the UI.

## Github Actions - Testing

<img width="1512" alt="image" src="https://user-images.githubusercontent.com/114537365/235001553-2dc11cd4-9131-48d2-a57b-75b302aeb372.png">




