import os
import sqlite3

import boto3
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import snowflake.connector

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 1,
    "execution_timeout": timedelta(hours=1),
}

dag = DAG(
    "update_api_calls",
    default_args=default_args,
    schedule_interval='0 * * * *', #runs every hour
    catchup=False,
)

SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")
SNOWFLAKE_USER_TABLE = os.environ.get("SNOWFLAKE_USER_TABLE")

conn = snowflake.connector.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA,
    table=SNOWFLAKE_USER_TABLE,
)

def update_api_calls():
    
    cursor = conn.cursor()
    query = """
        UPDATE APP_USERS SET calls_remaining =
            CASE service
                WHEN 'Free - (0$)' THEN 10
                WHEN 'Gold - (50$)' THEN 15
                WHEN 'Platinum - (100$)' THEN 20
                ELSE calls_remaining -- Handle invalid account types
            END;
    """
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()

run_this = PythonOperator(
    task_id="update_api_calls",
    python_callable=update_api_calls,
    dag=dag,
)

run_this