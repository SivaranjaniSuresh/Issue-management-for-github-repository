import os
import boto3
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import snowflake.connector
from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python_operator import PythonOperator
from great_expectations_provider.operators.great_expectations import GreatExpectationsOperator
from great_expectations.data_context.types.base import (
    DataContextConfig,
    CheckpointConfig
)

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
    table=SNOWFLAKE_TABLE,
)

base_path = "/opt/airflow/working_data"
#base_path = Path(__file__).parents[1]
ge_root_dir = os.path.join(base_path, "great_expectations")
data_file = os.path.join(base_path, "data/issue.csv")
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'github_issues_dag',
    default_args=default_args,
    description='Transcribe all audio files daily and move them to the appropriate folders',
    schedule_interval='0 0 * * *',
    start_date=datetime(2023, 4, 11),
    catchup=False
)

import pandas as pd
def extract_github_issues():
    cursor = conn.cursor()
    cursor.execute('SELECT ID, ISSUE_URL,REPO_OWNER,REPO_NAME,ISSUE_NUMBER,CREATED_BY,TITLE,BODY,STATE,UPDATED_AT FROM GITHUB_ISSUES.PUBLIC.ISSUES')
    cols = [col[0] for col in cursor.description]
    results = pd.DataFrame(cursor.fetchall(), columns=cols)
    
    # Close Snowflake connection
    cursor.close()
    conn.close()
    
    # Save results to CSV file
    results.to_csv('/opt/airflow/working_data/data/issues.csv', index=False)
    
    return None

file_path = '/opt/airflow/working_data/great_expectations/uncommitted/data_docs/local_site/index.html'
s3_bucket = 'damg1234'
s3_key = 'great_expectations/report.html'

def upload_to_s3():
    """
    Uploads a file to an Amazon S3 bucket.

    Parameters:
    file_path (str): The local file path of the file to be uploaded to S3.
    s3_bucket (str): The name of the S3 bucket to upload the file to.
    s3_key (str): The name of the key that the file will be stored under in S3.

    Returns:
    str: A message indicating if the file was uploaded successfully or if an error occurred.
    """
    AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
    AWS_REGION = os.environ.get('AWS_REGION')
    
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION,
    )

    # Upload the contents of the data_docs folder to the S3 bucket
    for root, dirs, files in os.walk('/opt/airflow/working_data/great_expectations/uncommitted/data_docs/local_site'):
        for file in files:
            local_file_path = os.path.join(root, file)
            s3_key = os.path.relpath(local_file_path, '/opt/airflow/working_data/great_expectations/uncommitted/data_docs/local_site')
            s3.upload_file(local_file_path, s3_bucket, s3_key)
    
extract_issues_task = PythonOperator(
    task_id='extract_issues',
    python_callable=extract_github_issues,
    dag=dag
)

ge_data_context_root_dir_with_checkpoint_name_pass = GreatExpectationsOperator(
    task_id="ge_data_context_root_dir_with_checkpoint_name_pass",
    data_context_root_dir=ge_root_dir,
    checkpoint_name="github_issues_checkpoint_v1",
    fail_task_on_validation_failure=False
)

upload_ge_report_task = PythonOperator(
    task_id='upload_ge_report',
    python_callable=upload_to_s3,
    dag=dag
)

#Flow
extract_issues_task >> ge_data_context_root_dir_with_checkpoint_name_pass >> upload_ge_report_task
