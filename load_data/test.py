# Event data simulating Cloud Storage event
# event = {
#     'name': 'departments.csv',
#     'table_id': 'departments'
# }
# event = {
#     'name': 'jobs.csv',
#     'table_id': 'jobs'
# }

event = {
    'name': 'hired_employees.csv',
    'table_id': 'hired_employees'
}
context = {}



# Importa la función desde tu script
from loader import csv_to_bigquery

# Llama a la función con los datos del evento simulados
csv_to_bigquery(event, context)
