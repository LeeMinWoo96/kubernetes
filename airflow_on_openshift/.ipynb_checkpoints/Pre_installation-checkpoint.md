# Disconnected OCP Installation 사전 구축 준비

### 1. OpenShift 4.3 Minimum resource requirements

| Machine       | Operating System | vCPU | RAM   | Storage | Count             |
| ------------- | ---------------- | ---- | ----- | ------- | ----------------- |
| Bootstrap     | RHCOS            | 4    | 16 GB | 120 GB  | 1                 |
| Control plane | RHCOS            | 4    | 16 GB | 120 GB  | 3                 |
| Compute       | RHCOS            | 2    | 8 GB  | 120 GB  | 2 (최소 1개 이상) |

- [x] OpenShift 4.3 버전의 경우에는 위와 같이 최소 자원 요구사항이 존재하며, 해당 요구사항이 준비 되어야 설치가 가능합니다.
- [x] ==Control plane(master)의 경우에는 반드시 3개로 구성이 되어야 합니다.==
- [x] ==Container workload를 수행하기 위해서는 worker node를 최소 1개 이상 함께 구성해야 합니다.==



### 2. 사전 체크리스트

|        구분        | 내용                                                         | 구성 방안                                                    |
| :----------------: | ------------------------------------------------------------ | ------------------------------------------------------------ |
|         OS         | bastion : RHEL 7  bootstrap : CoreOS  master : CoreOS  worker : CoreOS or RHEL 7.6 | RHEL 최소 설치                                               |
|      SELINUX       | bastion : disable  나머지 : enable                           | -                                                            |
|  Network Manager   | enable                                                       |                                                              |
|         IP         | static 설정                                                  | 아래 방법중 택 1  <br />- DHCP & PXE 서버를 사용 <br />- CoreOS에 직접 static IP를 설정 |
|      Hostname      | 모든 노드에 FQDN으로 설정                                    | 예) master01.gps.ocp.com                                     |
|     RHEL 계정      | root 혹은 sudo 권한이 있는 유저                              | root 혹은 no password로 sudo 사용 가능한 계정                |
|       Domain       | 도메인                                                       | 예) ocp.com                                                  |
|    Cluster Name    | 클러스터의 하위 도메인                                       | 예) gps를 클러스터 네임으로 설정시 *.gps.ocp.com으로 클러스터 full 도메인이 구성됨 |
|       방화벽       | 모든 노드간 OPEN                                             | git, 이미지 저장소, load balancer 등 방화벽 open             |
|    시간 동기화     | NTP 혹은 chrony                                              | NTP 혹은 chrony 서버 IP 필요                                 |
|   공유 스토리지    | PV 용도의 공유 스토리지                                      | Bastion에 NFS로 구성                                         |
|      DNS 서버      | 모든 노드의 hostname과 etcd등 DNS 서버 등록 필요             | hostname, etcd-*, api, api-int, apps, *,apps 등  DNS 등록    |
|  Private Registry  | Disconnected 환경에서 OCP 배포시, 배포를 위해 필요한 이미지를 저장하는  저장소 | bastion 서버에 구성                                          |
|        SSH         | 모든 노드에 bastion에서 SSH 접속 필요                        | 배포시 bastion SSH키 포함 배포                               |
| Management Network | 클러스터를 구성 및 관리 네트워크                             | 예) 10.10.10.0/24 <br /> ●    bastion (10.10.10.10) <br /> ●    bootstrap (10.10.10.11)<br /> ●    master[1-3] (10.10.10.2[1-3]) <br /> ●    worker[1-2] (10.10.10.3[1-2]) <br /> ●    infra[1-3] (10.10.10.4[1-3]) <br /> ●    router[1-3] (10.10.10.5[1-3]) |
|  Service Network   | 서비스 네트워크                                              | 기본값) 172.16.0.0/24                                        |
| Container Network  | 컨테이너 네트워크                                            | 기본값) 10.128.0.0/24                                        |
|     NTP Server     |                                                              | 예) 10.10.10.10 (bastion에 NTP 서버를 구성할경우,  bastion IP) |
|     DNS Server     |                                                              | 예) 10.10.10.10 (bastion에 DNS 서버를 구성할경우,  bastion IP) |



