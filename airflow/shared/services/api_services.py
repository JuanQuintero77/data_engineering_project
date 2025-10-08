import requests
from google.cloud import storage as gcs
import json, time, logging, gzip
from io import BytesIO
from urllib.parse import urlparse
from google.cloud import storage


class APIServices:

    def __init__(self,
                url: str,
                method: str = 'GET', 
                params: str =None,
                data: str = None,
                headers: dict = None,
                body: dict = None,
                timeout: int = 30,
                verify: bool = True,
                project_id: str = None,
                extra_config: dict = None,
                file_name: str = None
                ):
        self.url = url
        self.method = method
        self.params = params
        self.data = data
        self.headers = headers
        self.body = body
        self.timeout = timeout
        self.verify = verify
        self.gcs_client = gcs.Client(project=project_id)
        self.extra_config = extra_config if extra_config else {}
        self.file_name = file_name if file_name else "data.json"
    
    def fetch_data(self):
        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                params=self.params,
                data=self.data,
                headers=self.headers,
                json=self.body,
                timeout=self.timeout,
                verify=self.verify
            )
            response.raise_for_status()  
            return response.json()  
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None
    
    def fetch_data_to_storage(self, bucket_name: str, file_path: str):
        data = self.fecth_data()
        if data:
            try:
                json_data = json.dumps(data)
                bucket = self.gcs_client.bucket(bucket_name)  
                blob = bucket.blob(file_path)            
                blob.upload_from_string(json_data, content_type='application/json')
                print(f"Data successfully stored in {bucket_name}/{file_path}")
            except Exception as e:
                print(f"An error occurred while storing data: {e}")            
        else:
            print("No data to store") 

   
    '''
    Purpose: Fetches paginated API data by following links to next pages and consolidates all results into a single JSON file uploaded to GCS.
    Supports gzip compression and custom pagination structure.
    Parameters: url, method, headers, params, data, json_body, timeout, verify_ssl, raise_for_status: Same as fetch_data_from_api.
    project_id (str): GCP project ID.
    bucket (str): GCS bucket name.
    folder (str): Target folder in the bucket.
    compress (bool): Whether to gzip the output file.
    file_name (str): Base name for the output file.
    extra_config (dict, optional): Pagination configuration: data_field: Key in response JSON where the data list is stored (e.g. 'calls').
    pagination_field: Key where pagination metadata is stored (e.g. 'meta').
    next_page_key: Key inside the pagination field that contains the next page URL.
    delay_between_pages: Seconds to wait between requests (default: 1).
    Returns: str: GCS path of the final JSON file.
    '''
    def fetch_data_from_api_with_pages_save_json_to_gcs(self,
                                             url,
                                             method,
                                             headers,
                                             params,
                                             data,
                                             json_body,
                                             timeout,
                                             verify_ssl,
                                             raise_for_status,
                                             project_id,
                                             bucket,
                                             folder,
                                             compress,
                                             file_name,
                                             extra_config=None):
        extra_config = extra_config or {}
        data_field = extra_config.get("data_field")           # example: 'calls'
        pagination_field = extra_config.get("pagination_field")  # example: 'meta'
        next_page_key = extra_config.get("next_page_key")     # example: 'next_page_link'
        base_url = extra_config.get('base_url')
        delay_between_pages = extra_config.get("delay_between_pages", 1)  # seconds between requests

        all_results = []
        current_url = url
        current_params = params or {}
        page_count = 1

        while True:
            logging.info(f"Getting info from page {page_count} url: {current_url}")
            response = requests.request(
                method=method,
                url=current_url,
                headers=headers,
                params=current_params,
                data=data,
                json=json_body,
                timeout=timeout,
                verify=verify_ssl
            )

            if raise_for_status:
                response.raise_for_status()

            payload = response.json()

            if data_field:
                results = payload.get(data_field, [])
            else:
                results = payload if isinstance(payload, list) else []

            if isinstance(results, list):
                all_results.extend(results)
            else:
                all_results = payload
                break
            
            #logging.info(f"Parámetros dados: {params}")
            logging.info(f"Page {page_count} has {len(results)} results.")

            # Control de paginación
            next_link = None
            if pagination_field and next_page_key:
                next_link = payload.get(pagination_field, {}).get(next_page_key)
            elif next_page_key:
                next_link = payload.get(next_page_key)

            if next_link:
                base_url = extra_config.get("base_url")
                if base_url and next_link.startswith("/"):
                    parsed_base = urlparse(base_url)
                    base = f"{parsed_base.scheme}://{parsed_base.netloc}"
                    next_link = base + next_link

                current_url = next_link
                current_params = {}
                time.sleep(delay_between_pages)
                page_count += 1
                continue

            break  

        content = json.dumps(all_results, indent=4, ensure_ascii=False)
        if folder and folder.strip():
           full_path = f"{folder.rstrip().rstrip('/')}/{file_name}.json"
        else:
            full_path = f"{file_name}"
            
        if compress:
            full_path += ".gz"

        client = storage.Client(project=project_id)
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(full_path)

        if compress:
            buf = BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="w") as gz_file:
                gz_file.write(content.encode("utf-8"))
            buf.seek(0)
            blob.upload_from_file(buf, content_type="application/gzip")
        else:
            blob.upload_from_string(content, content_type="application/json")
            
        return f"gs://{bucket}/{full_path}"

        

   