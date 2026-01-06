"""
Sample Data Mesh DAG - Demonstrates data pipeline orchestration
This DAG simulates a data product pipeline in a Data Mesh architecture
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'data-mesh-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_customer_data(**context):
    """Simulate extracting customer data from source"""
    print("Extracting customer data from domain_customers...")
    # In a real scenario, this would connect to MariaDB
    return {"customers_count": 100, "extraction_time": str(datetime.now())}

def transform_customer_data(**context):
    """Simulate transforming customer data"""
    ti = context['ti']
    extracted_data = ti.xcom_pull(task_ids='extract_customers')
    print(f"Transforming {extracted_data['customers_count']} customer records...")
    return {"transformed_count": extracted_data['customers_count'], "status": "success"}

def load_to_data_product(**context):
    """Simulate loading data to a data product"""
    ti = context['ti']
    transformed_data = ti.xcom_pull(task_ids='transform_customers')
    print(f"Loading {transformed_data['transformed_count']} records to customer data product...")
    return {"loaded": True, "timestamp": str(datetime.now())}

def publish_metadata(**context):
    """Simulate publishing metadata to OpenMetadata"""
    print("Publishing data product metadata to OpenMetadata catalog...")
    # In a real scenario, this would call OpenMetadata API
    return {"metadata_published": True}

with DAG(
    'sample_data_mesh_pipeline',
    default_args=default_args,
    description='Sample Data Mesh pipeline demonstrating data product creation',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    catchup=False,
    tags=['data-mesh', 'sample', 'customer-domain'],
) as dag:

    # Task 1: Extract data from source
    extract_customers = PythonOperator(
        task_id='extract_customers',
        python_callable=extract_customer_data,
    )

    # Task 2: Transform data
    transform_customers = PythonOperator(
        task_id='transform_customers',
        python_callable=transform_customer_data,
    )

    # Task 3: Load to data product
    load_data_product = PythonOperator(
        task_id='load_data_product',
        python_callable=load_to_data_product,
    )

    # Task 4: Publish metadata
    publish_to_catalog = PythonOperator(
        task_id='publish_to_catalog',
        python_callable=publish_metadata,
    )

    # Task 5: Validate data quality
    validate_quality = BashOperator(
        task_id='validate_data_quality',
        bash_command='echo "Running data quality checks..." && sleep 2 && echo "Quality checks passed!"',
    )

    # Define task dependencies
    extract_customers >> transform_customers >> load_data_product >> [publish_to_catalog, validate_quality]