### 3. Machine 네트워크 체크리스트

1)  All Machines to all machines

| Protocol | Port        | Description                                                  |
| :------: | ----------- | ------------------------------------------------------------ |
|   TCP    | 2379-2380   | etcd server, peer, and metrics ports                         |
|          | 6443        | Kubernetes  API                                              |
|          | 9000-9999   | Host level services, including the node exporter<br /> on  ports 9100-9101 and the Cluster Version Operator on port 9099. |
|          | 10249-10259 | The default ports that Kubernetes reserves                   |
|          | 10256       | openshift-sdn                                                |
|   UDP    | 4789        | VXLAN  and GENEVE                                            |
|          | 6081        | VXLAN  and GENEVE                                            |
|          | 9000-9999   | Host level services, including the node exporter on  ports 9100-9101 |
|          | 30000-32767 | Kubernetes  NodePort                                         |

* Node간 물리 네트워크 방화벽 Port 오픈 필요
* Bastion 호스트에 웹서버 구성 시 웹서버 Port오픈 필요(ex: TCP 8080)



2) NETWORK TOPOLOGY REQUIREMENTS (Load balancers)

| Port  | Machines                                                     | Description            |
| ----- | ------------------------------------------------------------ | ---------------------- |
| 6443  | Bootstrap and control plane.   You remove the bootstrap machine from the load  balancer after the bootstrap machine initializes the cluster control plane. | Kubernetes  API server |
| 22623 | Bootstrap and control plane.   You remove the bootstrap machine from the load  balancer after the bootstrap machine initializes the cluster control plane. | Machine  Config server |
| 443   | The machines that run the Ingress router pods,  compute, or worker, by default. | HTTPS  traffic         |
| 80    | The machines that run the Ingress router pods,  compute, or worker by default. | HTTP  traffic          |



3) Required DNS records

| Component      | Record                                                       |
| -------------- | ------------------------------------------------------------ |
| Kubernetes API | api.<cluster_name>.<base_domain> <br />api-int.<cluster_name>.<base_domain> |
| Routes         | *.apps.<cluster_name>.<base_domain>                          |
| etcd           | etcd-<index>.<cluster_name>.<base_domain>  <br />_ etcd-server-ssl._tcp.<cluster_name>.<base_domain> |

 

### 4. Disk 및 Network Interface 정보 확인

> baremetal의 경우, Disk 혹은 Network Interface에 대한 정보를 알 수가 없기 때문에, 사전에 RHEL을 minimal install하여 정보를 취득합니다.

1) Disk 정보 확인

```bash
# fdisk -l

Disk /dev/vda: 536.9 GB, 536870912000 bytes, 1048576000 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk label type: dos
Disk identifier: 0x000cc109

   Device Boot      Start         End      Blocks   Id  System
/dev/vda1   *        2048     2099199     1048576   83  Linux
/dev/vda2         2099200  1048575999   523238400   8e  Linux LVM

Disk /dev/mapper/rhel-root: 535.8 GB, 535792975872 bytes, 1046470656 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes

# lsblk
NAME          MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sr0            11:0    1 1024M  0 rom  
vda           252:0    0  500G  0 disk 
├─vda1        252:1    0    1G  0 part /boot
└─vda2        252:2    0  499G  0 part 
  └─rhel-root 253:0    0  499G  0 lvm  /

```

2) Network Interface 정보 확인 (Service/Provision의 NIC Name 확인 방법)

```bash
# ip -o -4 a
1: lo    inet 127.0.0.1/8 scope host lo\       valid_lft forever preferred_lft forever
2: ens3    inet 192.168.200.100/24 brd 192.168.200.255 scope global noprefixroute eth0\       valid_lft forever preferred_lft forever
3: virbr0    inet 192.168.122.1/24 brd 192.168.122.255 scope global virbr0\       valid_lft forever preferred_lft forever

# ifconfig
ens3: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.200.100  netmask 255.255.255.0  broadcast 192.168.200.255
        inet6 fe80::5054:ff:fe60:4133  prefixlen 64  scopeid 0x20<link>
        ether 52:54:00:60:41:33  txqueuelen 1000  (Ethernet)
        RX packets 3615666  bytes 1972695617 (1.8 GiB)
        RX errors 0  dropped 5  overruns 0  frame 0
        TX packets 4136277  bytes 27841990538 (25.9 GiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 715769  bytes 53496433 (51.0 MiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 715769  bytes 53496433 (51.0 MiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```



