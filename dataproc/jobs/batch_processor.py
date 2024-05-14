from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, TimestampType

from utils import fetch_secret

# Inicializa la sesión de Spark
spark = SparkSession.builder \
    .appName("CSV to BigQuery Loader") \
    .getOrCreate()

# Define las rutas de los archivos CSV en Google Cloud Storage
gcs_bucket_path = fetch_secret("projects/492131365367/secrets/source-file-path/versions/1")
hired_employees_file = f"{gcs_bucket_path}/hired_employees.csv"
departments_file = f"{gcs_bucket_path}/departments.csv"
jobs_file = f"{gcs_bucket_path}/jobs.csv"



# Esquema para hired_employees.csv
schema_hired_employees = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True),
    StructField("datetime", TimestampType(), True),
    StructField("department_id", IntegerType(), True),
    StructField("job_id", IntegerType(), True)
])

# Esquema para departments.csv
schema_departments = StructType([
    StructField("id", IntegerType(), True),
    StructField("department", StringType(), True)
])

# Esquema para jobs.csv
schema_jobs = StructType([
    StructField("id", IntegerType(), True),
    StructField("job", StringType(), True)
])


# Cargar los archivos CSV utilizando los esquemas definidos
hired_employees_df = spark.read.csv(hired_employees_file, header=True, schema=schema_hired_employees)
departments_df = spark.read.csv(departments_file, header=True, schema=schema_departments)
jobs_df = spark.read.csv(jobs_file, header=True, schema=schema_jobs)

# Transformación de datos (si es necesario)
# Por ejemplo, convertir el formato de fecha en 'hired_employees_df'
hired_employees_df = hired_employees_df.withColumn("datetime", col("datetime").cast("timestamp"))

# Definir el nombre del proyecto y el dataset de BigQuery
project_id = fetch_secret("projects/492131365367/secrets/project-id/versions/1")
dataset_id = fetch_secret("projects/492131365367/secrets/mig-dataset-id/versions/1")
hired_employees_table = f"{project_id}:{dataset_id}.hired_employees"
departments_table = f"{project_id}:{dataset_id}.departments"
jobs_table = f"{project_id}:{dataset_id}.jobs"
temp_bucket = fetch_secret("projects/492131365367/secrets/temp-bucket/versions/1")

# Escribir DataFrames a BigQuery
hired_employees_df.write.format('bigquery') \
    .option("table", hired_employees_table) \
    .option("temporaryGcsBucket",temp_bucket) \
    .mode("append") \
    .save()

departments_df.write.format('bigquery') \
    .option("table", departments_table) \
    .option("temporaryGcsBucket",temp_bucket) \
    .mode("append") \
    .save()

jobs_df.write.format('bigquery') \
    .option("table", jobs_table) \
    .option("temporaryGcsBucket",temp_bucket) \
    .mode("append") \
    .save()

# Finalizar la sesión de Spark
spark.stop()
