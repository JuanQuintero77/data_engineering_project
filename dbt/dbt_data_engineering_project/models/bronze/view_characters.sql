SELECT
current_date() AS ingestion_date,
id,
name,
species,
status,
type,
gender,
origin_name,
location_name
FROM `data-engineering-dev-464423.BRONZE.rick_and_morty_characters`
