from google.cloud import bigquery
from google.cloud import secretmanager

import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Retrieve the Google Cloud project ID from environment variables
__project_id__ = os.getenv("GCP_PROJECT_ID")

def get_secret(secret_id):
    """
    Retrieve a secret from Google Cloud Secret Manager.

    Args:
        secret_id (str): Identifier for the secret to retrieve.

    Returns:
        str: The secret value.
    
    """

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{__project_id__}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")


def export_table_to_avro(request, context=None):
    """
    Exports a specified BigQuery table to a Google Cloud Storage bucket in AVRO format.
    
    This function is designed to be triggered by an HTTP request. The request payload must include
    a 'table_id' that specifies which table to export. The function constructs a destination URI
    for the AVRO files using the current date to organize exports by date.

    Args:
        request: The HTTP request object that triggered the function, containing 'table_id'.
        context: The context parameter is not used in this function but is included for compatibility
                 with Cloud Functions.

    Returns:
        str: A message indicating the export operation's success and the URI of the exported files.


    Usage example:
    {
        "table_id": "hired_employees"
    }
    """
    
    client = bigquery.Client()
    
    # Retrieve configurations from Google Cloud Secret Manager
    backups_path = get_secret("bq_backups_file_path")
    dataset_id = get_secret("mig-dataset-id")
    project_id = __project_id__

    payload = request.get_json()
    
    table_id = payload["table_id"]

    # Format the current date in YYYYMMDD format
    today = datetime.now().strftime("%Y%m%d")

    # Include the date in the file name
    destination_uri = f"{backups_path}{table_id}/{table_id}_{today}_*.avro"

    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    table_ref = dataset_ref.table(table_id)

    # Configure the extract job to export data in AVRO format
    extract_job = client.extract_table(
        table_ref,
        destination_uri,
        location='us-central1',
        job_config=bigquery.job.ExtractJobConfig(destination_format=bigquery.DestinationFormat.AVRO)
    )
    
    # Execute the job and wait for it to complete
    extract_job.result()  
    
    
    logger.info(f"Exported {table_id} to {destination_uri}")
    return f"Exported {table_id} to {destination_uri}"
