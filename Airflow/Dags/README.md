# Airflow Project Readme

This repository contains three Airflow DAGs for performing various data processing tasks.

## Embedding

The `Embedding` DAG is scheduled to run daily and fetches GitHub issue data, stores it in Snowflake, and computes embeddings. It consists of the following tasks:

- `fetch_owner_repo_pairs_task`: Retrieves owner-repo pairs from Snowflake.
- `fetch_and_store_github_issues_task`: Fetches all issues for each repository, preprocesses them, and stores them in Snowflake.
- `compute_embeddings_task`: Computes embeddings for preprocessed issues and stores them in XCom.
- `store_embeddings_in_milvus_task`: Stores embeddings in a Milvus database.

The DAG is defined using the `>>` operator to define the order in which the tasks should be executed. All tasks have the `provide_context=True` argument to enable them to access the DAG context and share information with other tasks using XCom. The `op_args` argument is used to specify the upstream tasks for a given task.

## github_issues_dag

The `github_issues_dag` is cron-scheduled to run at 12 AM every day. This DAG automates the data retrieval from Snowflake, runs the Great Expectations validation suite, and publishes the validation results to the specified S3 bucket. It consists of the following tasks:

- `extract_issues_task`: Extracts all the records for the columns `CREATE_BY`, `ID`, `ISSUE_NUMBER`, `ISSUE_URL`, `REPO_NAME`, `REPO_OWNER`, `STATE`, `TITLE`, and `UPDATED_AT` stored in a Snowflake table and stores them in a CSV file.
- `ge_data_context_root_dir_with_checkpoint_name_pass_task`: Runs the Great Expectations validation suite on the checkpoint created and adds the validation results to the `data_docs` folder to create `index.html` which presents the result of data check.
- `upload_ge_reports_task`: Pushes the files and folders created in `local_site`, which are responsible for creating the `index.html`, to the Amazon S3 bucket `great_expectations` for static hosting the webpage by using the property of S3 bucket.

## update_api_calls

The `update_api_calls` DAG runs every hour to update the number of API calls for the user we have for the system based on their subscription type. It consists of a single Python operator that updates the API call count in a Snowflake table using a SQL query.

query = """
        UPDATE APP_USERS SET calls_remaining =
            CASE service
                WHEN 'Free - (0$)' THEN 10
                WHEN 'Gold - (50$)' THEN 15
                WHEN 'Platinum - (100$)' THEN 20
                ELSE calls_remaining -- Handle invalid account types
            END;
    """

### Dependencies

- Snowflake
- Hugging Face Transformers
- PyMilvus
- Great Expectations
- Amazon S3

### Usage

To use this project, follow these steps:

1. Install the dependencies listed above.
2. Clone this repository to your local machine.
3. Update the credentials for Snowflake and Amazon S3 in the appropriate configuration files.
4. Copy the DAGs in this repository to your Airflow `dags` folder.
5. Start the Airflow scheduler and web server.
6. Trigger the DAGs manually or wait for them to run according to their schedules.
