from google.cloud import bigquery
from google.cloud import storage
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

def find_latest_backup(bucket_name, prefix):
    """
    Finds the latest backup file in the specified GCS bucket and prefix.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    latest_blob = None
    latest_date = datetime.min

    for blob in blobs:
        blob_date = blob.time_created
        if blob_date > latest_date:
            latest_blob = blob.name
            latest_date = blob_date

    return latest_blob if latest_blob else None

def restore_table_from_avro(request):
    """
    Automatically restores a BigQuery table from the latest AVRO file located in a GCS bucket.
    """
    client = bigquery.Client()
    backups_path = get_secret("bq_backups_file_path").replace('gs://', '')
    dataset_id = get_secret("mig-dataset-id")
    project_id = __project_id__

    payload = request.get_json()
    table_id = payload["table_id"]
    
    # Split to get bucket name and base path
    parts = backups_path.split('/', 1)
    bucket_name = parts[0]
    base_path = parts[1] if len(parts) > 1 else ''

    prefix = f"{base_path}{table_id}/"
    backup_file_name = find_latest_backup(bucket_name, prefix)

    if not backup_file_name:
        logger.error(f"No backup found for {table_id}")
        return f"No backup found for {table_id}", 404

    source_uri = f"gs://{bucket_name}/{backup_file_name}"
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    table_ref = dataset_ref.table(table_id)
    job_config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.AVRO)

    # Starting the job to restore the table
    load_job = client.load_table_from_uri(
        source_uri, table_ref, job_config=job_config
    )
    load_job.result()  # Wait for the job to complete

    logger.info(f"Imported {table_id} from {source_uri}")
    return f"Imported {table_id} from {source_uri}", 200
