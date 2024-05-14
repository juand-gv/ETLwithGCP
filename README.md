# ETLwithGCP

# Overview

![asdasd](docs/GlobantCh1.svg)




## Pre-requisites

This project runs in Docker + Docker Compose


## Installation

Use the docker-compose cli to install the image and run the container.

First Installation:
```bash
docker compose up --build
```

With the container already created:
```bash
docker compose up
```


## Example to run the Spark job

```bash
spark-submit --jars $(echo /opt/spark/extra_jars/*.jar | tr ' ' ',') \
    --conf spark.hadoop.fs.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem \
    --conf spark.hadoop.fs.AbstractFileSystem.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS \
    --conf spark.hadoop.fs.gs.project.id=data-intelligence-prepro \
    --conf spark.hadoop.google.cloud.auth.service.account.enable=true \
    --conf spark.hadoop.google.cloud.auth.service.account.json.keyfile=/opt/gcloud-service-key.json \
    --conf spark.executor.memory=4g \
    --conf spark.driver.memory=4g \
    dataproc/jobs/batch_processor.py
```