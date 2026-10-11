# On part de l'image officielle d'Airflow
FROM apache/airflow:2.7.3

# On copie notre fichier requirements.txt dans le conteneur
COPY requirements.txt /

# On installe Pandas, dbt, MinIO, etc. à l'intérieur d'Airflow
RUN pip install --no-cache-dir -r /requirements.txt