### 5. 물리 방화벽 Port Open 여부 확인 방법

1) nc 명령어를 통한 port open

```bash
# nc -l <port>
```

2) nc 명령어를 통한 port open check

```bash
# nc <IP> <port>
Test
```

●    정상 통신 될 경우 Test txt 전송 시 port open 노드에서 확인 가능

 

### 6. OCP 설치를 위해 준비할 파일 (온라인 환경)

> OCP 설치를 위해 필요한 파일을 준비 합니다. 

●    RHEL 7.7 ISO 파일 다운로드 (bastion, 또는 RHEL woker 노드에 사용)
 https://access.redhat.com/downloads/content/69/ver=/rhel---7/7.7/x86_64/product-software

 ●    CoreOS 파일 다운로드 (bootstrap, master, worker에 사용)
 https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.3/4.3.0/

○    DHCP 구성 후 배포시 

■  rhcos-4.3.0-x86_64-installer-kernel

■  rhcos-4.3.0-x86_64-installer-initramfs.img  

■  rhcos-4.3.0-x86_64-metal.raw.gz

○    Static IP 배포시

■  rhcos-4.3.0-x86_64-installer.iso

■  rhcos-4.3.0-x86_64-metal.raw.gz
 

●    openshift-install, openshift-client 파일 다운로드 (bastion)
 https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/

○    openshift-client-linux-4.3.５.tar.gz

○    openshift-install-linux-4.3.５.tar.gz

 

●    사전 준비후 Disconnected 환경에 가져갈 파일

○    패키지 다운을 위한 repository 압축 파일 (repos.tar.gz)

○    OCP 4 배포시 필요한 이미지 압축 파일 (data.tar.gz)

○    Private registry 구성을 위한 이미지 (registry.tar)

 

### 7.　YUM Repository reposync 준비

1) subscription 등록

```bash
# rpm  --import /etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release     
# subscription-manager register
Registering to:  subscription.rhsm.redhat.com:443/subscription  Username:  *레드햇 고객 포털 아이디*  Password:  *암호*  The  system has been registered with ID: 6b924884-039f-408e-8fad8d6b304bc2b5  The  registered system name is: localhost.localdomain 
```

2) OpenShift 설치에 필요한 repository 등록

```bash
#  subscription-manager list --available --matches '\*OpenShift\*' > aaa.txt
// OpenShift Subscription만 따로 뽑아서  그 중 하나를 선택하여 등록 합니다.

#  subscription-manager attach --pool=pool ID
Successfully attached a subscription for: Employee  SKU  

# subscription-manager repos  --enable=rhel-7-server-rpms --enable=rhel-7-server-extras-rpms -enable=rhel-7-server-ansible-2.8-rpms --enable=rhel-7-server-ose-4.3-rpms
Repository 'rhel-7-server-rpms' is enabled for this  system.  Repository 'rhel-7-server-ose-4.3-rpms' is enabled  for this system.  Repository 'rhel-7-server-ansible-2.8-rpms' is  enabled for this system.  Repository 'rhel-7-server-extras-rpms' is enabled  for this system.
```

3) repo sync를 위한 패키지 다운

```bash
# yum  -y install yum-utils createrepo
```

 4) repo sync 

```bash
# vim  repo.sh
#! /bin/bash
mkdir /var/repos  
for repo in \  
rhel-7-server-rpms \  
rhel-7-server-extras-rpms \  
rhel-7-server-ansible-2.-rpms \  
rhel-7-server-ose-4.3-rpms  
do 
 reposync -n  --gpgcheck -l --repoid=${repo} --download_path=/var/repos    
 createrepo -v  /var/repos/${repo} -o /var/repos/${repo}   
done

# sh repo.sh
```

 5) repository tar 압축

```bash
# tar  cvfz repos.tar.gz /var/repos/
```

6) Bastion 서버에 Repo 구성

```bash
# tar  xvfz repos.tar.gz /var/
```





