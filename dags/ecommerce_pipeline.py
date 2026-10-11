from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Configuration de base du pipeline
default_args = {
    'owner': 'othmane',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Définition du DAG (le nom affiché dans l'interface)
with DAG(
    'pfe_ecommerce_medallion',
    default_args=default_args,
    description='Pipeline PFE : Silver -> Gold -> Tests',
    schedule_interval='@daily', # Exécution quotidienne
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['pfe', 'ecommerce'],
) as dag:

    # Tâche 1 : Lancer le nettoyage Silver (Pandas + PostgreSQL)
    t1_silver = BashOperator(
        task_id='traitement_silver',
        bash_command='python /opt/airflow/scripts/silver_layer.py'
    )

    # Tâche 2 : Lancer la modélisation Gold (dbt run)
    t2_gold = BashOperator(
        task_id='modelisation_gold',
        bash_command='cd /opt/airflow/dbt_ecommerce && dbt run --profiles-dir .'
    )

    # Tâche 3 : Lancer les tests de qualité (dbt test)
    t3_tests = BashOperator(
        task_id='tests_qualite_donnees',
        bash_command='cd /opt/airflow/dbt_ecommerce && dbt test --profiles-dir .'
    )

    # L'ORDRE D'EXÉCUTION : Airflow ne lancera l'étape suivante que si la précédente réussit
    t1_silver >> t2_gold >> t3_tests