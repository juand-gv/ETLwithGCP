from google.cloud import bigquery
from google.cloud import secretmanager
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any
from flask import escape, jsonify, Flask, request

import os
import logging


# Retrieve the Google Cloud project ID from environment variables
__project_id__ = os.getenv("GCP_PROJECT_ID")



app = Flask(__name__)

class Department(BaseModel):
    """Data model for department entities."""
    id: int
    department_name: str

class Job(BaseModel):
    """Data model for job entities."""
    id: int
    job_name: str

class Employee(BaseModel):
    """Data model for employee entities, including validation for datetime format."""
    id: int
    name: str
    datetime: str
    department_id: int
    job_id: int


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

def process_records(data: List[Dict], model: BaseModel, dataset_id: str, table_name: str) -> None:
    """
    Validates and inserts a list of records into a specified BigQuery table.

    Args:
        data (List[Dict]): The list of data to be inserted, represented as dictionaries.
        model (BaseModel): Pydantic model to validate the data against.
        dataset_id (str): The dataset ID in BigQuery.
        table_name (str): The table name in the dataset where data will be inserted.
    
    Raises:
        RuntimeError: If the insertion process encounters any errors.
    """
    client = bigquery.Client()
    table_id = f"{dataset_id}.{table_name}"
    errors = []

    records = [model(**record).dict() for record in data]
    errors = client.insert_rows_json(table_id, records)

    if errors:
        raise RuntimeError(f"Failed to insert records into {table_id}: {errors}")

@app.route('/', methods=['POST'])
def insert_data():
    """
    Endpoint to receive and insert data into BigQuery.

    Expects a JSON payload with keys corresponding to tables: 'departments', 'jobs', 'employees'.

    Returns:
        JSON response indicating the status of the operations.

    Status Codes:
        200: Success
        400: Bad request due to invalid JSON or data validation failure.
        500: Internal server error from BigQuery operations or other exceptions.
    """
    request_data = request.get_json()

    if not request_data:
        return jsonify({'error': 'Invalid or missing JSON'}), 400

    dataset_id = get_secret("mig-dataset-id")

    try:
        if 'departments' in request_data:
            process_records(request_data['departments'], Department, dataset_id, 'departments')

        if 'jobs' in request_data:
            process_records(request_data['jobs'], Job, dataset_id, 'jobs')

        if 'employees' in request_data:
            process_records(request_data['employees'], Employee, dataset_id, 'employees')

        return jsonify({'message': 'Data inserted successfully'}), 200

    except ValidationError as e:
        return jsonify({'error': 'Data validation failed', 'details': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to insert data', 'details': str(e)}), 500

