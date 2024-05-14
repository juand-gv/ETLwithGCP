# Usamos una imagen base que ya contiene Python y OpenJDK
FROM openjdk:17-slim-buster

# Instalación de Python y utilidades necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-pip python3-dev \
    python3-pip \
    python3-dev \
    python3-setuptools \
    wget \
    tar \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configuramos variables de entorno para Java y Spark
ENV JAVA_HOME="/usr/local/openjdk-17"
ENV SPARK_HOME="/opt/spark"
ENV PATH="$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin"
ENV PYTHONPATH="$SPARK_HOME/python:$PYTHONPATH"
ENV PYSPARK_PYTHON=python3

# Descarga y configuración de Spark
RUN mkdir -p /opt/spark/ && \
    wget -qO- https://archive.apache.org/dist/spark/spark-3.3.0/spark-3.3.0-bin-hadoop3-scala2.13.tgz | tar -xz -C /opt/spark/ --strip-components=1

# Descarga y configuración de los JARs necesarios para BigQuery y GCS
RUN mkdir -p /opt/spark/extra_jars/ && \
    wget -O /opt/spark/extra_jars/spark-3.3-bigquery-0.32.1.jar https://storage.googleapis.com/spark-lib/bigquery/spark-3.3-bigquery-0.32.1.jar && \
    wget -O /opt/spark/extra_jars/gcs-connector-hadoop3-latest.jar https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-hadoop3-latest.jar

# Copia de configuraciones personalizadas de Spark
COPY log4j.properties /opt/spark/conf/

# Configuración de las credenciales de GCP
COPY env/gcloud-service-key.json /opt/
ENV GOOGLE_APPLICATION_CREDENTIALS="/opt/gcloud-service-key.json"

# Instalación de librerías de Python necesarias
COPY requirements.txt /opt/
RUN pip3 install --no-cache-dir --default-timeout=1000 -r /opt/requirements.txt

# Alternativamente, puedes copiar un archivo .whl o .tar.gz localmente
# COPY pyspark-3.4.1.tar.gz /opt/
# RUN pip install --no-cache-dir /opt/pyspark-3.4.1.tar.gz

# Directorio de trabajo
WORKDIR /opt/app

# Copia del código de aplicación Python
COPY . /opt/app/
