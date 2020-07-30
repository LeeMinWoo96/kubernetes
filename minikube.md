
## minikube

mini + kube로써 보통 로컬 환경에서 쿠버네티스 환경을 제공하고자 하는 프로젝트 명이며, 프로그램 이름이다. k3s 와 유사하지만 다르다.

*k3s 는 etcd 대신 Sqlite 를 사용합니다.*

---
### 설치


현재 개발환경 :ec2 (ubuntu 18.04)

**설치 전 Docker 설치 해야합니다.**

**Kuberctl install**
```
curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl

chmod +x ./kubectl

sudo mv ./kubectl /usr/local/bin/kubectl
```

**Docker install**

```
sudo apt-get update && \
    sudo apt-get install docker.io -y
```



**Kubernetes 1.18~**

```sudo apt install conntrack```



**Minikube install**
```
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && chmod +x minikube && sudo mv minikube /usr/local/bin/
```

root 로 전환 후 구동 ```minikube start --vm-driver=none ```

---

### 유의사항 

1. 2cpu, 2GB, 20DB 이상 임으로 t2.medium 사양 이상이 필요하다 
2. 반드시 docker 가 설치되어 있어야한다.
3. 구동 실패 후 다시 구동시엔 minikube delete 로 클러스트를 삭제해야한다.



#### 참고자료

[ec2에서 구동 ](https://www.oops4u.com/2366)

[minikube 설치 및 활용](https://medium.com/@cratios48/minikube-%EC%84%A4%EC%B9%98-%EB%B0%8F-%ED%99%9C%EC%9A%A9-4a63ddbc7fcb)

[minikube on ec2](https://www.radishlogic.com/kubernetes/running-minikube-in-aws-ec2-ubuntu/)
