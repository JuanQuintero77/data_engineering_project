import functions_framework
import pandas as pd
import pyarrow as pa
import json
from google.cloud import storage

@functions_framework.http
def process_characters(request):
    """
    HTTP Cloud Function:
    Espera un JSON con:
    {
      "input_bucket": "bucket-origen",
      "input_file": "rick_and_morty_characters.json",
      "output_bucket": "bucket-destino",
      "output_file": "rick_and_morty_characters_processed.parquet"
    }
    """
    request_json = request.get_json(silent=True)

    input_bucket = request_json.get("input_bucket")
    input_file = request_json.get("input_file")
    output_bucket = request_json.get("output_bucket")
    output_file = request_json.get("output_file")

    client = storage.Client()

    # Descargar JSON desde GCS
    bucket_in = client.bucket(input_bucket)
    blob_in = bucket_in.blob(input_file)
    raw_data = blob_in.download_as_text(encoding="utf-8")
    data = json.loads(raw_data)

    # Procesar con pandas
    df = pd.json_normalize(data)
    df = df[['id', 'name', 'species', 'status', 'type', 'gender', 'origin.name', 'location.name', 'episode']]
    df.rename(columns={'origin.name': 'origin_name', 'location.name': 'location_name'}, inplace=True)
    df['episode_count'] = df['episode'].apply(len)
    df.drop(columns=['episode'], inplace=True)
    df = df.astype(str)

    # Guardar como parquet en GCS
    bucket_out = client.bucket(output_bucket)
    blob_out = bucket_out.blob(output_file)

    parquet_bytes = df.to_parquet(engine="pyarrow", index=False)
    blob_out.upload_from_string(parquet_bytes, content_type="application/octet-stream")

    return {"rows": len(df), "message": "Procesamiento exitoso"}
