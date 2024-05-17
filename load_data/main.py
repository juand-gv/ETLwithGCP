from google.cloud import bigquery
from google.cloud import storage
from google.cloud import secretmanager

import os
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


# Retrieve the Google Cloud project ID from environment variables
__project_id__ = os.getenv("GCP_PROJECT_ID")


# Define schemas for each table to be loaded into BigQuery
__schemas__ = {
    "hired_employees": [
        bigquery.SchemaField("id", "INTEGER"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("datetime", "STRING"),
        bigquery.SchemaField("department_id", "INTEGER"),
        bigquery.SchemaField("job_id", "INTEGER"),
    ],
    "departments": [
        bigquery.SchemaField("id", "INTEGER"),
        bigquery.SchemaField("department", "STRING"),
    ],
    "jobs": [
        bigquery.SchemaField("id", "INTEGER"),
        bigquery.SchemaField("job", "STRING"),
    ],
}


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


def csv_to_bigquery(request, context=None):
    """
    Cloud Function to load CSV files from Google Cloud Storage into BigQuery.

    Args:
        request ( Flask request object,): The event payload.
        context (google.cloud.functions.Context): Metadata for the event.

    Usage example:
    {
        "request": {
            "name": "file_name.csv",
            "table_id": "table_name"
        }
    } 
    """

    client = bigquery.Client()
    gcs_client = storage.Client()

    # Retrieve configurations from Google Cloud Secret Manager
    file_path = get_secret("source-file-path")
    dataset_id = get_secret("mig-dataset-id")
    project_id = __project_id__

    table_id = request.args.get("table_id")

    # Determine the table based on the file name in the event
    source_blob_name = request.args.get("name")
    uri = f"{file_path}{source_blob_name}"


    # Select schema based on the source file name
    if "hired_employees" in source_blob_name:
        table_id = "hired_employees"
        schema = __schemas__["hired_employees"]
    elif "departments" in source_blob_name:
        table_id = "departments"
        schema = __schemas__["departments"]
    elif "jobs" in source_blob_name:
        table_id = "jobs"
        schema = __schemas__["jobs"]
    else:
        raise ValueError("Unknown file type")

    dataset_ref = client.dataset(dataset_id, project=project_id)
    table_ref = dataset_ref.table(table_id)

    # Configure the BigQuery load job
    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.CSV
    job_config.field_delimiter = ";"
    job_config.write_disposition = "WRITE_TRUNCATE"
    job_config.skip_leading_rows = 0
    job_config.autodetect = False

    load_job = client.load_table_from_uri(uri, table_ref, job_config=job_config)

        
    # Wait for the job to complete
    load_job.result() 

    logger.info(f"Job finished. Loaded {load_job.output_rows} rows.")

    return True
