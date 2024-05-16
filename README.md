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


## Creating the BigQuery tables
```SQL
CREATE TABLE IF NOT EXISTS ODS_ORG_MIGRATION.hired_employees (
  id              INT64,
  name            STRING,
  datetime        STRING,
  department_id   INT64,
  job_id          INT64
)
OPTIONS(labels=[('process', 'migration')]);


CREATE TABLE IF NOT EXISTS ODS_ORG_MIGRATION.departments (
  id              INT64,
  department      STRING
)
OPTIONS(labels=[('process', 'migration')]);


CREATE TABLE IF NOT EXISTS ODS_ORG_MIGRATION.jobs (
  id              INT64,
  job            STRING
)
OPTIONS(labels=[('process', 'migration')]);
``` 


