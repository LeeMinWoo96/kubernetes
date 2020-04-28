## Helm
----
[1. 특징](#특징)

[2. 설치](#설치)

[3. 명령](#명령)

[4. 구조](#구조)

[5. Helm v2 vs v3](#Helm-v2-vs-v3)

[6. 참고 자료](#참고-자료)


----
**Helm : package 관리 툴**
Python 의 pip와 유사한 기능

***Version 2 기준 V3 는 tiller 사라짐***

### 특징
- 복잡한 어플리케이션 배포 관리
    - kubernetes 오케스트레이션 된 애플리케이션 배포는 매우 복잡함 -> helm 차트는 복잡한 애플리 케이션을 코드로 관리하여 배포 
- Hooks
    - helm 차트로 관리를 하여 생명주기를 개입할 수 있는 기능을 Hoo을 이용해 제공 
- 릴리즈 

![](./img/helm.PNG)


- Helm Chart : Kubernetes에서 리소스를 만들기 위한 템플릿 화 된 yaml 형식의 파일
- Helm (Chart) Repository : Helm Repository는 해당 리포지토리에 있는 모든 차트의 모든 메타데이터를 포함하는 저장소. 상황에 따라서, Public Repository를 사용 하거나 내부에 Private Repository를 구성할 수 있습니다.
- Helm Client(cli) : 외부의 저장소에서 Chart를  가져 오거나, gRPC로 Helm Server 와 통신하여 요청을 하는 역할을 합니다.
- Helm Server(tiller) : Helm Client의 요청을 처리하기 위하여 대기하며, 요청이 있을 경우 Kuberernetes에 Chart를 설치하고 릴리즈를 관리 합니다.

일반적으로 tiller 는 kubernetes 클러스터 내부에서 실행 -> tiller 를 위한 Role 을 설정해야함

### 설치 

```
$ curl https://raw.githubusercontent.com/helm/helm/master/scripts/get > get_helm.sh
$ chmod 700 get_helm.sh
$ ./get_helm.sh


sudo apt-get install socat # 소켓 설치
```

tiller 서비스 account 생성 ```kubectl -n kube-system create sa tiller```

cluster-admin role 부여 
```kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller```

tiller 설치 ```helm init --service-account tiller```

### v3설치

[helm v3 설치 window](https://velog.io/@rudasoft/Helm-%EC%84%A4%EC%B9%98-m0k3y75ock)

[linux](https://gruuuuu.github.io/cloud/l-helm-basic/#)
----



### 명령

`helm repo` 명령을 이용하여 Repository 관리 가능 
ex) helm repo list

`helm install [chart name]` 명령을 이용해서 helm chart 배포 가능

`helm ls` 명령을 이용하여 배포된 release 확인 가능
 
 만약 베포되면 kubernetes 에서 확인할 수 있다.


존재하면 upgrade 하고 없을땐 install 하는 명령 뒤에 values 옵션으로 커스터마이징 

`helm upgrade --install airflow ./airflow/ --namespace airflow  --values ./airflow/values.yaml`


배포된 helm 차트 지우는 명령(찌거기도 전부)
`helm ls --all --short | xargs -L1 helm delete --purge`


`helm dependany update` 명령을 통해 종속된 차트들을 다운 받을 수 있음 


----
### 구조


 ![](./img/구조.PNG)
 
 
---
### Helm v2 vs v3

1. Version 3 는 tiller가 사라졌다.
    - kubernetes 1.6 이하엔 rbac 를 지원하지 않아 tiller 가 kubernetes 서버에 존재하면서 관리했지만 이젠 rbac 를 지원함으로 tiller 가 사라졌다 -> 보안 증가 
    
2. namespace를 생성해주지 못한다 -> 먼저 생성하고 진행해야 한다.
3. helm delete 를 진행했을때 자동으로 puarg 옵션이 자동으로 적용되어 깔끔하게 지워준다.


----
### 참고 자료

[개념](https://tech.osci.kr/2019/11/23/86027123/)

[설치](https://reoim.tistory.com/entry/Kubernetes-Helm-%EC%82%AC%EC%9A%A9%EB%B2%95)