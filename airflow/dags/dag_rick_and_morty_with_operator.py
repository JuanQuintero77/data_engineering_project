from airflow import DAG
from shared.operators.api_pagination import FetchPaginatedApiDataOperator
from datetime import datetime
import json
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.functions import CloudFunctionInvokeFunctionOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator
from airflow.models import Variable

config_project = json.loads(Variable.get('data-engineering-project'))
url=config_project['url']
project_id=config_project['project_id']
bucket=config_project['bucket']
folder_raw=config_project['folder_raw']
folder_processed=config_project['folder_processed']
folder_historic=config_project['folder_historic']
schema=config_project['schema']
bq_table=config_project['bq_table']
sp=config_project['sp']

default_args = {'owner': 'Juan Quintero',
                'retries': 1,
                'retry_delay': 10}

with DAG(dag_id="dag_rick_and_morty_api",
        tags=['api', 'rick_and_morty', 'api_paginated', 'custom_operator'],
        description="DAG to fetch paginated data from Rick and Morty API and store it in GCS",
        start_date=datetime(2025, 10, 1),
        default_args=default_args,
        catchup=False
    ) as dag:
    
    start = EmptyOperator(task_id='start')

    get_character_info = FetchPaginatedApiDataOperator(
        task_id='get_characters_info_from_api',
        url=url,
        method='GET',
        project_id=project_id,
        bucket=bucket,
        folder=folder_raw,
        compress=False,
        file_name='rick_and_morty_characters',
        extra_config={
                    'data_field': 'results',
                    'pagination_field': 'info',
                    'next_page_key': 'next',
                    'delay_between_pages': 1},
        verify_ssl=False
    )
    
    process_json_api = CloudFunctionInvokeFunctionOperator(
        task_id='process_json_api_response',
        function_id='process-rick-and-morty-characters',
        input_data={'data':json.dumps({
            'input_bucket': bucket,
            'input_file': f"{folder_raw}/rick_and_morty_characters.json",
            'output_bucket': bucket,
            'output_file': f"{folder_processed}/rick_and_morty_characters.parquet"
        })},
        location='us-central1',
        project_id=project_id,
        gcp_conn_id='google_cloud_connection'
    )
    
    insert_bq = GCSToBigQueryOperator(
        task_id='load_data_to_bq',
        bucket=bucket,
        source_objects=[f"{folder_processed}/rick_and_morty_characters.parquet"],
        destination_project_dataset_table=f"{project_id}.BRONZE.{bq_table}",
        schema_object=schema,
        source_format='PARQUET',
        write_disposition='WRITE_TRUNCATE',
        gcp_conn_id='google_cloud_connection'
    )
    
    execute_sp = BigQueryInsertJobOperator(
        task_id='execute_stored_procedure',
        project_id=project_id,
        configuration={
            "query":{
                "query": f"CALL {sp};",
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_connection'
    )
    
    move_file_to_historic_folder = GCSToGCSOperator(
        task_id = 'move_file_to_historic_folder',
        source_bucket = bucket,
        source_object = f"{folder_processed}/*.parquet",
        destination_bucket = bucket,
        destination_object = f'{folder_historic}/rick_and_morty_characters_{{ ds_nodash }}.parquet',
        move_object = True,
        gcp_conn_id='google_cloud_connection'
    )
    
    
    end = EmptyOperator(task_id='end', trigger_rule='all_done')
    
start >> get_character_info >> process_json_api >> insert_bq >> execute_sp >> move_file_to_historic_folder >> end