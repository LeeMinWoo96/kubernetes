from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago


default_args = {
    'owner': 'airflow',
    'start_date': days_ago(2),
}

dag = DAG(
    dag_id = 'kubernetes_sample2',
    schedule_interval='0 0 * * *',
    default_args=default_args,
    dagrun_timeout=timedelta(minutes=60),



run_this_last = DummyOperator(
    task_id='run_this_last',
    dag=dag,
)

run_this = BashOperator(
    task_id='run_after_loop',
    bash_command='ls',
    dag=dag,
)
run_this_last >> run_this

if __name__ == "__main__":
    dag.cli()
