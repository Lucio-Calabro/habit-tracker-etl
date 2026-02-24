from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text, create_engine
import logging

logger = logging.getLogger(__name__)

json = {
    "update_id": 123456789,
    "message": {
        "message_id": 42,
        "from": {"id": 987654321, "is_bot": False, "first_name": "Lucio"},
        "date": 1708785600,
        "text": "Gym 1",
    },
}


def extract_raw():
    pass


def transform():
    pass


def load_core():
    pass


default_args = {"owner": "Lucio", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="habit_tracker",
    default_args=default_args,
    description="DAG que se encarga de recibir los datos en crudo cargador por el usuario para poder limpiarlos y almacenarlos para que puedan ser consumidos por el usuario al finalizar el mes",
    start_date=datetime(2026, 2, 2),
    schedule_interval="@daily",
    catchup=False,
) as dag:

    task_extract_raw = PythonOperator(
        task_id="extract_raw", python_callable=extract_raw
    )

    task_transform = PythonOperator(task_id="transform", python_callable=transform)

    task_load_core = PythonOperator(task_id="load_core", python_callable=load_core)

    task_extract_raw >> task_transform >> task_load_core