### ８．Private Registry 구성을 위한 이미지 mirror 

1) 외부 환경에서 OCP Deploy를 위한 mirror 이미지 준비

```bash
# wget https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-client-linux-4.3.1.tar.gz 

# tar xzf /var/www/html/openshift-client-linux-4.3.1.tar.gz -C /usr/local/bin/
```

2) 작업 디렉토리 생성

```bash
# mkdir  -p /opt/registry/{auth,data,certs}
```

3) 인증서 작업

＊　https 구성을 위한 SSL 인증서 생성

```bash
# cd  /opt/registry/certs  

#  openssl req -newkey rsa:4096 -nodes -sha256 -keyout domain.key -x509 -days  36500 -out domain.crt
Generating a 4096 bit RSA private key  ............................................................................  ...................++  ...............................................++  writing new private key to 'domain.key'  -----  You are about to be asked to enter information that  will be incorporated  into your certificate request.  What you are about to enter is what is called a  Distinguished Name or a DN.  There are quite a few fields but you can leave some  blank  For some fields there will be a default value,  If you enter '.', the field will be left blank.  -----  
Country Name (2 letter code) [XX]:KR  
State or Province Name (full name) []:Seoul  
Locality Name (eg, city) [Default City]:Gangnam  
Organization Name (eg, company) [Default Company  Ltd]:Redhat  
Organizational Unit Name (eg, section) []:GPS  
Common Name (eg, your name or your server's  hostname)  []:pre.gps.ocp.com

# ls -l  /otp/registry/certs/
total 8  
-rw-r--r--. 1 root root 2102 Mar 4 21:16 domain.crt  
-rw-r--r--. 1 root root 3272 Mar 4 21:16 domain.key

# cp  /opt/registry/certs/domain.crt /etc/pki/ca-trust/source/anchors/ 
# update-ca-trust extract
```

＊　이미지 다운을 위한 Pull Secret 생성

