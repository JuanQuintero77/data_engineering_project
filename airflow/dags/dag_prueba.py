from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def _print_hello():
    print(">>> HOLA DESDE AIRFLOW LOGS <<<")

with DAG(
    dag_id = "dag_test_logs",
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    say_hello=PythonOperator(
        task_id="say_hello",
        python_callable=_print_hello,
    )
    
say_hello