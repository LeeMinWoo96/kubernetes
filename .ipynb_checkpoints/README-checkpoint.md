작성자 : 이민우 <br>
작성일 : 2020-03-31<br>
내용 : Airflow kubernetesPodOperator 설치 <br>

---

[1. 개발환경](#개발환경)<br>
[2. Helm 구성도](#Helm-구성)<br>
[3. 설치](#설치)
---

#### 개발 환경

ubuntu 18.04 on ec2<br>
helm 2.16.3<br>
minikube 1.17.4<br>
airlfow 1.10.4<br>
postgre 0.13.1<br>

---


#### Helm 구성 
![구성](./img/gusung.PNG)



#### 설치 

**시작 전 Docker 와 Helm 설치 해야합니다.**

minikube , helm 문서에 설치법 정리해두었습니다.

**1. helm chart download**
```
git clone https://github.com/LeeMinWoo96/kubernetes.git
```

**2. Minikube start ( 가상머신 안씀을 가정)**

`minikube start --vm-driver=none`

**3. Helm tiller 를 Kubernetes cluster에 설치(helm 3 버전 이하일 경우)<br>**

```
kubectl -n kube-system create sa tiller  #tiller 서비스 account 생성


kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller  #cluster-admin role 부여 

helm init --service-account tiller  #tiller 설치

```

**4. Airflow Docker image build**

```
cd kubernetes/airflow-kube-helm
./examples/minikube/docker/build-docker.sh

```

**5. FERNET_KEY 등록 (데이터베이스의 비밀번호를 암호화)**

```
python -c "from cryptography.fernet import Fernet; FERNET_KEY = Fernet.generate_key().decode(); print(FERNET_KEY)"
```

위 코드를 통해 생성된 key를 vaule.yaml 파일에서 fernet_key 부분을 찾아 

![key](./img/key.PNG)

이런식으로 수정합니다.

**6. git url 수정**
현재 dag 를 저의 git 폴더에서 임의로 가져오고 있습니다. 따로 git url을 수정하여 dag 경로를 바꾸고 싶다면 vaule.yaml 파일에서 url을 수정하여 바꿀 수 있습니다. subpath 는 git 경로에서 dag 가 있는 폴더 위치입니다.


![url](./img/url.PNG)

**7. helm dependency update**

이 명령은 requirment.yaml 파일을 보고 종속된 다른 차트를 받아오는 명령입니다.
현재 postgre 0.13.1 차트를 받아오게 되는데 helm version 과 apiVersion 충돌이 있어 수정해두었습니다.

만약 저 명령을 통해 받아온다면 chart 디렉토리의 파일을 압축해제한 후
template 디렉토리의 yaml 파일들에 들어가 맨 첫줄을 `piVersion: apps/v1`으로 수정하면 됩니다.

현재는 수정을 해둔 상태입니다.

**8. Use Helm to generate the yaml files and deploy Airflow.**
helm 차트를 배포합니다. 해당 명령어는
airflow 라는 이름으로 airflow/ 디렉토리 내의 파일을 이용하여 
쿠버네트스 namespace는 airflow로 하고 airflow/values.yaml 로 값을 설정하겠다 라는 의미입니다.

```
helm upgrade --install airflow airflow/ \
    --namespace airflow \
    --values airflow/values.yaml
```

**9. 작동 확인 및 접속**

동작 확인

![run](./img/run.PNG)

port 확인 


![port](./img/port.PNG)

nodeport로 개방되어 있기 때문에 외부에서 port로 바로 접근 가능

![port](./img/web.PNG)


-----

*이 외에 airflow.cfg 를 수정하고 싶으면 configuemap.yaml 에서 확인 할 수 있고
나머지 기본 설정 값들은 value.ymal 에 들어 있습니다.*

---

#### 참고자료

[KubernetesExecutor for Airflow](https://towardsdatascience.com/kubernetesexecutor-for-airflow-e2155e0f909c)

[Kubernetes 위에서 Airflow 사용하기](https://humbledude.github.io/blog/2019/07/12/airflow-on-k8s/)

[doc](https://airflow.apache.org/docs/stable/kubernetes.html)

[helm 을 사용하지 않은 가이드](https://github.com/apache/airflow/tree/master/scripts/ci/kubernetes) 

[Celery Executor 기반 helm 차트](https://github.com/helm/charts/tree/master/stable/airflow)
