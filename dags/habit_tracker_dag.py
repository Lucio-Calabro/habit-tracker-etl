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
import json # noqa: E402

from airflow import DAG # noqa: E402
from airflow.operators.python import PythonOperator # noqa: E402
from airflow.providers.postgres.hooks.postgres import PostgresHook # noqa: E402

#import pandas as pd # noqa: E402
#from sqlalchemy import text, create_engine # noqa: E402

#from src.clases import Clean_habit # noqa: E402

from src.src import consultar_respuestas, transform_pre_value , get_date# noqa: E402



logger = logging.getLogger(__name__)


simulacion_telegram = {
    "update_id": 123456789,
    "message": {
        "message_id": 42,
        "from": {"id": 987654321, "is_bot": False, "first_name": "Lucio"},
        "date": 1708785600,
        "text": "Gym 1",
    },
}


def extract_raw(**context):
    respuestas = consultar_respuestas(logger)

    hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")

    query = """
        INSERT INTO raw_events (data_source, message_id, run_id, payload)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (message_id) DO NOTHING;
    """
    for r in respuestas:
        try:

            data_source = "telegram"

            if 'message' in r:
                message_id = str(r["message"]["message_id"])
            
            elif 'callback_query' in r:
                message_id = str(r['callback_query']["message"]["message_id"])

            run_id = context["run_id"]
            payload = json.dumps(r)

            hook.run(query, parameters=(data_source, message_id, run_id, payload))

            logger.info(f'Respuesta agregada correctamente a tabla raw_events, message_id : {message_id}')

        except Exception as e:
            logger.error(f"Error al intentar cargar una respuesta en raw_events : {e}")


def transform(**context):
    hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")

    query = """
        SELECT payload
        FROM raw_events
        WHERE run_id = %s;
    """

    habits = hook.get_records(query,parameters = (context['run_id'],))
    
    date = get_date(habits)

    clean_data = []

    query_id = """
        SELECT name, habit_id
        FROM habits;
    """
    habits_id = hook.get_records(query_id)
    map_habits = {fila[0]:fila[1] for fila in habits_id}

    for h in habits:
        payload = h[0]
        if 'callback_query' in payload:
            response = payload['callback_query']['data']


            name, pre_value = response.split('_')

            value = transform_pre_value(pre_value)
            habit_id = map_habits.get(name)

            clean = {
                'date':date,
                'value':value,
                'habit_id':habit_id
            }

            clean_data.append(clean)
        
        elif 'message' in payload:
            response = payload['message']['text']

            name_and_value = response.split(' ')
            name = name_and_value[0]
            value = int(name_and_value[1])

            habit_id = map_habits.get(name)

            clean = {
                'date':date,
                'value':value,
                'habit_id':habit_id
            }

            clean_data.append(clean)

    return clean_data    


def load_core(**context):
    data = context['ti'].xcom_pull(task_ids='transform')

    if not data:
        logger.info('No hay datos para subir')
        return

    hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")

    for d in data:
        try:
            date = d.get('date')
            value = d.get('value')
            habit_id = d.get('habit_id')

            query = """
                INSERT INTO habits_logs(date, value, habit_id)
                VALUES (%s,%s,%s)
                ON CONFLICT (date, habit_id)
                DO UPDATE SET value = EXCLUDED.value;
            """

            hook.run(query,parameters=(date,value,habit_id))

            logger.info(f'Dato limpio cargado, date : {date}, habit_id : {habit_id}')
        except Exception as e:
            logger.error(f'Error al cargar los datos limpios : {e}')
    

def monthly_update(**context):
    
    hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")

    target_month = context['ds'].replace('-', '')[:6]

    query = """
        INSERT INTO monthly_progress (month_date,habit_id,mtd_value,last_updated_at)

        SELECT 
            TO_CHAR(date, 'YYYYMM') as month_date,
            habit_id,
            SUM(value) as mtd_value,
            CURRENT_TIMESTAMP AS last_updated_at
        FROM habits_logs
        WHERE TO_CHAR(date,'YYYYMM') = %s
        GROUP BY TO_CHAR(date,'YYYYMM'),habit_id

        ON CONFLICT (month_date,habit_id)
        DO UPDATE SET
            mtd_value = EXCLUDED.mtd_value,
            last_updated_at = EXCLUDED.last_updated_at;
    """

    try:
        hook.run(query, parameters=(target_month,))
        logger.info(f"Progreso mensual actualizado para el mes {target_month}")
    except Exception as e:
        logger.error(f"Error actualizando mes {e}")





default_args = {"owner": "Lucio", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="habit_tracker",
    default_args=default_args,
    description="DAG que se encarga de recibir los datos en crudo cargador por el usuario para poder limpiarlos y almacenarlos para que puedan ser consumidos por el usuario al finalizar el mes",
    start_date=datetime(2026, 2, 2),
    schedule_interval="@daily",
    catchup=False,
) as dag:

    task_extract_raw = PythonOperator(task_id="extract_raw", python_callable=extract_raw)

    task_transform = PythonOperator(task_id="transform", python_callable=transform)

    task_load_core = PythonOperator(task_id="load_core", python_callable=load_core)

    task_monthly_update = PythonOperator( task_id='monthly_update',python_callable=monthly_update)

    task_extract_raw >> task_transform >> task_load_core >> task_monthly_update
