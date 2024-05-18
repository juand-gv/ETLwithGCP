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
        "event": {
            "file_name": "file_name.csv",
            "table_id": "table_name"
        }
    } 
    """

    client = bigquery.Client()
    # gcs_client = storage.Client()

    # Retrieve configurations from Google Cloud Secret Manager
    file_path = get_secret("source-file-path")
    dataset_id = get_secret("mig-dataset-id")
    project_id = __project_id__

    payload = request.get_json()

    event = payload["event"]
    file_name = event["file_name"]
    table_id = event["table_id"]

    # Determine the table based on the file name in the event
    uri = f"{file_path}{file_name}"

    logger.info(f"Starting load job for {file_name} into {table_id}")


    # Select schema based on the source file name
    if "hired_employees" in file_name:
        schema = __schemas__["hired_employees"]
    elif "departments" in file_name:
        schema = __schemas__["departments"]
    elif "jobs" in file_name:
        schema = __schemas__["jobs"]
    else:
        logger.error(f"Unknown file type for {file_name}")
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
    job_config.schema = schema



    try:
        load_job = client.load_table_from_uri(uri, table_ref, job_config=job_config)
        load_job.result()
        logger.info(f"Job finished. Loaded {load_job.output_rows} rows into {table_id}.")

        return f"Job finished. Loaded {load_job.output_rows} rows into table: {table_id}. In truncate mode."

    except Exception as e:
        logger.error(f"Failed to load data into {table_id}: {str(e)}")
        raise Exception("Failed to load data into {table_id}: {str(e)}")
