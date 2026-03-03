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
from airflow.providers.postgres.hooks.postgres import PostgresHook # noqa: E402

from src.src import send_email,generar_reporte # noqa: E402

logger = logging.getLogger(__name__)


def load_monthly_report(**context):

    hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")

    target_month = context['ds'].replace('-', '')[:6]

    query = """
        INSERT INTO monthly_report (month_date,habit_id,final_value,target_value, compliance_ratio)
        SELECT 
            mp.month_date AS month_date,
            h.habit_id AS habit_id,
            mp.mtd_value AS final_value,
            h.monthly_target AS target_value,
            ROUND((mp.mtd_value::NUMERIC / h.monthly_target::NUMERIC ) * 100,2) AS compliance_ratio
        FROM monthly_progress mp
        INNER JOIN habits h ON mp.habit_id = h.habit_id
        WHERE mp.month_date = %s
        ON CONFLICT (month_date,habit_id)
        DO UPDATE SET
            final_value = EXCLUDED.final_value,
            target_value = EXCLUDED.target_value,
            compliance_ratio = EXCLUDED.compliance_ratio;

    """
    try:
        hook.run(query,parameters=(target_month,))
        logger.info(f"Datos de {target_month} cargados correctamente a monthly_report")

    except Exception as e:
        logger.error(f"Error al cargar {target_month} en la tabla monthly_report: {e}")

def report(**context):
    hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")
    target_month = context['ds'].replace('-', '')[:6]

    query = """
        SELECT mr.month_date, mr.final_value, mr.target_value, mr.compliance_ratio, h.name
        FROM monthly_report mr
        INNER JOIN habits h ON h.habit_id = mr.habit_id  
        WHERE month_date = %s
    """

    monthly_reports = hook.get_records(query,parameters=(target_month,))

    reporte = generar_reporte(monthly_reports)
    send_email(reporte, logger)
    




default_args = {"owner": "Lucio", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="monthly_report",
    default_args=default_args,
    description="DAG que se encarga de cerrar el mes, cargar los datos en la tabla monthly_report y generar el informe final de mes",
    start_date=datetime(2026, 2, 2),
    schedule_interval="@monthly",
    catchup=False,
) as dag:

    task_load_monthly_report = PythonOperator(task_id="load_monthly_report", python_callable=load_monthly_report)

    task_report = PythonOperator(task_id="report", python_callable=report)

    task_load_monthly_report >> task_report 


