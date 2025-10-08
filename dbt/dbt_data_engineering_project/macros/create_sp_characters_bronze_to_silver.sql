-- macros/create_sp_characters_bronze_to_silver.sql
{% macro create_sp_characters_bronze_to_silver() %}
  {% set sql %}
    CREATE OR REPLACE PROCEDURE `{{ var('project_name') }}.{{ var('dataset_silver') }}.sp_characters_bronze_to_silver`()
    BEGIN
      MERGE INTO `{{ var('project_name') }}.{{ var('dataset_silver') }}.{{ var('table_characters_silver') }}` AS target
      USING (
        SELECT 
          ingestion_date,
          id,
          name,
          species,
          status,
          type,
          gender,
          origin_name,
          location_name
        FROM `{{ var('project_name') }}.{{ var('dataset_bronze') }}.{{ var('view_characters_bronze') }}`
      ) AS source
      ON target.id = source.id
      WHEN MATCHED THEN
        UPDATE SET
          target.ingestion_date = source.ingestion_date,
          target.name = source.name,
          target.species = source.species,
          target.status = source.status,
          target.type = source.type,
          target.gender = source.gender,
          target.origin_name = source.origin_name,
          target.location_name = source.location_name
      WHEN NOT MATCHED THEN
        INSERT (
          ingestion_date, id, name, species, status, type, gender, origin_name, location_name
        )
        VALUES (
          source.ingestion_date, source.id, source.name, source.species,
          source.status, source.type, source.gender, source.origin_name, source.location_name
        );

        TRUNCATE TABLE `{{ var('project_name') }}.{{ var('dataset_bronze') }}.{{ var('table_characters_bronze') }}`;
    END;
  {% endset %}
  {% do run_query(sql) %}
{% endmacro %}