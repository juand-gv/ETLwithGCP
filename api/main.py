from google.cloud import bigquery
from google.cloud import secretmanager
from pydantic import BaseModel, ValidationError, Field, field_validator
from typing import List, Dict, Any

from datetime import datetime
import os
import logging


# Retrieve the Google Cloud project ID from environment variables
__project_id__ = os.getenv("GCP_PROJECT_ID")


class Department(BaseModel):
    """Data model for department entities."""
    id: int
    department: str

class Job(BaseModel):
    """Data model for job entities."""
    id: int
    job: str

class Employee(BaseModel):
    """Data model for employee entities, including validation for datetime format."""
    id: int
    name: str
    datetime: str
    department_id: int
    job_id: int

    @field_validator('datetime')
    def datetime_format(cls, v):
        """
        Validates datetime in ISO 8601 format.

        Parameters:
            v (str): The datetime string to validate.

        Returns:
            str: The validated datetime string.

        Raises:
            ValueError: If the datetime is not in ISO 8601 format.
        """
        try:
            # Intenta parsear la fecha en formato ISO 8601
            # datetime.fromisoformat asume 'Z' como '+00:00' cuando se usa
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("datetime must be in ISO 8601 format")
        return v


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
    valid_records = []
    errors = []

    for record in data:
        try:
            validated_record = model(**record)
            valid_records.append(validated_record.dict())
        except ValidationError as e:
            errors.append(f"Validation failed for record {record}: {str(e)}")
            logging.error(f"Validation failed for record {record}: {str(e)}")

    if valid_records:
        error_response = client.insert_rows_json(table_id, valid_records)
        if error_response:
            logging.error(f"Failed to insert records into {table_id}: {error_response}")
            errors.extend([str(err) for err in error_response])
    
    # Retrning errors for further processing
    return errors

def insert_data(request):
    """
    Endpoint to receive and insert data into BigQuery.

    Expects a JSON payload with keys corresponding to tables: 'departments', 'jobs', 'hired_employees'.

    Returns:
        JSON response indicating the status of the operations.

    Usage Example:    
    {
        "departments": [
            {
                "id": 666,
                "department": 6
            },
            {
                "id": 888,
                "department": "Gaming"
            }
        ],
        "jobs": [
            {
                "id": 666,
                "job": "Game Developer"
            },
            {
                "id": 222,
                "job": "Analyst"
            }
        ],
        "hired_employees": [
            {
                "id": 10101,
                "name": "John Doe",
                "datetime": "2021-11-07T02:48:42Z",
                "department_id": 1,
                "job_id": 1
            },
            {
                "id": 20202,
                "name": "Jane Doe",
                "datetime": "2021-12-07T02:48:42Z",
                "department_id": 2,
                "job_id": 2
            }
        ]
    }
    """
    request_data = request.get_json()


    if not request_data:
        return {'error': 'Invalid or missing JSON'}

    dataset_id = get_secret("mig-dataset-id")
    total_errors  = []



    for entity, model in [('departments', Department), ('jobs', Job), ('employees', Employee)]:
        if entity in request_data:
            errors = process_records(request_data[entity], model, dataset_id, entity)
            if errors:
                total_errors.extend(errors)


    if total_errors:
        # Return error response if there are any validation or insertion errors
        return {'error': 'Some records failed validation or insertion', 'details': total_errors}
    else:
        # Return success response if all records are processed without errors
        return {'message': 'Data inserted successfully'}

