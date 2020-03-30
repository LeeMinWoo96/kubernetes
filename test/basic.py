
import os
import sys

import airflow
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.contrib.kubernetes.pod import Port

from airflow.contrib.kubernetes.volume import Volume
from airflow.contrib.kubernetes.volume_mount import VolumeMount

from datetime import datetime, timedelta

"""
depends_on_past: when set to True, keeps a task from getting triggered if the previous schedule for the task hasn’t succeeded

wait_fow_downstream: when set to true, an instance of task X will wait for tasks immediately downstream of the previous instance of task X to finish successfully before it runs.

retries (int) – the number of retries that should be performed before failing the task

catchup - backfill 할건지 

"""



                                            
default_args = {
        
        'owner' : 'airflow',
        'depends_on_past' : True,
        'wait_for_downstream' : True,
        'start_date' : datetime(2020,3,25),
        'schedule_interval': '@once'
        }



dag = DAG(
        dag_id = 'testing',
        catchup = True,
        default_args = default_args,
        )



k = KubernetesPodOperator(namespace='airflow',
                          image="task1",
                          name="test",
                          task_id="task1",
                          dag = dag
                          )

k2 = KubernetesPodOperator(namespace='airflow',
                          image="task2",
                          ports=[port],
                          name="test2",
                          task_id="task2",
                          dag = dag
                          )

k2.set_upstream(k)






