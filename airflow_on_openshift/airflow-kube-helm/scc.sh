


oc adm policy add-scc-to-user anyuid system:serviceaccount:airflow:airflow-cluster-access

oc adm policy add-scc-to-user anyuid system:serviceaccount:airflow:default

oc adm policy add-scc-to-user hostaccess system:serviceaccount:airflow:airflow-cluster-access

