import sys
import os
# Path - Gemini
ruta_actual = os.path.dirname(__file__)
ruta_pasillo = os.path.join(ruta_actual, '..')
ruta_completa = os.path.abspath(ruta_pasillo)
sys.path.append(ruta_completa)
sys.path.append('/home/lucio/Escritorio/HabitTracker')
#

from datetime import datetime, timedelta # noqa: E402
import logging # noqa: E402
#import json # noqa: E402

from airflow import DAG # noqa: E402
from airflow.operators.python import PythonOperator # noqa: E402
#from airflow.providers.postgres.hooks.postgres import PostgresHook # noqa: E402

logger = logging.getLogger(__name__)


def extract():
    pass
def load_monthly_report():
    pass
def report():
    pass


default_args = {"owner": "Lucio", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="monthly_report",
    default_args=default_args,
    description="DAG que se encarga de cerrar el mes, cargar los datos en la tabla monthly_report y generar el informe final de mes",
    start_date=datetime(2026, 2, 2),
    schedule_interval="@monthly",
    catchup=False,
) as dag:
    task_extract = PythonOperator(task_id="extract", python_callable=extract)

    task_load_monthly_report = PythonOperator(task_id="load_monthly_report", python_callable=load_monthly_report)

    task_report = PythonOperator(task_id="report", python_callable=report)

    

    task_extract >> task_load_monthly_report >> task_report 


