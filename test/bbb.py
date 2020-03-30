from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2020,3,29),
    }

dag = DAG(
    dag_id = 'kubernetes_sample2',
    schedule_interval='0 0 * * *',
    default_args=default_args,
    dagrun_timeout=timedelta(minutes=60),
    )


start = DummyOperator(task_id='run_this_first',
                      dag=dag,
                      )

run_this = BashOperator(
    task_id='run_after_loop',
    bash_command='echo 1',
    dag=dag,
)

start >> run_this

if __name__ == "__main__":
    dag.cli()
