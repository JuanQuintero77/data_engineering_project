from airflow import DAG
from shared.operators.api_pagination import FetchPaginatedApiDataOperator
from datetime import datetime
import json
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.functions import CloudFunctionInvokeFunctionOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator

default_args = {'owner': 'Juan Quintero',
                'retries': 1,
                'retry_delay': 10}

with DAG(dag_id="dag_rick_and_morty_api",
        tags=['api', 'rick_and_morty', 'api_paginated', 'custom_operator'],
        description="DAG to fetch paginated data from Rick and Morty API and store it in GCS",
        start_date=datetime(2024, 1, 1),
        default_args=default_args,
        catchup=False) as dag:
    
    start = EmptyOperator(task_id='start')

    get_character_info = FetchPaginatedApiDataOperator(
        task_id='get_characters_info_from_api',
        url='https://rickandmortyapi.com/api/character',
        method='GET',
        project_id='data-engineering-dev-464423',
        bucket='test_data_engineering_path',
        folder='raw',
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
            'input_bucket': 'test_data_engineering_path',
            'input_file': 'raw/rick_and_morty_characters.json',
            'output_bucket': 'test_data_engineering_path',
            'output_file': 'processed/rick_and_morty_characters.parquet'
        })},
        location='us-central1',
        project_id='data-engineering-dev-464423',
        gcp_conn_id='google_cloud_connection'
    )
    
    insert_bq = GCSToBigQueryOperator(
        task_id='load_data_to_bq',
        bucket='test_data_engineering_path',
        source_objects=['processed/rick_and_morty_characters.parquet'],
        destination_project_dataset_table='data-engineering-dev-464423.BRONZE.rick_and_morty_characters',
        schema_object='schemas/rick_and_morty_characters_schema.json',
        source_format='PARQUET',
        write_disposition='WRITE_TRUNCATE',
        gcp_conn_id='google_cloud_connection'
    )
    
    execute_sp = BigQueryInsertJobOperator(
        task_id='execute_stored_procedure',
        project_id='data-engineering-dev-464423',
        configuration={
            "query":{
                "query": "CALL `data-engineering-dev-464423.SILVER.sp_characters_bronze_to_silver`();",
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_connection'
    )
    
    move_file_to_historic_folder = GCSToGCSOperator(
        task_id = 'move_file_to_historic_folder',
        source_bucket = 'test_data_engineering_path',
        source_object = 'processed/rick_and_morty_characters.parquet',
        destination_bucket = 'test_data_engineering_path',
        destination_object = 'historic/rick_and_morty_characters_{{ ds_nodash }}.parquet',
        move_object = True,
        gcp_conn_id='google_cloud_connection'
    )
    
    
    end = EmptyOperator(task_id='end', trigger_rule='all_done')
    
start >> get_character_info >> process_json_api >> insert_bq >> execute_sp >> move_file_to_historic_folder >> end