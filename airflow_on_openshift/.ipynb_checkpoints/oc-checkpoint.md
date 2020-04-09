
### Openshift cli 설치


#### 설치파일

os에 맞는 파일 다운 후 압출풀기<br>
[설치링크](https://github.com/openshift/okd/releases)

----
#### 설치

환경변수 설정에 들어가서openshift cli 를 설치한 곳으로 변수를 설정합니다.

![](./img/env.png)
![](./img/path.png)


그 후 Path에 해당 변수를 추가합니다. 

![](./img/path2.png)


----

#### 설치 확인 

커맨드창에서 oc version 커맨드를 입력하여 출력되면 정상설치입니다. 

![](./img/version.png)


----

#### 접속


oc login <주소> 커맨드로 로그인 
-> openshift에 접속

![](./img/exec.png)

![](./img/exec2.png)
