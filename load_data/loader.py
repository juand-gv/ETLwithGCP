from google.cloud import bigquery
from google.cloud import storage
from google.cloud import secretmanager

import os

__project_id__ = os.getenv('GCP_PROJECT_ID')


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
    ]
}

def get_secret(secret_id):
    """Recupera un secreto del Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{__project_id__}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')


def csv_to_bigquery(event, context):
    client = bigquery.Client()
    gcs_client = storage.Client()

    # Obtener secretos de Google Secret Manager
    file_path = get_secret('source-file-path')
    dataset_id = get_secret('mig-dataset-id')
    project_id = __project_id__

    table_id = event["table_id"]

    source_blob_name = event['name'] 
    uri = f"{file_path}{source_blob_name}"


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

    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.CSV
    job_config.field_delimiter = ";"
    job_config.write_disposition = "WRITE_TRUNCATE"
    job_config.skip_leading_rows = 0  # Ajusta según tu CSV
    job_config.autodetect = False

    load_job = client.load_table_from_uri(
        uri,
        table_ref,
        job_config=job_config
    )

    load_job.result()  # Espera a que la carga se complete.

    print(f"Job finished. Loaded {load_job.output_rows} rows.")
