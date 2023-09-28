import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
from loguru import logger

from helpers.db_helper import write_to_mysql
from helpers.discord_alert import on_dag_status_change
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

task_discord_start = PythonOperator(
    task_id="discord_start",
    python_callable=on_dag_status_change("start"),
    op_args=[],
    dag=dag,
)

task_discord_finish = PythonOperator(
    task_id="discord_finish",
    python_callable=on_dag_status_change("finish"),
    op_args=[],
    dag=dag,
)

task_li_de_search = PythonOperator(
    task_id="li_de_search",
    python_callable=page_search,
    op_args=[
        login(),
        "90000084",  # sf bay area
        "data engineer",  # data engineer job title
        "2,1,3",  # remote, hybrid, on-site
        "r86400",  # last 24 hours
        "1",
        logger,
    ],
    dag=dag,
)

task_le_swe_search = PythonOperator(
    task_id="li_swe_search",
    python_callable=page_search,
    op_args=[
        login(),
        "90000084",  # sf bay area
        "software engineer data",  # software engineer job title
        "2,1,3",  # remote, hybrid, on-site
        "r86400",  # last 24 hours
        "1",
        logger,
    ],
)

# run the actual DAG
(
    task_post_starting_message
    >> [task_li_de_search, task_le_swe_search]
    >> task_post_ending_message
)
