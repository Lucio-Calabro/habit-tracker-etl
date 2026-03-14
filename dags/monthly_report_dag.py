import sys
import os
# Path - Gemini
ruta_actual = os.path.dirname(__file__)
ruta_pasillo = os.path.join(ruta_actual, '..')
ruta_completa = os.path.abspath(ruta_pasillo)
sys.path.append(ruta_completa)
sys.path.append('/home/lucio/HabitTracker')
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

    target_month = datetime.now() - timedelta(days=5)
    target_month = target_month.strftime('%Y%m')

    query = """
        INSERT INTO monthly_report (month_date, habit_id, final_value, target_value, compliance_ratio)
        SELECT 
            %s AS month_date,
            h.habit_id,
            CASE 
                WHEN h.name = 'dormir' THEN ROUND(AVG(hl.value)::NUMERIC, 2)
                ELSE SUM(hl.value) 
            END AS final_value,
            h.monthly_target AS target_value,
            CASE 
                WHEN h.name = 'dormir' THEN ROUND((AVG(hl.value)::NUMERIC / h.monthly_target::NUMERIC) * 100, 2)
                ELSE ROUND((SUM(hl.value)::NUMERIC / h.monthly_target::NUMERIC) * 100, 2) 
            END AS compliance_ratio
        FROM habits_logs hl
        INNER JOIN habits h ON hl.habit_id = h.habit_id
        WHERE TO_CHAR(hl.date, 'YYYYMM') = %s
        GROUP BY h.habit_id, h.monthly_target, h.name
        ON CONFLICT (month_date, habit_id)
        DO UPDATE SET
            final_value = EXCLUDED.final_value,
            target_value = EXCLUDED.target_value,
            compliance_ratio = EXCLUDED.compliance_ratio;
    """
    
    try:
        # IMPORTANTE: Ahora pasamos target_month dos veces porque la query usa %s en el SELECT y en el WHERE
        hook.run(query, parameters=(target_month, target_month))
        logger.info(f"Datos de {target_month} cargados correctamente a monthly_report")

    except Exception as e:
        logger.error(f"Error al cargar {target_month} en la tabla monthly_report: {e}")

def report(**context):
    # hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")
    # target_month = datetime.now() - timedelta(days=5)
    # target_month = target_month.strftime('%Y%m')

    # query = """
    #     SELECT mr.month_date, mr.final_value, mr.target_value, mr.compliance_ratio, h.name
    #     FROM monthly_report mr
    #     INNER JOIN habits h ON h.habit_id = mr.habit_id  
    #     WHERE month_date = %s
    # """

    # monthly_reports = hook.get_records(query,parameters=(target_month,))

    # reporte = generar_reporte(monthly_reports)
    # send_email(reporte, logger)


    hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")
    target_month = datetime.now() - timedelta(days=5)
    target_month = target_month.strftime('%Y%m')

    # Buscamos el promedio del año en curso (YTD) y el valor del mes actual
    query = """
        SELECT 
            h.name,
            ROUND(AVG(mr.compliance_ratio), 2) AS ytd_ratio,
            MAX(CASE WHEN mr.month_date = %s THEN mr.compliance_ratio ELSE 0 END) AS current_ratio
        FROM monthly_report mr
        INNER JOIN habits h ON h.habit_id = mr.habit_id  
        WHERE LEFT(mr.month_date, 4) = LEFT(%s, 4) -- Mismo Año
          AND mr.month_date <= %s -- Hasta el mes objetivo inclusive
        GROUP BY h.name;
    """

    # Le pasamos el parámetro 3 veces porque la query lo pide en 3 lugares
    monthly_reports = hook.get_records(query, parameters=(target_month, target_month, target_month))

    reporte_html = generar_reporte(monthly_reports)
    send_email(reporte_html, logger)
    




default_args = {"owner": "Lucio", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="monthly_report",
    default_args=default_args,
    description="DAG que se encarga de cerrar el mes, cargar los datos en la tabla monthly_report y generar el informe final de mes",
    start_date=datetime(2026, 2, 2),
    schedule_interval="0 5 1 * *",
    catchup=False,
) as dag:

    task_load_monthly_report = PythonOperator(task_id="load_monthly_report", python_callable=load_monthly_report)

    task_report = PythonOperator(task_id="report", python_callable=report)

    task_load_monthly_report >> task_report 


