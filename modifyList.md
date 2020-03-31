
~DockerFile 에서 
현재 Airflow 버전 1.10.1 로 수정 ~

[참고](https://github.com/puckel/docker-airflow/issues/342)

~DockerFile 에서
pip install Flask==1.0 추가~

~airflow 에서 Flask 버전을 고정하지 않아 문제 생김~


DockerFile 변경

[도커파일](https://github.com/puckel/docker-airflow/blob/master/Dockerfile)



chart 파일에 문제가 있었음 helm dependency update 를 진행하면 requirment 에 정해둔 chart를 다운받게됨 
이 때 안에 버전이 안맞는게 있음 -> 압출 풀고 extension 을 apps/v1으로 변경해야함 


extensions 에서 apps/v1 으로 변경하게되면
spec 에 반드시 selector 가 있어야하고 
.spec.template.labels 와 일치해야함 ~~

에어플로우 이미지 수정 -> airflow:latest 버전이 없었음
-> Docker image 를 로컬에 만들고 진행해야함 

wait for postgre -> 현재 host 환경변수 값이 전달되지 않음 
-> 
기본으로 불러오는 docker image 버전을 낮춰줘야 했음 (git clone 할때)
image 구성이 살짝 바뀌었는데 postgre 설정 부분이 조금 차이가 있어 그 부분을 맞춰주거나 버전 낮추면 가능
postgre설정 부분 제외하고 큰 차이가 없음 (현재 1.10.4 clone으로 고정)


Pod 에서 service account 가 적용되지 않음 -> spec에 servicve account 위치 수정
선언 위치가 잘못되었었음 spec.template.spec  에 위치 시켜야함 


[타임아웃 에러  ](https://github.com/kubernetes-client/python/issues/990)
kubernetes executor 를 사용하려면 Labelselector 반드시 정의 -> 수정중

1.10.5 버전 이후로 python 패키지 중 KubernetesJobWatcher 에서 timeout 문제 발생
-> 현재 수정 방안은 Error를 Warning으로 바꾸는게 유일함 (이것도 잘 안됨)
-> 1.10.4 버전으로 downgrade


현재 git 주소 변경시 메모리 문제 -> 해결중
-> Airflow repository 에 있을때? 우선 저장소 위치 바꿔서 해결

Configmap -> airflow.cfg 파일에 serviceaccount 전달 



