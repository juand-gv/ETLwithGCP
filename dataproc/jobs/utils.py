from google.cloud import secretmanager
from google.cloud import storage
from google.cloud import bigquery




# Initialize Google Secret Manager client
secret_client = secretmanager.SecretManagerServiceClient()
storage_client = storage.Client()
bigquery_client = bigquery.Client()


def fetch_secret(secret_name):
    # Fetches secret data from Google Secret Manager.
    secret_response = secret_client.access_secret_version(name=secret_name)
    return secret_response.payload.data.decode('utf-8')