```bash
 # vim  /opt/registry/pull-secret
{"auths":{"cloud.openshift.com":{"auth":"b3BlbnNoaWZ0LXJlbGVhc2UtZGV2K3NvaHJlZGhhdGNvbTF2NWhmY3ZrbmR6Z2QxZHFlOG9vY21xMHFlbjpXSThZR1pHME43R1FWSjFKMVM5QVJZUFhST1NSODQ1NE5ITVFGNFJDUjEyUjk3SFo1SjJKOFZZS09MNExYUFpW","email":"soh@redhat.com"},"quay.io":{"auth":"b3BlbnNoaWZ0LXJlbGVhc2UtZGV2K3NvaHJlZGhhdGNvbTF2NWhmY3ZrbmR6Z2QxZHFlOG9vY21xMHFlbjpXSThZR1pHME43R1FWSjFKMVM5QVJZUFhST1NSODQ1NE5ITVFGNFJDUjEyUjk3SFo1SjJKOFZZS09MNExYUFpW","email":"soh@redhat.com"},"registry.connect.redhat.com":{"auth":"NTMwNDkwOTZ8dWhjLTFWNWhmQ1ZrbmR6Z2QxZHFFOG9vQ01xMHFFbjpleUpoYkdjaU9pSlNVelV4TWlKOS5leUp6ZFdJaU9pSTNaalV5TW1Rd1l6SXlNR1EwTkRNMVlqRTNZakJrWkRsak9UVTFNVFJqTXlKOS51SldsMVhPelNvVmx4WXJYZmNkSjQ3ZDZuWkV1dExnVjFGcmxtc2ZmdExQcVNPbUY3SFdfLXlJcm1Cak5UNzlMQWhWNldRUGJHZ2dFVUtlanJ5RGRCN1pkeWRPZkZzVm9kY0dmS3l6dm5RUmc1d0RlekhPTThfOFFjcEppaXhyWFhzOFJWT3U2bDE5Z19oNTJxbDYzN3J6cHUxUURmTUNCZGJIYW9hc3JrTjc1d2t3ak1wXzd6TV9wNkZnTk5Od0V3UW9pMnZEN2pJblRsWkxGYkFzSlhMY25Ud3dhMV9USTYyZlJDdjc2emE5aUszaFl2ZDQ1Z2VvbFppb1JtM2hNWWNfV3VmNnB4ZkdWaF83NlU2SVIxcEMyRFZmRTZDN3FwYnlzU2VNYjBDUE1aZnRFcmpEbVdWbDhSS1hSdjhPUHdXbHhQakN4bmhRenlsSUVRaHpOZ2lTUURscUt1YlJJU0d3VDBRSTJnak9URDJSbkljeGp5VzF1N2ZpS1lINFhRV3pGeFFmTS1JSjVBUkFQNEI3Y3pZdjlBaWNVSm1Ma0QyQS1FSmdJSS1heWhpY0o1RjkwbWVLb3ZpZkF1ekwxVVdnZmkxeVdGazhEczRDb2pyLTZiN0hMZU45cDQtYWYwQ21pU1gzYlhtVzhzbkgzSTBveGN5TzAwNDBzQ2lwTUtIazhFNWJwZUJfTGZ0YnR1Qms5bS1ZcjhLbzk5eXA2THdGS3FuN3V6WDltTWRxdXRob2hvV1dKdGtfQ2F6dmtxT18zakYxb0tsRG9lVEtaSXJRbndtZUQ5UEhCSkxvUDNSYUM1NVU0YzR0YXRtbGczRlQzQWh4TDk0NnZhN19qY1VkbEVCSERUQU5qazM4RlFvMFdhZDZKWVJLdnRGR0xSUmRBZlIzUm5uMA==","email":"soh@redhat.com"},"registry.redhat.io":{"auth":"NTMwNDkwOTZ8dWhjLTFWNWhmQ1ZrbmR6Z2QxZHFFOG9vQ01xMHFFbjpleUpoYkdjaU9pSlNVelV4TWlKOS5leUp6ZFdJaU9pSTNaalV5TW1Rd1l6SXlNR1EwTkRNMVlqRTNZakJrWkRsak9UVTFNVFJqTXlKOS51SldsMVhPelNvVmx4WXJYZmNkSjQ3ZDZuWkV1dExnVjFGcmxtc2ZmdExQcVNPbUY3SFdfLXlJcm1Cak5UNzlMQWhWNldRUGJHZ2dFVUtlanJ5RGRCN1pkeWRPZkZzVm9kY0dmS3l6dm5RUmc1d0RlekhPTThfOFFjcEppaXhyWFhzOFJWT3U2bDE5Z19oNTJxbDYzN3J6cHUxUURmTUNCZGJIYW9hc3JrTjc1d2t3ak1wXzd6TV9wNkZnTk5Od0V3UW9pMnZEN2pJblRsWkxGYkFzSlhMY25Ud3dhMV9USTYyZlJDdjc2emE5aUszaFl2ZDQ1Z2VvbFppb1JtM2hNWWNfV3VmNnB4ZkdWaF83NlU2SVIxcEMyRFZmRTZDN3FwYnlzU2VNYjBDUE1aZnRFcmpEbVdWbDhSS1hSdjhPUHdXbHhQakN4bmhRenlsSUVRaHpOZ2lTUURscUt1YlJJU0d3VDBRSTJnak9URDJSbkljeGp5VzF1N2ZpS1lINFhRV3pGeFFmTS1JSjVBUkFQNEI3Y3pZdjlBaWNVSm1Ma0QyQS1FSmdJSS1heWhpY0o1RjkwbWVLb3ZpZkF1ekwxVVdnZmkxeVdGazhEczRDb2pyLTZiN0hMZU45cDQtYWYwQ21pU1gzYlhtVzhzbkgzSTBveGN5TzAwNDBzQ2lwTUtIazhFNWJwZUJfTGZ0YnR1Qms5bS1ZcjhLbzk5eXA2THdGS3FuN3V6WDltTWRxdXRob2hvV1dKdGtfQ2F6dmtxT18zakYxb0tsRG9lVEtaSXJRbndtZUQ5UEhCSkxvUDNSYUM1NVU0YzR0YXRtbGczRlQzQWh4TDk0NnZhN19qY1VkbEVCSERUQU5qazM4RlFvMFdhZDZKWVJLdnRGR0xSUmRBZlIzUm5uMA==","email":"soh@redhat.com"}}}    
// 해당 파일은 온라인에서 다운 받을 수 있습니다.
https://cloud.redhat.com/openshift/install/pull-secret 
```

