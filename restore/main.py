from google.cloud import bigquery
from google.cloud import storage
from google.cloud import secretmanager
import pytz  # Se necesita para manejar la zona horaria

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
    logger.info(f"Listing blobs in bucket {bucket_name} with prefix {prefix}")
    blobs = bucket.list_blobs(prefix=prefix)
    latest_blob = None
    latest_date = datetime.min.replace(tzinfo=pytz.UTC)

    for blob in blobs:
        logger.info(f"Found blob: {blob.name} with date: {blob.time_created}")
        blob_date = blob.time_created
        if blob_date > latest_date:
            latest_blob = blob.name
            latest_date = blob_date

    return latest_blob if latest_blob else None

def restore_table_from_avro(request):
    client = bigquery.Client()
    backups_path = get_secret("bq_backups_file_path").strip('/')
    dataset_id = get_secret("mig-dataset-id")
    project_id = __project_id__

    payload = request.get_json()
    
    table_id = payload["table_id"]

    # Assuming the backups_path does not include 'gs://' prefix here
    bucket_name = backups_path.split('/')[2]
    path = backups_path.split('/')[3]
    prefix = f"{path}/{table_id}/"

    logger.info(f"Looking for latest backup in {bucket_name}/{prefix}")
    backup_file_name = find_latest_backup(bucket_name, prefix)

    if not backup_file_name:
        error_msg = f"No backup found for {table_id}"
        logger.error(error_msg)
        return error_msg, 404

    source_uri = f"gs://{bucket_name}/{backup_file_name}"
    logger.info(f"Restoring from {source_uri}")
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    table_ref = dataset_ref.table(table_id)
    job_config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.AVRO)

    load_job = client.load_table_from_uri(
        source_uri, table_ref, job_config=job_config
    )
    load_job.result()  # Wait for the job to complete

    success_msg = f"Imported {table_id} from {source_uri}"
    logger.info(success_msg)
    return success_msg, 200

