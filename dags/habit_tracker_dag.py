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
import pendulum # noqa: E402

from airflow import DAG # noqa: E402
from airflow.operators.python import PythonOperator # noqa: E402
from airflow.providers.postgres.hooks.postgres import PostgresHook # noqa: E402
from airflow.models import Variable # noqa: E402

from src.src import consultar_respuestas, interpretar_response# noqa: E402



logger = logging.getLogger(__name__)


def extract_raw(**context):
    respuestas, nuevo_offset = consultar_respuestas(logger)

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
            

            run_id = context["run_id"]
            payload = json.dumps(r)

            hook.run(query, parameters=(data_source, message_id, run_id, payload))

            logger.info(f'Respuesta agregada correctamente a tabla raw_events, message_id : {message_id}')

        except Exception as e:
            logger.error(f"Error al intentar cargar una respuesta en raw_events : {e}")
    
    if nuevo_offset:
        Variable.set("telegram_update_offset", nuevo_offset)


def transform(**context):
    hook = PostgresHook(postgres_conn_id="postgrest_habit_tracker")

    query = """
        SELECT payload
        FROM raw_events
        WHERE run_id = %s;
    """

    habits = hook.get_records(query,parameters = (context['run_id'],))
    
    clean_data = []

    query_id = """
        SELECT name, habit_id
        FROM habits;
    """
    habits_id = hook.get_records(query_id)
    map_habits = {fila[0]:fila[1] for fila in habits_id}

    for h in habits:
        try:
            payload = h[0]
            
            if 'message' in payload and 'text' in payload['message']:
                
                date = payload['message']['date']
                response = payload['message']['text']

                fecha_utc = pendulum.from_timestamp(int(date))
                fecha_arg = fecha_utc.in_timezone("America/Argentina/Buenos_Aires")
                clean_date = fecha_arg.strftime('%Y-%m-%d')

                id_and_value = interpretar_response(response, map_habits)
                habit_id = id_and_value[0]
                value = id_and_value[1]

                if habit_id is not None and value is not None:
                    clean = {
                        'date': clean_date,
                        'value': int(value),
                        'habit_id': habit_id
                    }
                    clean_data.append(clean)
                    
        except Exception as e:
            logger.error(f"Error {e} procesando el payload: {payload}")

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

    ahora_arg = pendulum.now("America/Argentina/Buenos_Aires")
    fecha_segura = ahora_arg.subtract(hours=6)
    target_month = fecha_segura.strftime('%Y%m')

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





default_args = {"owner": "Lucio", "retries": 2, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="habit_tracker",
    default_args=default_args,
    description="DAG que se encarga de recibir los datos en crudo cargador por el usuario para poder limpiarlos y almacenarlos para que puedan ser consumidos por el usuario al finalizar el mes",
    start_date=datetime(2026, 2, 2),
    schedule_interval="0 2 * * *",
    catchup=False,
) as dag:

    task_extract_raw = PythonOperator(task_id="extract_raw", python_callable=extract_raw)

    task_transform = PythonOperator(task_id="transform", python_callable=transform)

    task_load_core = PythonOperator(task_id="load_core", python_callable=load_core)

    task_monthly_update = PythonOperator( task_id='monthly_update',python_callable=monthly_update)

    task_extract_raw >> task_transform >> task_load_core >> task_monthly_update
