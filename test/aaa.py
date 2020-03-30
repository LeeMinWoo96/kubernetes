from airflow import DAG
from datetime import datetime, timedelta
# from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator


default_args = {
    'owner': 'airflow',
    'depends_on_past': True,
    'start_date': datetime(2020,3,29),
    'wait_for_downstream' : True,
    'schedule_interval': '@once'
    }

dag = DAG(
    'kubernetes_sample', default_args=default_args , catchup = True,)


start = DummyOperator(task_id='run_this_first', dag=dag)

run_this = BashOperator(
    task_id='run_after_loop',
    bash_command='echo 1',
    dag=dag,
)

start >> run_this

#passing = KubernetesPodOperator(namespace='default',
#                          image="Python:3.6",
#                          cmds=["Python","-c"],
#                          arguments=["print('hello world')"],
#                          labels={"foo": "bar"},
#                          name="passing-test",
#                          task_id="passing-task",
#                          get_logs=True,
#                          dag=dag
#                          )

#failing = KubernetesPodOperator(namespace='default',
#                          image="ubuntu:1604",
#                          cmds=["Python","-c"],
#                          arguments=["print('hello world')"],
#                          labels={"foo": "bar"},
#                          name="fail",
#                          task_id="failing-task",
#                          get_logs=True,
#                          dag=dag
#                          )

#passing.set_upstream(start)
#failing.set_upstream(passing)


if __name__ == "__main__":
    dag.cli()
