### Openshift image registry

---

현재 상태

외부 접속 x 
-> 실패한 이유는 docker registry는 로컬머신에서 사용하는 것이 아니라면 https만 지원을 하기 때문이다. 그럼 원격지에서 접속하기 위해서는 docker registry 설정을 해주어야 한다. (SSL 발급 및 설정)

[더 참고해보기](https://docs.openshift.com/container-platform/3.7/install_config/registry/securing_and_exposing_registry.html)                      

UI x
-> ui 관련 이미지를 받아 pod 을 띄우는 것 고려
-> web ui 연결하려면 HTTPS 접속 가능해야함

Container list x
-> link를 걸어야하는데 docker container list가 안보임
 
pod 생성해서 (base ubuntu) 인증서 넘겨서 login 부분 확인

Airflow 에서 pull 확인 -> 로그인 안했는데 왜 되지???



---

수정 ing

/etc/pki/tls 에서 subjectAltName 추가



/etc/docker/certs.d/ 아래에 ip 명으로 폴더 생성 및 권한 부여

SSL 인증서를 위 경로에 복사해 넣기

/ets/pki/tls/certs 아래에 인증서 정보 있음 default 설정임 이 인증서를 사용


현재 내부 cluster 에 docker가 설치되어있으면 실행가능함 (인증서 갖고 있을 때)



/etc/hosts 파일에 도메인 등록 되어있는지



---

참고자료 

[openshift registry](https://docs.openshift.com/container-platform/4.3/registry/accessing-the-registry.html#registry-viewing-logs_accessing-the-registry)

[docker registry](https://novemberde.github.io/2017/04/09/Docker_Registry_0.html)

[docker registry2](https://www.44bits.io/ko/post/running-docker-registry-and-using-s3-storage)

[SSL 개념](https://namjackson.tistory.com/24)

[subjectAltName](https://github.com/docker/distribution/issues/948)