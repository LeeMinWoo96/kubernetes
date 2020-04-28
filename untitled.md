#### Jupyter enterprise gateway 

**목적 : kernel custom**

----

1. 환경

Helm v3 , okd4 및 ec2 ubuntu minikube(test)

2. 진행사항

***Minikube 환경***

- [x] Enterprise gatway 구조 파악 및 노트북 설치
- [x] 설치된 Notebook과 pod으로 올린 gateway와 연동 (ec2 ubuntu minikube 환경)
- [x] Custom kernel을 위한 volume mount(hostPath) (ec2)
- [x] Custom kernel image 생성 (기존 Kernel image 확장)
- [x] Custom kernel 과 Enterprise gatway 연동

---

***OKD 환경***

- [x] test 환경에 구축한 helm 차트 수정(OKD에 이미 올라온 것과 동일한 내용 수정)
- [x] Jupyter notebook pod 생성
- [x] scc 권한 해제
- [x] notebook pod과 enterpris
 