3) 방화벽　해제

```bash
#  firewall-cmd --add-port=5000/tcp
#  firewall-cmd --add-port=5000/tcp --permanent
```

4) registry 컨테이너 생성

```bash
# vim  /opt/registry/registry.sh
 podman run --name mirror-registry -p 5000:5000 \  
 -v /opt/registry/data:/var/lib/registry:z \  
 -v /opt/registry/certs/:/certs:z \  
 -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \  
 -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \  
 -d docker.io/library/registry:2
 
# sh  /opt/registry/registry.sh

# podman ps  
CONTAINER ID IMAGE             COMMAND        CREATED    STATUS      PORTS          NAMES  e0ab92483707 docker.io/library/registry:2 /entrypoint.sh /e... 5 seconds ago Up 4 seconds ago 0.0.0.0:5000->5000/tcp mirror-registry

# curl  -k https://pre.gps.ocp.com:5000/v2/_catalog   
{"repositories":[]}  
```

5) registry mirror

```bash
# vi /opt/registry/mirror.sh  
OCP_RELEASE="4.3.1-x86_64"  
LOCAL_REGISTRY='pre.gps.ocp.com:5000'  
LOCAL_REPOSITORY='ocp4/openshift4'  
PRODUCT_REPO='openshift-release-dev'  
RELEASE_NAME="ocp-release"  
LOCAL_SECRET_JSON=/registry/pull-secret     

oc adm -a  ${LOCAL_SECRET_JSON} release mirror \  
--from=quay.io/${PRODUCT_REPO}/${RELEASE_NAME}:${OCP_RELEASE}  \  
--to=${LOCAL_REGISTRY}/${LOCAL_REPOSITORY}  \  
--to-release-image=${LOCAL_REGISTRY}/${LOCAL_REPOSITORY}:${OCP_RELEASE}    

# sh -x   /opt/registry/mirror.sh
+  OCP_RELEASE=4.3.1-x86_64  
+ LOCAL_REGISTRY=pre.gps.ocp.com:5000  
+  LOCAL_REPOSITORY=ocp4/openshift4  
+  PRODUCT_REPO=openshift-release-dev  
+  RELEASE_NAME=ocp-release  
+  LOCAL_SECRET_JSON=/registry/pull-secret  
+ oc adm -a  /registry/pull-secret release mirror  --from=quay.io/openshift-release-dev/ocp-release:4.3.1-x86_64  --to=pre.gps.ocp.com:5000/ocp4/openshift4  --to-release-image=pre.gps.ocp.com:5000/ocp4/openshift4:4.3.1-x86_64  info: Mirroring 101  images to pre.gps.ocp.com:5000/ocp4/openshift4 ...    
…(생략)...
Success  
Update image:   pre.gps.ocp.com:5000/ocp4/openshift4:4.3.1-x86_64  
Mirror prefix:  pre.gps.ocp.com:5000/ocp4/openshift4     

To use the new mirrored repository to  install, add the following section to the install-config.yaml:     

imageContentSources:  
- mirrors:   
　- pre.gps.ocp.com:5000/ocp4/openshift4   
　source:  quay.io/openshift-release-dev/ocp-release  
- mirrors:  
　- pre.gps.ocp.com:5000/ocp4/openshift4   
　source:  quay.io/openshift-release-dev/ocp-v4.0-art-dev  
```

6) 이미지 압축

```bash
# tar －cvfz data.tar.gz /registry/data
```

7) Bastion 서버에 압축파일 압축 해제

```bash
# tar －xvfz data.tar.gz -C /opt/registry/
```



### ９. 외부 환경에서 Private Registry 구성을 위한 이미지 준비

1) 이미지 확인

```bash
 #  podman images  
 REPOSITORY          TAG  IMAGE ID    CREATED    SIZE  docker.io/library/registry  2    708bc6af7e5e  5 weeks ago   26.3 MB  
```

2) 이미지 압축 저장

```bash
 #  podman save -o registry.tar docker.io/library/registry:2  
```

3) Bastion 서버에 이미지 load

```bash
 #  podman load -i registry.tar
```