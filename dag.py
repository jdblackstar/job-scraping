import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv

from helpers.db_helper import write_to_db
from scrape.linkedin_scrape import login, page_search

load_dotenv()

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2022, 1, 1),
    "email": [os.getenv("ALERT_EMAIL")],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG("linkedin_scraper", default_args=default_args, schedule_interval=timedelta(1))

task_login = PythonOperator(
    task_id="login",
    python_callable=login,
    dag=dag,
)

task_page_search = PythonOperator(
    task_id="page_search",
    python_callable=page_search,
    dag=dag,
)

task_write_to_db = PythonOperator(
    task_id="write_to_db",
    python_callable=write_to_db,
    dag=dag,
)

task_login >> task_page_search >> task_write_to_db
