{{ config(
    materialized='table',
    partition_by={
        "field": "ingestion_date",
        "data_type": "date"
    }
)}}

SELECT
current_date("America/Bogota") AS ingestion_date,
id,
name,
species,
status,
type,
gender,
origin_name,
location_name
FROM `{{ var('project_name') }}.{{ var('dataset_bronze') }}.{{ var('table_characters_bronze') }}`


