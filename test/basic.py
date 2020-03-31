
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

from airflow import configuration as conf
                                            
default_args = {
        'owner' : 'airflow',
        'depends_on_past' : True,
        'wait_for_downstream' : True,
        'start_date' : datetime(2020,3,29),
        'schedule_interval': '@once',
        }



dag = DAG(
        dag_id = 'testing',
        catchup = True,
        default_args = default_args,
        )

namespace = conf.get('kubernetes', 'NAMESPACE')

print('debug :  ', namespace)

k = KubernetesPodOperator(namespace=namespace,
                          image='hello-world:latest',
                          #image="task1",
                          name="test",
                          task_id="task1",
                          dag = dag,
                          in_cluster=True,
                          
                          )

k2 = KubernetesPodOperator(namespace=namespace,
                          image='hello-world:latest',
                          #image="task2",
                          name="test2",
                          task_id="task2",
                          dag = dag,
                          in_cluster=True,
                          )

k2.set_upstream(k)






