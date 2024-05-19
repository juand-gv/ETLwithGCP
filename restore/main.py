from google.cloud import bigquery
from google.cloud import secretmanager

import os
import logging


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


def import_table_from_avro(request, context):
    client = bigquery.Client()


    # Retrieve configurations from Google Cloud Secret Manager
    backups_path = get_secret("bq_backups_file_path")
    dataset_id = get_secret("mig-dataset-id")
    project_id = __project_id__

    payload = request.get_json()

    table_id = payload["table_id"]
    backup_file_name = payload["backup_file_name"]

    source_uri = f"{backups_path}{table_id}/{backup_file_name}"

    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    table_ref = dataset_ref.table(table_id)

    job_config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.AVRO)
    load_job = client.load_table_from_uri(
        source_uri, table_ref, job_config=job_config
    )
    
    # Execute the job and wait for it to complete
    load_job.result()


    logger.info(f"Imported {table_id} from {source_uri}")
    return f"Imported {table_id} from {source_uri}"
