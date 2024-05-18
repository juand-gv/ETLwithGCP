CREATE OR REPLACE VIEW ODS_ORG_MIGRATION.employees_hired_per_quarter AS
SELECT
  d.department,
  j.job,
  COUNTIF(EXTRACT(QUARTER FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', e.datetime)) = 1) AS Q1,
  COUNTIF(EXTRACT(QUARTER FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', e.datetime)) = 2) AS Q2,
  COUNTIF(EXTRACT(QUARTER FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', e.datetime)) = 3) AS Q3,
  COUNTIF(EXTRACT(QUARTER FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', e.datetime)) = 4) AS Q4
FROM
  ODS_ORG_MIGRATION.hired_employees e
JOIN
  ODS_ORG_MIGRATION.departments d ON e.department_id = d.id
JOIN
  ODS_ORG_MIGRATION.jobs j ON e.job_id = j.id
WHERE
  EXTRACT(YEAR FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', e.datetime)) = 2021
GROUP BY
  d.department,
  j.job
ORDER BY
  d.department,
  j.job;


CREATE OR REPLACE VIEW ODS_ORG_MIGRATION.departments_above_average_hires AS
SELECT
  d.id,
  d.department,
  COUNT(e.id) AS hired
FROM
  ODS_ORG_MIGRATION.hired_employees e
JOIN
  ODS_ORG_MIGRATION.departments d ON e.department_id = d.id
WHERE
  EXTRACT(YEAR FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', e.datetime)) = 2021
GROUP BY
  d.id,
  d.department
HAVING
  COUNT(e.id) > (
    SELECT
      AVG(hired_count)
    FROM (
      SELECT
        COUNT(id) AS hired_count
      FROM
        ODS_ORG_MIGRATION.hired_employees
      WHERE
        EXTRACT(YEAR FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', datetime)) = 2021
      GROUP BY
        department_id
    )
  )
ORDER BY
  hired DESC;

