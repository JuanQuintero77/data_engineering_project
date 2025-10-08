from airflow.models import BaseOperator
from shared.services.api_services import APIServices
import json


class FetchPaginatedApiDataOperator(BaseOperator):
    '''
    Purpose: Fetch data from a paginated API and store the aggregated result as a JSON file in GCS.
    Parameters: url (str): API endpoint.
    method (str): HTTP method.
    project_id (str): GCP project ID.
    bucket (str): GCS bucket name.
    folder (str): Folder path within the bucket.
    headers (dict, optional): HTTP headers.
    api_params (dict or str, optional): Initial query parameters.
    data (dict, optional): Form-encoded data.
    json_body (dict, optional): JSON body for the request.
    timeout (int): Timeout for requests.
    verify_ssl (bool): Whether to verify SSL.
    raise_for_status (bool): Raise error on failed requests.
    compress (bool): Whether to GZIP the final JSON (default is True).
    file_name (str, optional): File name (no extension).
    extra_config (dict, optional): Additional configuration for pagination, like page size, keys for next page tokens, etc.
    Returns:(str): GCS path where the full JSON file was saved.
    '''
    template_fields = ('headers', 'api_params', 'file_name')

    def __init__(self,*,
                url: str,
                method: str,
                project_id: str,
                bucket: str,
                folder: str,
                headers: dict = None,
                api_params: dict = None,
                data: dict = None,
                json_body: dict = None,
                timeout: int = 60,
                verify_ssl: bool = True,
                raise_for_status: bool = True,
                compress: bool = True,
                file_name: str = None,
                extra_config: dict = None,
                **kwargs):
        super().__init__(**kwargs)
        self.api_service = APIServices(
            url=url,
            method=method,
            headers=headers,
            params=api_params,
            data=data,
            body=json_body,
            timeout=timeout,
            verify=verify_ssl,
            project_id=project_id,
            extra_config=extra_config,
            file_name=file_name
        )
        self.url = url
        self.method = method
        self.project_id = project_id
        self.bucket = bucket
        self.folder = folder
        self.headers = headers
        self.api_params = api_params
        self.data = data
        self.json_body = json_body
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.raise_for_status = raise_for_status
        self.compress = compress
        self.file_name = file_name
        self.extra_config = extra_config

    def execute(self, context):
        self.log.info("Fetching data in json format from API")
        if isinstance(self.api_params, str):
            try:
                self.api_params = json.loads(self.api_params)
                self.log.info(f"Parsed JSON params: {self.api_params}")
            except json.JSONDecodeError as e:
                self.log.info("Failed to parse params as JSON.")
                raise e
        
        try:
            response = self.api_service.fetch_data_from_api_with_pages_save_json_to_gcs(
                url = self.url,
                method = self.method,
                project_id = self.project_id,
                bucket = self.bucket,
                folder = self.folder,
                headers = self.headers,
                params = self.api_params,
                data = self.data,
                json_body = self.json_body,
                timeout = self.timeout,
                verify_ssl = self.verify_ssl,
                raise_for_status = self.raise_for_status,
                compress = self.compress,
                file_name = self.file_name,
                extra_config = self.extra_config)
            self.log.info(f"Response: {response}")
            self.log.info(f"HEADERS RENDERED: {self.headers}")
            return response
        except Exception as e:
            self.log.info(f"There was an error while fetching data from the API -> {e}")
            raise e