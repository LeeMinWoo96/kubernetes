### OpenShift 4.3 vSphere Installation Guide - None DHCP (UPI)

---------------------------

### ==주의 사항==

- 설치 실패 후 설치 `디렉토리 재 사용 금지`

- 기존 디렉토리 이름으로 재 설치 하고자 한다면, `기존 디렉토리 백업후 기존 디렉토리 이름으로 재 생성 후 설치 가능`

- 기존 ignition 파일 재 사용 할 수 없고, `ignition 파일은 새로 생성하여 재 설치 진행해야 합니다.`

- ==vShpere와 bare-metal의 install-config.yaml은 내용이 다릅니다. (설치 시 유의)==

- install-config.yaml 외에 다른 구성은 bare-metal 구성에도 참고 할 수 있습니다.

  

### 1. OpenShift 4.3 Minimum resource requirements** 

| Machine       | Operating System | vCPU | RAM   | Storage | Count             |
| ------------- | ---------------- | ---- | ----- | ------- | ----------------- |
| Bootstrap     | RHCOS            | 4    | 16 GB | 120 GB  | 1                 |
| Control plane | RHCOS            | 4    | 16 GB | 120 GB  | 3                 |
| Compute       | RHCOS            | 2    | 8 GB  | 120 GB  | 2 (최소 1개 이상) |

- [x] OpenShift 4.3 버전의 경우에는 위와 같이 최소 자원 요구사항이 존재하며, 해당 요구사항이 준비 되어야 설치가 가능합니다.
- [x] ==Control plane(master)의 경우에는 반드시 3개로 구성이 되어야 합니다.==
- [x] ==Container workload를 수행하기 위해서는 worker node를 최소 1개 이상 함께 구성해야 합니다.==



### 2. PoC 준비 테스트 환경

| Machine   | Operating System | vCPU | RAM   | Storage | Count |
| --------- | ---------------- | ---- | ----- | ------- | ----- |
| bastion   | RHEL 7.7         | 8    | 16 GB | 300 GB  | 1     |
| bootstrap | RHCOS 4.3        | 8    | 16 GB | 300 GB  | 1     |
| master    | RHCOS 4.3        | 8    | 32 GB | 300 GB  | 3     |
| infra     | RHCOS 4.3        | 16   | 64 GB | 300 GB  | 2     |
| worker    | RHCOS 4.3        | 16   | 16 GB | 300 GB  | 2     |

- [x] 해당 가이드는 인터넷이 되는 vSphere 환경에서 OpenShift 4.3 설치 구성 테스트를 진행 하였습니다.

- [x] ==모든 노드는인터넷이 되는 환경 입니다.== 

- [x] 인터넷이 되는 VMware(vSphere) 환경 구축에 도움이 되었으면 합니다.

- [x] 해당 가이드는 DHCP 서버를 구성 할 수 없는 사항에 대비하여 테스트를 진행 하였습니다.

- [x] bare-metal 환경에서도 활용 할 수 있습니다. (install-config.yaml 내용 다름)

  

  2-1) User-Provisioned Infrastructure  (UPI)를 위해 준비해야 하는 부분 (사전 준비)**

  - [x] Load Balancer (HAproxy)

    > Haproxy는 OCP 4.3 설치시 Load Balancer 역할을 합니다. 
    > Haproxy(Load Balancer)는 master, infra, bootstrap node 간에 통신을 할 수 있는 front and backend protocol(Upstream)을 제공함으로써 OCP 4.3 설치에 중요한 브로커 역할을 수행합니다.

  - [x] DNS 구성

    >  RHOCP 내부 DNS로 각 Node간 FQDN Resolving으로 활용하게 되며 구성을 위한 namd.conf 설정 변경, zone 파일 생성 및 DNS 서버 방화벽 오픈 작업을 수행합니다.

  

### 3. subscription 설정

>  테스트 환경에서는 따로 yum repository를 구축하지 않고, subscription manager를 사용하였습니다.



3-1) subscription 등록

```bash
# rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release

# subscription-manager register
Registering to: subscription.rhsm.redhat.com:443/subscription
Username: ${USERNAME} 
Password: ${PASSWORD}
The system has been registered with ID: 6b924884-039f-408e-8fad-8d6b304bc2b5
The registered system name is: localhost.localdomain
```

> 등록 시 redhat customer portal ID/PWD를 입력합니다.



3-2) OpenShift 설치에 필요한 RPM 활성화	

```bash
# subscription-manager list --available --matches '*OpenShift*' > aaa.txt

// OpenShift Subscription만 따로 뽑아서 그 중 하나를 선택하여 등록 합니다.

# subscription-manager attach --pool=8a85f9833e1404a9013e3cddf95a0599
Successfully attached a subscription for: Employee SKU

# subscription-manager repos --enable="rhel-7-server-rpms" --enable="rhel-7-server-extras-rpms" --enable="rhel-7-server-ansible-2.8-rpms" --enable="rhel-7-server-ose-4.3-rpms"
   Repository 'rhel-7-server-rpms' is enabled for this system.
Repository 'rhel-7-server-ose-4.3-rpms' is enabled for this system.
   Repository 'rhel-7-server-ansible-2.8-rpms' is enabled for this system.
Repository 'rhel-7-server-extras-rpms' is enabled for this system.				
```



### 4. Bastion 서버 Hostname 변경

4-1) hostname 변경

```bash
# hostnamectl set-hostname bastion.ocp4.skbb-poc.com
```

4-2) 변경된 hostname 확인

```bash
[root@bastion ~]# hostnamectl
   Static hostname: bastion.ocp4.skbb-poc.com
         Icon name: computer-vm
           Chassis: vm
        Machine ID: df1374b4f6984c949c2210afc1d33c2e
           Boot ID: 04a0ed0b6e184c708a818938b2d169d1
    Virtualization: vmware
  Operating System: Employee SKU
       CPE OS Name: cpe:/o:redhat:enterprise_linux:7.6:GA:server
            Kernel: Linux 3.10.0-957.el7.x86_64
      Architecture: x86-64
```



### 5. httpd install

5-1) httpd install

```bash
[root@bastion ~]# yum install -y httpd
```

5-2) httpd port 변경

> haproxy 구성 시에 80/443 port가 사용 되므로 겹치치 않도록 httpd port를 8080 (다른 Port)으로 변경

```bash
# vi /etc/httpd/conf/httpd.conf (설정 파일 수정)
   #Listen 80 
   Listen 8080
--- 생략 ---
```

5-3) Port 방화벽 해제 및 서비스 시작

```bash
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-service=http
firewall-cmd --reload
systemctl enable httpd
systemctl start httpd
systemctl status httpd
```



### 6. DNS 구성

- OpenShift 4.3 환경 구성을 위해서는 DNS 구성이 정방향, 역방향이 다 가능해야 합니다.
- DNS는 name 확인(A records), 인증서 생성(PTR records) 및 서비스 검색(SRV records)에 사용 됩니다.
- OpenShift 4버전은 클러스터 DNS records에 통합 될 clusterid 개념이 있습니다.
  DNS records에는 모두 CLUSTERID.DOMAIN이 포함됩니다.
  즉, clusterid는 FQDN의일부가 되는 것 입니다.



6-1)  정방향 DNS (FORWARD DNS RECORDS)

-  정방향 DNS records는 bootstrap, master, infra, worker node에 대해 생성합니다.

- 또한, api 및 api-int에 대한 항목을 만들어 각각의 load balancer를 가르켜야 합니다.

  (두 항목 모두 동일한 load balancer를 가리킬 수 있음)

6-2)  ETCD DNS RECORDS

- etcd를 생성하기 위해서는 두 개의 record type이 필요합니다.
- 정방향 record는 master의 IP를 가리켜야 합니다.
- 또한, name은 etcd-INDEX여야 하며, 0부터 시작 됩니다.
- ==여러 etcd-entries를 가리키는 SRV records도 생성해야 하며, 이 record를 우선 순위 0, 가중치 10 및 포트는 2380으로 설정해야 합니다.==

6-3)  역방향 DNS (REVERSE DNS RECORDS)

- 역방향 DNS records는 bootstrap, master, infra, worker node, api 및 api-int에 대해 구성합니다.
- RHEL CoreOS가 모든 node의 호스트 이름을 설정하는 방식이므로 역방향 DNS records가 중요합니다.
- 해당 설정을 하지 않는 경우에는 CoreOS 기동 시에 호스트 이름이 localhost로 설정되어 설치가 됩니다.

6-4) bind, bind-utils install

```bash
# yum install -y bind bind-utils
```

6-5) DNS Port 방화벽 해제

```bash
firewall-cmd --perm --add-port=53/tcp
firewall-cmd --perm --add-port=53/udp
firewall-cmd --add-service dns --zone=internal --perm 
firewall-cmd --reload
```

6-6) named.conf 수정 

> 파일 위치 :  /etc/named.conf

- 상위 DNS를 외부 네트워크로 나갈 수 있도록 설정하고, 나머지 노드들은 내부 DNS를 바라보게 설정을 하였습니다.

```bash
//
// named.conf
//
// Provided by Red Hat bind package to configure the ISC BIND named(8) DNS
// server as a caching only nameserver (as a localhost DNS resolver only).
//
// See /usr/share/doc/bind*/sample/ for example named configuration files.
//
// See the BIND Administrator's Reference Manual (ARM) for details about the
// configuration located in /usr/share/doc/bind-{version}/Bv9ARM.html

options {
        listen-on port 53 { any; };
        listen-on-v6 port 53 { none; };
        directory       "/var/named";
        dump-file       "/var/named/data/cache_dump.db";
        statistics-file "/var/named/data/named_stats.txt";
        memstatistics-file "/var/named/data/named_mem_stats.txt";
        recursing-file  "/var/named/data/named.recursing";
        secroots-file   "/var/named/data/named.secroots";
        allow-query     { any; };

        /*
         - If you are building an AUTHORITATIVE DNS server, do NOT enable recursion.
         - If you are building a RECURSIVE (caching) DNS server, you need to enable
           recursion.
         - If your recursive DNS server has a public IP address, you MUST enable access
           control to limit queries to your legitimate users. Failing to do so will
           cause your server to become part of large scale DNS amplification
           attacks. Implementing BCP38 within your network would greatly
           reduce such attack surface
        */
        recursion yes;

        forward only;
        forwarders {
                10.64.255.25;   // 상위 DNS 설정 (외부 네트워크를 위한)

        };

        dnssec-enable yes;
        dnssec-validation no;  // yes -> no로 변경

        /* Path to ISC DLV key */
        bindkeys-file "/etc/named.root.key";

        managed-keys-directory "/var/named/dynamic";

        pid-file "/run/named/named.pid";
        session-keyfile "/run/named/session.key";
};

logging {
        channel default_debug {
                file "data/named.run";
                severity dynamic;
        };
};

zone "." IN {
        type hint;
        file "named.ca";
};

include "/etc/named.rfc1912.zones";
include "/etc/named.root.key";
```

6-7)  named.rfc1912.zones 파일 수정 

> 파일 위치 :  /etc/named.rfc1912.zones

- named.rfc1912.zones의 맨 하단 부분에 추가할 도메인 zone 파일 정보를 입력 합니다.

```bash
// named.rfc1912.zones:
//
// Provided by Red Hat caching-nameserver package
//
// ISC BIND named zone configuration for zones recommended by
// RFC 1912 section 4.1 : localhost TLDs and address zones
// and http://www.ietf.org/internet-drafts/draft-ietf-dnsop-default-local-zones-02.txt
// (c)2007 R W Franks
//
// See /usr/share/doc/bind*/sample/ for example named configuration files.
//

zone "localhost.localdomain" IN {
        type master;
        file "named.localhost";
        allow-update { none; };
};

zone "localhost" IN {
        type master;
        file "named.localhost";
        allow-update { none; };
};

zone "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa" IN {
        type master;
        file "named.loopback";
        allow-update { none; };
};

zone "1.0.0.127.in-addr.arpa" IN {
        type master;
        file "named.loopback";
        allow-update { none; };
};

zone "0.in-addr.arpa" IN {
        type master;
        file "named.empty";
        allow-update { none; };
};

zone "skbb-poc.com" IN {
        type master;
        file "/var/named/skbb-poc.com.zone";
        allow-update { none; } ;
};

zone "168.76.10.in-addr.arpa" IN {
        type master;
        file "/var/named/168.76.10.in-addr.rev";
        allow-update { none; } ;
};
```

6-8) 정방향 zone 파일 생성

> 파일 위치 : /var/named/skbb-poc.com.zone

```bash
$TTL 1D
@   IN SOA  @ ns.skbb-poc.com. (
            4019954001  ; serial
            3H          ; refresh
            1H          ; retry
            1W          ; expiry
            1H )        ; minimum

@           IN NS       ns.skbb-poc.com.
@           IN A        10.76.168.40

; Ancillary services
lb.ocp4          IN A        10.76.168.40

; Bastion or Jumphost
bastion.ocp4     IN A        10.76.168.40
ns     IN A       10.76.168.40

; OCP Cluster
bootstrap.ocp4   IN A        10.76.168.41

master1.ocp4    IN A        10.76.168.42
master2.ocp4    IN A        10.76.168.43
master3.ocp4    IN A        10.76.168.44

infra1.ocp4     IN A        10.76.168.45
infra2.ocp4     IN A        10.76.168.46

worker1.ocp4    IN A        10.76.168.47
worker2.ocp4    IN A        10.76.168.48

etcd-0.ocp4      IN A        10.76.168.42
etcd-1.ocp4      IN A        10.76.168.43
etcd-2.ocp4      IN A        10.76.168.44

_etcd-server-ssl._tcp.ocp4.skbb-poc.com.    IN SRV  0   10  2380    etcd-0.ocp4.skbb-poc.com.
                                            IN SRV  0   10  2380    etcd-1.ocp4.skbb-poc.com.
                                            IN SRV  0   10  2380    etcd-2.ocp4.skbb-poc.com.

api.ocp4         IN A    10.76.168.40  ; external LB interface
api-int.ocp4     IN A    10.76.168.40  ; internal LB interface
apps.ocp4        IN A    10.76.168.40
*.apps.ocp4      IN A    10.76.168.40
```

6-9) 역방향 zone 파일 생성

> 파일 위치 : /var/named/168.76.10.in-addr.rev

```bash
$TTL    86400
@       IN      SOA   skbb-poc.com. ns.skbb-poc.com. (
                      179332     ; Serial
                      3H         ; Refresh
                      1H         ; Retry
                      1W         ; Expire
                      1H )       ; Minimum

@      IN NS   ns.
40     IN PTR  ns.
40     IN PTR  bastion.ocp4.skbb-poc.com.
41     IN PTR  bootstrap.ocp4.skbb-poc.com.
42     IN PTR  master1.ocp4.skbb-poc.com.
43     IN PTR  master2.ocp4.skbb-poc.com.
44     IN PTR  master3.ocp4.skbb-poc.com.
45     IN PTR  infra1.ocp4.skbb-poc.com.
46     IN PTR  infra2.ocp4.skbb-poc.com.
47     IN PTR  worker1.ocp4.skbb-poc.com.
48     IN PTR  worker2.ocp4.skbb-poc.com.
40     IN PTR  api.ocp4.skbb-poc.com.
40     IN PTR  api-int.ocp4.skbb-poc.com.
```

> RHCoreOS 호스트 이름 설정 관련하여 역방향 DNS zone 설정이 중요합니다.

6-10) DNS 서비스 등록 및 시작, 상태 확인

```bash
# systemctl enable named
# systemctl start named
# systemctl status named 
```

6-11) 정방향 DNS Resovling 확인

```bash
[root@bastion ~]# nslookup bootstrap.ocp4.skbb-poc.com
Server:         10.76.168.40
Address:        10.76.168.40#53

Name:   bootstrap.ocp4.skbb-poc.com
Address: 10.76.168.41

[root@bastion ~]# nslookup worker1.ocp4.skbb-poc.com
Server:         10.76.168.40
Address:        10.76.168.40#53

Name:   worker1.ocp4.skbb-poc.com
Address: 10.76.168.47

--- 생략 ---
```

- 외부로도 DNS lookup이 되는지 확인

  > 예시로 google.com과 quay.io로 테스트 하였습니다.

  ```bash
  [root@bastion ~]# nslookup google.com
  Server:         10.76.168.40
  Address:        10.76.168.40#53
  
  Non-authoritative answer:
  Name:   google.com
  Address: 172.217.26.14
  Name:   google.com
  Address: 2404:6800:4004:809::200e
  
  [root@bastion ~]# nslookup quay.io
  Server:         10.76.168.40
  Address:        10.76.168.40#53
  
  Non-authoritative answer:
  Name:   quay.io
  Address: 107.23.216.34
  Name:   quay.io
  Address: 52.21.62.45
  Name:   quay.io
  Address: 34.198.225.139
  Name:   quay.io
  Address: 18.214.53.124
  Name:   quay.io
  Address: 52.72.254.43
  Name:   quay.io
  Address: 34.202.115.40
  
  --- 생략 ---
  ```

6-12) 역방향 DNS Resolving 확인

```bash
[root@bastion ~]# dig -x 10.76.168.47 +short
worker1.ocp4.skbb-poc.com.
[root@bastion ~]# dig -x 10.76.168.40 +short
api.ocp4.skbb-poc.com.
bastion.ocp4.skbb-poc.com.
api-int.ocp4.skbb-poc.com.
ns.

--- 생략 ---
```



### 7. Load Balancer 구성 (Haproxy)

> 내부와 외부 API와 OpenShift 라우터를 forntend하기 위해서는 Load Balancer가 필요합니다. 

7-1) haproxy install

```bash
# yum install -y haproxy
```

7-2) haproxy 설정

> 파일 위치 : /etc/haproxy/haproxy.cfg 

```bash
#---------------------------------------------------------------------
# Example configuration for a possible web application.  See the
# full configuration options online.
#
#   http://haproxy.1wt.eu/download/1.4/doc/configuration.txt
#
#---------------------------------------------------------------------

#---------------------------------------------------------------------
# Global settings
#---------------------------------------------------------------------
global
    # to have these messages end up in /var/log/haproxy.log you will
    # need to:
    #
    # 1) configure syslog to accept network log events.  This is done
    #    by adding the '-r' option to the SYSLOGD_OPTIONS in
    #    /etc/sysconfig/syslog
    #
    # 2) configure local2 events to go to the /var/log/haproxy.log
    #   file. A line like the following can be added to
    #   /etc/sysconfig/syslog
    #
    #    local2.*                       /var/log/haproxy.log
    #
    log         127.0.0.1 local2

    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     4000
    user        haproxy
    group       haproxy
    daemon

    # turn on stats unix socket
    stats socket /var/lib/haproxy/stats

#---------------------------------------------------------------------
# common defaults that all the 'listen' and 'backend' sections will
# use if not designated in their block
#---------------------------------------------------------------------
defaults
    mode                    http
    log                     global
    option                  httplog
    option                  dontlognull
    option http-server-close
    option forwardfor       except 127.0.0.0/8
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m
    timeout server          1m
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 4000

#---------------------------------------------------------------------
# static backend for serving up images, stylesheets and such
#---------------------------------------------------------------------
backend static
    balance     roundrobin
    server      static 127.0.0.1:4441 check

#---------------------------------------------------------------------
# round robin balancing between the various backends
#---------------------------------------------------------------------
frontend openshift-api-server
    bind *:6443
    default_backend openshift-api-server
    mode tcp
    option tcplog

backend openshift-api-server
    balance source
    mode tcp
    server bootstrap 10.76.168.41:6443 check
    server master1 10.76.168.42:6443 check
    server master2 10.76.168.43:6443 check
    server master3 10.76.168.44:6443 check

frontend machine-config-server
    bind *:22623
    default_backend machine-config-server
    mode tcp
    option tcplog

backend machine-config-server
    balance source
    mode tcp
    server bootstrap 10.76.168.41:22623 check
    server master1 10.76.168.42:22623 check
    server master2 10.76.168.43:22623 check
    server master3 10.76.168.44:22623 check

frontend ingress-http
    bind *:80
    default_backend ingress-http
    mode tcp
    option tcplog

backend ingress-http
    balance source
    mode tcp
    server infra1 10.76.168.45:80 check
    server infra2 10.76.168.46:80 check

frontend ingress-https
    bind *:443
    default_backend ingress-https
    mode tcp
    option tcplog

backend ingress-https
    balance source
    mode tcp
    server infra1 10.76.168.45:443 check
    server infra2 10.76.168.46:443 check
```

7-3) 방화벽 해제

```bash
* SELINUX 설정 (HTTP Listener로 정의되지 않은 Port에 대해 SELINUX 권한 허용)
semanage port -a -t http_port_t -p tcp 6443
semanage port -a -t http_port_t -p tcp 22623
```

```bash
firewall-cmd --permanent --add-port=22623/tcp
firewall-cmd --permanent --add-port=6443/tcp
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=http

firewall-cmd --add-port 22623/tcp --zone=internal --perm
firewall-cmd --add-port 6443/tcp --zone=internal --perm  
firewall-cmd --add-service https --zone=internal --perm  
firewall-cmd --add-service http --zone=internal --perm  
 
firewall-cmd --add-port 6443/tcp --zone=external --perm  
firewall-cmd --add-service https --zone=external --perm  
firewall-cmd --add-service http --zone=external --perm  
firewall-cmd --complete-reload
```

7-4) firewalld port 확인

```bash
[root@bastion ~]# firewall-cmd --list-all
public (active)
  target: default
  icmp-block-inversion: no
  interfaces: ens192
  sources:
  services: ssh dhcpv6-client http https
  ports: 8080/tcp 5000/tcp 53/tcp 53/udp 22623/tcp 6443/tcp
  protocols:
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
```

7-5) haproxy 서비스 등록 및 시작

```bash
systemctl enable haproxy 
systemctl start haproxy
systemctl status haproxy
```



### 8. ssh-key 생성

> 설치 실행 할 cluster install node에서 ssh key 생성과 ssh-agent에 key 등록 합니다.

```bash
[root@bastion ~]# ssh-keygen -t rsa -b 4096
Generating public/private rsa key pair.
Enter file in which to save the key (/root/.ssh/id_rsa): 
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /root/.ssh/id_rsa.
Your public key has been saved in /root/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:vdqvFVLKMSRQWSmdl7TNSPOULjv1Dyk3nJjWJLn2HJI root@bastion.ocp4.example.com
The key's randomart image is:
+---[RSA 4096]----+
|      .oo+o++... |
|        oo+.oO.  |
|         .o.+o+  |
|         o =+ +  |
|        S = .& + |
|           oE.X .|
|          .o.B +.|
|         o .  o .|
|        . oo.    |
+----[SHA256]-----+

[root@bastion ~]# eval "$(ssh-agent -s)"
Agent pid 23173
[root@bastion ~]# ssh-add ~/.ssh/id_rsa
Identity added: /root/.ssh/id_rsa (/root/.ssh/id_rsa)
```



### 9. install 사전 확인

9-1) ip 확인

```bash
[root@bastion ~]# ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: ens192: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:95:20:32 brd ff:ff:ff:ff:ff:ff
    inet 10.76.168.40/23 brd 10.76.169.255 scope global noprefixroute ens192
       valid_lft forever preferred_lft forever
    inet6 2620:52:0:4ca8:250:56ff:fe95:2032/64 scope global mngtmpaddr dynamic
       valid_lft 2591585sec preferred_lft 604385sec
    inet6 fe80::250:56ff:fe95:2032/64 scope link
       valid_lft forever preferred_lft forever
```

9-2)  DNS 서비스 확인

```bash
# systemctl status named
```

9-3) haproxy 서비스 확인

```bash
# systemctl status haproxy
```



### 10. install-config.yaml 생성

10-1) install에 필요한 파일 다운 로드

- wget이 없는 경우 설치 후 진행 

  ```bash
  # yum install -y wget
  ```
  
  - /var/www/html/ocp 디렉토리에서 명령어 실행
  
    ```bash
      wget https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.3/4.3.0/rhcos-4.3.0-x86_64-installer.iso
      wget https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.3/4.3.0/rhcos-4.3.0-x86_64-metal.raw.gz
      wget https://mirror.openshift.com/pub/openshift-v4/clients/ocp/4.3.0/openshift-install-linux-4.3.0.tar.gz
      wget https://mirror.openshift.com/pub/openshift-v4/clients/ocp/4.3.0/openshift-client-linux-4.3.0.tar.gz
    ```
  
- rhcos-4.3.0-x86_64-metal.raw.gz 파일의 경우 설치시 편의를 위해서 해당 파일 이름을 다음과 같이 변경

  ```bash
  # mv rhcos-4.3.0-x86_64-metal.raw.gz bios.raw.gz
  ```

10-2) openshift-install, openshift-client install 파일을 압축 해제 

```bash
tar -xzf /var/www/html/ocp/openshift-client-linux-4.3.0.tar.gz -C /usr/local/bin/
tar -xzf /var/www/html/ocp/openshift-install-linux-4.3.0.tar.gz -C /usr/local/bin/
```

- 압축 해제 후 oc command가 정상적으로 수행 되는지 확인합니다.

  ```bash
  [root@bastion ~]# oc
  OpenShift Client
  
  This client helps you develop, build, deploy, and run your applications on any
  OpenShift or Kubernetes cluster. It also includes the administrative
  commands for managing a cluster under the 'adm' subcommand.
  
  To familiarize yourself with OpenShift, login to your cluster and try creating a sample application:
  
      oc login mycluster.mycompany.com
      oc new-project my-example
      oc new-app django-psql-example
      oc logs -f bc/django-psql-example
  
  --- 생략 ---
  ```

10-3) install-config.yaml 생성

> OpenShift를 설치할 디렉토리를 생성한 후 install-config.yaml을 작성합니다.
>
> 본 가이드의 설치 디렉토리는 /var/www/html/ocp 입니다.
>
> ==install-config.yaml은 OpenShift 4.3 Cluster 구성을 위한 ignition 파일을 생성하는데 필요하며, 해당 파일은 ignition 파일을 생성하고 삭제되므로 반드시 백업을 한 후 작업을 하는 것이 좋습니다.==

- [x] ==생성된 ignition config 파일은 24시간 동안 유효한 인증서를 포함하고 있어서 반드시 24시간 내에 OpenShift Cluster 구성을 완료해야 합니다.==

- [x] ==또한, 설치가 완료된 이후에도 24시간 내에 master node는 종료하면 안 됩니다.==

- [x] 24시간 이후에 master node의 인증서가 갱신 되기 때문입니다. 

  - vSphere install-config.yaml Sample 

    ```yaml
    apiVersion: v1
    baseDomain: example.com 
    compute:
    - hyperthreading: Enabled   
      name: worker
      replicas: 0 
    controlPlane:
      hyperthreading: Enabled   
      name: master
      replicas: 3 
    metadata:
      name: test 
    platform:
      vsphere:
        vcenter: your.vcenter.server 
        username: username 
        password: password 
        datacenter: datacenter 
        defaultDatastore: datastore 
    fips: false 
    pullSecret: '{"auths": ...}' 
    sshKey: 'ssh-ed25519 AAAA...' 
    ```

  - install-config.yaml (vShpere)

    ```bash
    apiVersion: v1
    baseDomain: skbb-poc.com
    compute:
    - hyperthreading: Enabled
      name: worker
      replicas: 0
    controlPlane:
      hyperthreading: Enabled
      name: master
      replicas: 3
    metadata:
      name: ocp4
    platform:
      vsphere:
        vcenter: ${vcenter} // 실제 값 입력 또는 환경 변수로 처리 가능
        username: ${username} // 실제 값 입력 또는 환경 변수로 처리 가능
        password: ${password} // 실제 값 입력 또는 환경 변수로 처리 가능
        datacenter: ${Datacenter} // 실제 값 입력 또는 환경 변수로 처리 가능
        defaultDatastore: ${defaultDatastore} // 실제 값 입력 또는 환경 변수로 처리 가능
    pullSecret: '{"auths":{"cloud.openshift.com":{"auth":"b3BlbnNoaWZ0LXJlbGVhc2UtZGV2K3JobnN1cHBvcnRoeW91MXNhOW9md2d2cTVzNnpiZWc1cHBwMzNzdnBuOlZERUpCT01GSkNXUUcySk0yWEFGNDJYS0NXUUpXOUVPV1o4MTI3Nk45UElVT0YzUVRLU1hPTUEwMVMySUpXWEQ=","email":"hyou@redhat.com"},"quay.io":{"auth":"b3BlbnNoaWZ0LXJlbGVhc2UtZGV2K3JobnN1cHBvcnRoeW91MXNhOW9md2d2cTVzNnpiZWc1cHBwMzNzdnBuOlZERUpCT01GSkNXUUcySk0yWEFGNDJYS0NXUUpXOUVPV1o4MTI3Nk45UElVT0YzUVRLU1hPTUEwMVMySUpXWEQ=","email":"hyou@redhat.com"},"registry.connect.redhat.com":{"auth":"NTI4MzgyMTF8dWhjLTFTYTlPRldHdlE1czZ6YkVnNVBwcDMzU1ZQTjpleUpoYkdjaU9pSlNVelV4TWlKOS5leUp6ZFdJaU9pSTBZek5sTVRJMFpUQmpZbU0wTWpKbFlUSXhObVkyT1dNMk1qQTROR1EyWWlKOS5vVEtoLXh3dUVtTUx1by12T0NmTHRwbkprQlBTVm1xdUtZUERYT3lndXdmMHVfWU1VTWlhcDU5bzR5LVFhYmthUl9JVThWaTFqeHo0QmpTOXFiNGk4S2NNYzVDb0c4SDJiY0VnV0JWNDFXcTNScGhfSzA1WmdPWDRhaFJRU1NIN2NGYUt5d3l0eW9LWU9tREVZTkZybGdrZjhpUnF3ZjN0WnpFYTU3dWdOTTQ1ajZYUzlqZHhYR2Jab2pGWGdsUHZ5T1pHMjI3eHZoMkR6bk5WdmYwMVE3MXBlcV9aU3VEYmpYYkFKQ3E3LURIMnhaYkMzZXBMOHBnN1R4ZDlrSFZuek9WSHJtRnQzUDVyeEVQTHhEcUlpQVlUQmE5LXJwOWpwdHl5a1VoYW1vbEhSYW50MkhEZ0Vac0lidDVjcFg4YTEtYVNsT2NaQUF2R1FRam1ZV1FDTzRZRFhpWXlINUNVMWY1ZnFiUkxva0NpeXUtVHNDTE9TdU9qRnN6Z3VYbzIzaU5QUVlDMmtfWWFJWENBa1VVYnVIQm5LcUhPQXVsa1NvRk1uanlzU0l6SmZWMXdvcFpMM050bFVSVnlsek5fbVJpWVJJcmxlZHRCN01Vdy1Tb2drMlpSLXUyREFHTEIxSmd6ZFQteF9qZnRpWVpZc0lETUk2VWlGb0J3ZjVLaWZycXVTYklqUWRPdC01MEw5VjQ3ZGZ6M3pxcDd0OUNfSEFzLTZBbVNvVHdETW9McWJVTW5VejlHbVdEdk15eHlCZ1U5NTlUX2RaTmhKV3pQUHlRR2JuME9heXRxNEpnYjBVc3JEdTItY2RwanBLQ2NmRnZBal93RE9odlkxYkVNSDlXWkR4WThyY3NVcGJ2MGhLNjJrYUctN0p6RGdVQjFuZGRWOWYyYmVHaw==","email":"hyou@redhat.com"},"registry.redhat.io":{"auth":"NTI4MzgyMTF8dWhjLTFTYTlPRldHdlE1czZ6YkVnNVBwcDMzU1ZQTjpleUpoYkdjaU9pSlNVelV4TWlKOS5leUp6ZFdJaU9pSTBZek5sTVRJMFpUQmpZbU0wTWpKbFlUSXhObVkyT1dNMk1qQTROR1EyWWlKOS5vVEtoLXh3dUVtTUx1by12T0NmTHRwbkprQlBTVm1xdUtZUERYT3lndXdmMHVfWU1VTWlhcDU5bzR5LVFhYmthUl9JVThWaTFqeHo0QmpTOXFiNGk4S2NNYzVDb0c4SDJiY0VnV0JWNDFXcTNScGhfSzA1WmdPWDRhaFJRU1NIN2NGYUt5d3l0eW9LWU9tREVZTkZybGdrZjhpUnF3ZjN0WnpFYTU3dWdOTTQ1ajZYUzlqZHhYR2Jab2pGWGdsUHZ5T1pHMjI3eHZoMkR6bk5WdmYwMVE3MXBlcV9aU3VEYmpYYkFKQ3E3LURIMnhaYkMzZXBMOHBnN1R4ZDlrSFZuek9WSHJtRnQzUDVyeEVQTHhEcUlpQVlUQmE5LXJwOWpwdHl5a1VoYW1vbEhSYW50MkhEZ0Vac0lidDVjcFg4YTEtYVNsT2NaQUF2R1FRam1ZV1FDTzRZRFhpWXlINUNVMWY1ZnFiUkxva0NpeXUtVHNDTE9TdU9qRnN6Z3VYbzIzaU5QUVlDMmtfWWFJWENBa1VVYnVIQm5LcUhPQXVsa1NvRk1uanlzU0l6SmZWMXdvcFpMM050bFVSVnlsek5fbVJpWVJJcmxlZHRCN01Vdy1Tb2drMlpSLXUyREFHTEIxSmd6ZFQteF9qZnRpWVpZc0lETUk2VWlGb0J3ZjVLaWZycXVTYklqUWRPdC01MEw5VjQ3ZGZ6M3pxcDd0OUNfSEFzLTZBbVNvVHdETW9McWJVTW5VejlHbVdEdk15eHlCZ1U5NTlUX2RaTmhKV3pQUHlRR2JuME9heXRxNEpnYjBVc3JEdTItY2RwanBLQ2NmRnZBal93RE9odlkxYkVNSDlXWkR4WThyY3NVcGJ2MGhLNjJrYUctN0p6RGdVQjFuZGRWOWYyYmVHaw==","email":"hyou@redhat.com"}}}'
    sshKey: 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCukz6D55UxCJhxd3guY90PwM3citKFzx6VGM12ZY0jdKUyDu9YY22HmrogO5srBd9EJnhT+jcmLjWykbGopxc8WdFFJ3da9Q7wdBKIoJBqoo2hlkuUnmS/8YeXxxoUd9kfl9+OicEda1XrzP98IsU0ZoQXJIblVqOLzbQpIAsIIffMzCDNlV/8JIwp0bCAs+iGMhUerKH8vtT1DO00LQ45m7uaYOETV6KW2/y0HgUg8B+1ed9WlFfZxvZCKJGgwnfP1Ky0UthIxsGGprt3WexLAqafwhgXCEfOjP6301hZLH5ExMp8uQe6SIZ6L3Gwr32Fds18a/SOYIcr760dtBPVzilP57CfHQ356kVi65gO9lD5j5s/KSA41BPakfEuOQHlI2D9/9kuiE/9E88ppeIQ9JvBlX4lP/mDH8tbzYGd1XKqpAE3wPsUmnvBtuEN5VTEsWMkzcf0SqeWpRh3096nHNp+qY8rwUdbpexR2Tr04hIlK+l7XFcaJAxbE3UIAvacMdLuLgAfEPmyBS7kDedC3p52krxWwTr6g6zbUa2GyFzMbvKusD1rSZ9RM394cxbPmeuHBC7DBCht8S4mPnnZaY/BR74gzjvE56GLDSrtScGJu1fI29BBhubUV9ijB1VPFiywAEzR4W6SzFC8TfIZRtMm/daaR4x5XAoa908uDw== root@bastion.ocp4.skbb-poc.com'
    ```

    - baseDomain : skbb-poc.com (도메인 이름)
    - name : ocp4 (Cluster 이름)
    - pullSecret: cloud.openshift.com에서 다운 받은 pull-secret 파일 내용 입력
    - sshKey: 위에서 생성한 ssh-key의 /root/.ssh/id_rsa.pub 내용 입력



### 11. ignition 파일 생성

11-1) install-config.yaml 생성

- [x] ==생성된 ignition config 파일은 24시간 동안 유효한 인증서를 포함하고 있어서 반드시 24시간 내에 OpenShift Cluster 구성을 완료해야 합니다.==
- [x] ==ingnition 파일을 생성하면 install-config.yaml 파일은 삭제되므로 작업 전에 백업을 합니다.==

```bash
[root@bastion ocp]# cp install-config.yaml install-config.yaml_bak
```

11-2)  Kubernetest manifests file 생성

```bash
[root@bastion ~]# openshift-install create manifests --dir=/var/www/html/ocp
INFO Consuming "Install Config" from target directory
WARNING Making control-plane schedulable by setting MastersSchedulable to true for Scheduler cluster settings
```

- /var/www/html/ocp/manifests/cluster-scheduler-02-config.yml 에서  mastersSchedulable  값을 '==true-> false==로' 변경 후 저장

  ```bash
  [root@bastion ocp]# cd manifests/
  [root@bastion manifests]# sed -i 's/mastersSchedulable: true/mastersSchedulable: false/g' cluster-scheduler-02-config.yml
  [root@bastion manifests]# cat cluster-scheduler-02-config.yml
  apiVersion: config.openshift.io/v1
  kind: Scheduler
  metadata:
    creationTimestamp: null
    name: cluster
  spec:
    mastersSchedulable: false
    policy:
      name: ""
status: {}
  ```
  
  > 현재 Kubernetes 제한으로 인해 control-plane 머신에서 실행되는 router pod에 수신 로드 밸런서가 도달 할 수 없습니다. 향후 minor 버전의 OpenShift Container Platform에서는이 단계가 필요하지 않을 수 있습니다.
  
  > 설치 관리자가 master를 예약 할 수 있음을 알려줍니다. 설치를 위해 master를 예약 할 수 없도록 설정해야 합니다.

11-3) Modifying advanced network configuration parameters (vSphere만 해당)

> <installation_directory>/manifests/ directory 에 cluster-network-03-config.yml 파일 생성
>
> 해당 가이드의 installation_directory=/var/www/html/ocp

```yaml
apiVersion: operator.openshift.io/v1
kind: Network
metadata:
  name: cluster
spec:
  clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
  serviceNetwork:
  - 10.76.168.0/24   // service IP 대역 맞춤
  defaultNetwork:
    type: OpenShiftSDN
    openshiftSDNConfig:
      mode: NetworkPolicy
      mtu: 1450
      vxlanPort: 4789
```

> 디렉토리 내에 파일 확인 

```bash
ls <installation_directory>/manifests/cluster-network-*
```

```bash
[root@bastion manifests]# ls /var/www/html/ocp/manifests/cluster-network-*
/var/www/html/ocp/manifests/cluster-network-01-crd.yml  /var/www/html/ocp/manifests/cluster-network-02-config.yml  /var/www/html/ocp/manifests/cluster-network-03-config.yml
```

> ==manifests 디렉토리 및 해당 파일은 ignition 생성 명령어를 실행할 경우 디렉토리 내에서 사라집니다.==

11-4)  ignition config 파일 생성

- ignition config 파일 생성

```bash
[root@bastion ocp]# openshift-install create ignition-configs --dir=/var/www/html/ocp
INFO Consuming "Install Config" from target directory
INFO Consuming "Master Machines" from target directory
INFO Consuming "Common Manifests" from target directory
INFO Consuming "Worker Machines" from target directory
INFO Consuming "Openshift Manifests" from target directory
```

> 아래와 같이 디렉토리 및 파일이 생성됩니다.

```bash
├── auth
│   ├── kubeadmin-password
│   └── kubeconfig
├── bootstrap.ign
├── master.ign
├── metadata.json
└── worker.ign
```

static ip를 위한 ignition 파일 생성

- 원활한 작업을 위해 ignition 디렉토리를 생성하여 해당 디렉토리안에 각 node의 별도 ignition 파일을 생성합니다.

  ```bash
  [root@bastion ocp]# mkdir ign
  [root@bastion ocp]# ls -rlt
  total 308
  -rw-r--r--. 1 root root   3875 Feb 11 08:18 install-config.yaml_bak
  drwxr-x---. 2 root root     50 Feb 11 08:19 auth
  -rw-r-----. 1 root root   1821 Feb 11 08:19 master.ign
  -rw-r-----. 1 root root   1821 Feb 11 08:19 worker.ign
  -rw-r-----. 1 root root 297360 Feb 11 08:19 bootstrap.ign
  -rw-r-----. 1 root root     94 Feb 11 08:19 metadata.json
  drwxr-xr-x. 2 root root      6 Feb 11 08:21 ign  // 디렉토리 생성 확인
  ```

- 기본 ignition 파일로 각 node의 별도 ignition 파일 복사 및 이동

  - 파일 복사
  
  ```bash
  cp bootstrap.ign poc_bootstrap.ign
  cp master.ign poc_master1.ign
  cp master.ign poc_master2.ign
  cp master.ign poc_master3.ign
  cp worker.ign poc_infra1.ign
  cp worker.ign poc_infra2.ign
  cp worker.ign poc_worker1.ign
  cp worker.ign poc_worker2.ign
  ```
  
  - 파일 이동
  
  ```bash
  mv poc_bootstrap.ign ./ign
  mv poc_master1.ign ./ign
  mv poc_master2.ign ./ign
  mv poc_master3.ign ./ign
  mv poc_infra1.ign ./ign
  mv poc_infra2.ign ./ign
  mv poc_worker1.ign ./ign
  mv poc_worker2.ign ./ign
  ```

11-4) 개별 node ignition 구성을 위한 network script 생성

- ==network script 작성 시 DNS1은 내부 DNS인 bastion 서버를 입력 합니다.==

- bootstrap (ex. boot-net.txt)

  > bootstrap network-script 내용 작성
  
  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.41
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

- master1 (ex. master1-net.txt)

  > master1 network-script 내용 작성

  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.42
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

- master2 (ex. master2-net.txt)

  > master2 network-script 내용 작성

  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.43
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

- master3 (ex. master3-net.txt)

  > master3 network-script 내용 작성

  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.44
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

- infra1 (ex. infra1-net.txt)

  > infra1 network-script 내용 작성

  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.45
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

- infra2 (ex. infra2-net.txt)

  > infra2 network-script 내용 작성

  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.46
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

- worker1 (ex. worker1-net.txt)

  > worker1 network-script 내용 작성

  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.47
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

- worker2 (ex. worker2-net.txt)

  > worker2 network-script 내용 작성

  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.48
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

11-5) network-script를 base64 인코딩

- 11-4)에서 작성한 내용을 실제 설치에 필요한 ignition에 추가 하기 위해 base64 인코딩 작업을 합니다.

- script로 실행하여 출력된 부분을 사용하는 편집기에 복사해 놓습니다.

  ```bash
  [root@bastion ~]# for list in `ls -1 *.txt`; do echo $list ; cat $list | base64 -w0 ; echo \ ; done
  
  boot-net.txt
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQxCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  infra1-net.txt
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQ1Ck5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  infra2-net.txt
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQ2Ck5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  master1-net.txt
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQyCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  master2-net.txt
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQzCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  master3-net.txt
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQ0Ck5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  worker1-net.txt
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQ3Ck5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  worker2-net.txt
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQ4Ck5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  ```

11-6) ignition 파일 수정

> ignition 파일 수정 전에 jq를 이용하여 yaml 형태로 파일 변환

- jq가 존재하지 않는 경우 패키지 설치 필요

  ```bash
  # yum install -y jq
  ```

- jq를 이용하여 11-5) 에서 ign 디렉토리로 옮긴 파일을 아래 명령어로 yaml 형태로 변환 합니다.

  - 수행 위치 : /var/www/html/ocp/ign

    ```bash
    for list in `ls -1 *.ign`; do echo $list ; cat $list | jq > jq-$list; done
    ```

- 변환한 파일에 각 노드의 static ip 설정을 위해 아래 내용을 참고하여 위에서 생성한 파일을 편집합니다.

  (e.g : /var/www/html/ocp/ign/jq-poc_bootstrap.ign )

- example 첨부

  ```bash
  "storage": {
  "files": [
  {
  "contents": {
    "source": "data:text/plain;charset=utf-8,worker-0.ocp4.example.com",
    "verification": {}
  },
  "filesystem": "root",
  "group": {},
  "mode": 420,
  "path": "/etc/hostname",
  "user": {}
  },
  {
  "contents": {
    "source": "data:text/plain;charset=utf-8;base64,<BASE64_ETHERNET_OUTPUT>",
    "verification": {}
  },
  "filesystem": "root",
  "path": "/etc/sysconfig/network-scripts/ifcfg-INTERFACE_NAME",
  "mode": 420,
  "user": {}
  }
  ]
  },
  ```

- bootstrap 

- 파일 위치 : /var/www/html/ocp/ign/jq-poc_bootstrap.ign

  > 위의 예시를 참고하여 bootstrap 용도로 작성한 것 입니다.

  ```yaml
  "storage": {
  "files": [
  {
  "contents": {
    "source": "data:text/plain;charset=utf-8,bootstrap.ocp4.skbb-poc.com",
    "verification": {}
  },
  "filesystem": "root",
  "group": {},
  "mode": 420,
  "path": "/etc/hostname",
  "user": {}
  },
  {
  "contents": {
    "source": "data:text/plain;charset=utf-8;base64,VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQyCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==",
    "verification": {}
  },
  "filesystem": "root",
  "path": "/etc/sysconfig/network-scripts/ifcfg-ens192",
  "mode": 420,
  "user": {}
  }
  ]
  },
  ```

  > storage 섹션 아래에 위의 내용을 추가합니다.

- 실제 파일 예시

  ```bash
  {"ignition":{"config":{},"security":{"tls":{}},"timeouts":{},"version":"2.2.0"},"networkd":{},"passwd":{"users":[{"name":"core","sshAuthorizedKeys":["ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCukz6D55UxCJhxd3guY90PwM3citKFzx6VGM12ZY0jdKUyDu9YY22HmrogO5srBd9EJnhT+jcmLjWykbGopxc8WdFFJ3da9Q7wdBKIoJBqoo2hlkuUnmS/8YeXxxoUd9kfl9+OicEda1XrzP98IsU0ZoQXJIblVqOLzbQpIAsIIffMzCDNlV/8JIwp0bCAs+iGMhUerKH8vtT1DO00LQ45m7uaYOETV6KW2/y0HgUg8B+1ed9WlFfZxvZCKJGgwnfP1Ky0UthIxsGGprt3WexLAqafwhgXCEfOjP6301hZLH5ExMp8uQe6SIZ6L3Gwr32Fds18a/SOYIcr760dtBPVzilP57CfHQ356kVi65gO9lD5j5s/KSA41BPakfEuOQHlI2D9/9kuiE/9E88ppeIQ9JvBlX4lP/mDH8tbzYGd1XKqpAE3wPsUmnvBtuEN5VTEsWMkzcf0SqeWpRh3096nHNp+qY8rwUdbpexR2Tr04hIlK+l7XFcaJAxbE3UIAvacMdLuLgAfEPmyBS7kDedC3p52krxWwTr6g6zbUa2GyFzMbvKusD1rSZ9RM394cxbPmeuHBC7DBCht8S4mPnnZaY/BR74gzjvE56GLDSrtScGJu1fI29BBhubUV9ijB1VPFiywAEzR4W6SzFC8TfIZRtMm/daaR4x5XAoa908uDw== root@bastion.ocp4.skbb-poc.com"]}]},"storage":{"files":[{"contents":{"source":"data:text/plain;charset=utf-8,bootstrap.ocp4.skbb-poc.com","verification":{}},"filesystem":"root","group":{},"mode":420,"path":"/etc/hostname","user":{}},{"contents":{"source":"data:text/plain;charset=utf-8;base64,VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQyCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==","verification":{}},"filesystem":"root","path":"/etc/sysconfig/network-scripts/ifcfg-ens192","mode":420,"user":{}},
  
  --- 생략 ----
  
  
  ```

  > 추가된 부분은 {"contents"}: ---- "mode":420,"user":{}}, 부분까지 입니다.
  >
  > ==yaml 형식으로 depth가 맞다면 한줄로 변환하지 안하도 됩니다.==

- master, infra, worker의 경우 형식이 비슷하므로 한 가지 예시만 작성 하였습니다.

  - master

    > master의 경우에도 storage {} 섹션 아래 해당 내용을 추가합니다.

    ```bash
    "files": [
    {
    "contents": {
      "source": "data:text/plain;charset=utf-8,master1.ocp4.skbb-poc.com",
      "verification": {}
    },
    "filesystem": "root",
    "group": {},
    "mode": 420,
    "path": "/etc/hostname",
    "user": {}
    },
    {
    "contents": {
      "source": "data:text/plain;charset=utf-8;base64,VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQxCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==",
      "verification": {}
    },
    "filesystem": "root",
    "path": "/etc/sysconfig/network-scripts/ifcfg-ens192",
    "mode": 420,
    "user": {}
    }
    ]
    ```

- 수정한 ignition파일이 yaml 형식이면 그대로 사용해도 되고, 한줄로 변경해서 사용해도 됩니다.

- 실제 파일 예시 

  ``` bash
  {"ignition":{"config":{"append":[{"source":"https://api-int.ocp4.skbb-poc.com:22623/config/master","verification":{}}]},"security":{"tls":{"certificateAuthorities":[{"source":"data:text/plain;charset=utf-8;base64,LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURFRENDQWZpZ0F3SUJBZ0lJSGEyR2hZejg5dGd3RFFZSktvWklodmNOQVFFTEJRQXdKakVTTUJBR0ExVUUKQ3hNSmIzQmxibk5vYVdaME1SQXdEZ1lEVlFRREV3ZHliMjkwTFdOaE1CNFhEVEl3TURJeE1qRTNORGswT0ZvWApEVE13TURJd09URTNORGswT0Zvd0pqRVNNQkFHQTFVRUN4TUpiM0JsYm5Ob2FXWjBNUkF3RGdZRFZRUURFd2R5CmIyOTBMV05oTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUE2UUNIYSsyZksxZm4KYy94MnVwcW9lYi9DUlpNaUg0ZWp4YzNNaVBjWFIvSHBHbHIxZWkvNmZIMXdMQ3VBbXZOSWNYQ2tENDBaM2h6VApCRE1OcERveCtPeDYrUzcvcE1BS2ZTS3M3Qk9EeVN2M1E3c0tMQmlUd3Q3dHdvVS9vRXFEU1g2MXMvREdWNDhWCi92d1JLTnVWU1U5bXpwc2YySkJITkhPalFSU2RlWUhVa2JTaVVEY2h6T1JVc2tITjRiWk93endmYUJBK1hteGQKemVsbWpIOVFsbVNPbU5vSlNmbUVaVHNkZ1YvNmFETXFTcjlYRTZvdUl0NldHWjZnaXpQNzRpZ3AyTjQxTzdmVApzTUQvTU16ZUFuRlorM0tXZEU1eWxncXJFeDFQZjFHMlZwZkhualFsZVp6SUMyZnVFZzNEdkdLUmlWMXdqVkpRClpRNVk2eWV4VFFJREFRQUJvMEl3UURBT0JnTlZIUThCQWY4RUJBTUNBcVF3RHdZRFZSMFRBUUgvQkFVd0F3RUIKL3pBZEJnTlZIUTRFRmdRVTVTbk5JeFNpdXV3Y00rNk5JWDBLakc2b0R6TXdEUVlKS29aSWh2Y05BUUVMQlFBRApnZ0VCQUg3WFQ4R25XbXBlZDIvYnErL2d5UVZoMDBIMy9nU09YRWUwdU9jWWZscWQ4Ri9iektJOU45bXNSZTZqCi9kbFMxK2VvQ05mWDI2WWZIUzI1NkRITTlUd1QyMEd6dEJuakF3aFZsRm10dGxObmwvdWxwTHdnNThMUDBjQnUKRTVTaTY5U0diZVA1QjFoY3hzalhrSW1TTkRLR1N0MmR0UjRydGdOLzFYbitYWFlRaUdUTzcveGFVMG50cDNKVgpUSXZ6cDVLVHlpSEc5cEFkamxPNnZzdlRpVnQzc1hQeWlPcWV3ZE9MLy9kbTNiRVJxWFpaMTlIYTY4V2hsQmtmCkVtd3ZHbnhmMVNrSWdSQXRoM2dnajNObE5zZUEwMkZpWGZKUDdrMGlsdDlZaHpJOXlZM0xPTklVeHJFcmpWSmYKU2hrWlpWRlV4aEZKeEZiaVkzVzgzUlNpYmNBPQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==","verification":{}}]}},"timeouts":{},"version":"2.2.0"},"networkd":{},"passwd":{},"storage":{"files":[{"contents":{"source":"data:text/plain;charset=utf-8,master1.ocp4.skbb-poc.com","verification":{}},"filesystem":"root","group":{},"mode":420,"path":"/etc/hostname","user":{}},{"contents":{"source":"data:text/plain;charset=utf-8;base64,VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjQyCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==","verification":{}},"filesystem":"root","path":"/etc/sysconfig/network-scripts/ifcfg-ens192","mode":420,"user":{}}]},"systemd":{}}
  ```

  > 추가된 부분은 {"files" --  "user":{}}] 까지 입니다.

- 한줄로 변환 할 경우

  > 위에서 작업한 내용을 한줄로 변환 할 경우 아래 script를 수행합니다.
  
  ```bash
  [root@bastion ign]# cat jq_after.sh
  cat jq-poc_bootstrap.ign | jq -c > boot1.ign
  cat jq-poc_master1.ign | jq -c > master1.ign
  cat jq-poc_master2.ign | jq -c > master2.ign
  cat jq-poc_master3.ign | jq -c > master3.ign
  cat jq-poc_infra1.ign | jq -c > infra1.ign
  cat jq-poc_infra2.ign | jq -c > infra2.ign
  cat jq-poc_worker1.ign | jq -c > worker1.ign
  cat jq-poc_worker2.ign | jq -c > worker2.ign
  ```
  
  >  위와 같이 작업을 한 경우에 설치를 위한 사전 작업이 거의 된 것 입니다.



### 12. 설치 사전 확인

> 설치 전에 사전에 확인해야 할 부분을 확인 합니다.

12-1) ip address 확인 

```bash
[root@bastion ign]# ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: ens192: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:95:20:32 brd ff:ff:ff:ff:ff:ff
    inet 10.76.168.40/23 brd 10.76.169.255 scope global noprefixroute ens192
       valid_lft forever preferred_lft forever
    inet6 2620:52:0:4ca8:250:56ff:fe95:2032/64 scope global mngtmpaddr dynamic
       valid_lft 2591781sec preferred_lft 604581sec
    inet6 fe80::250:56ff:fe95:2032/64 scope link
       valid_lft forever preferred_lft forever
```

12-2) httpd 상태 확인

```bash
[root@bastion ign]# systemctl status httpd
● httpd.service - The Apache HTTP Server
   Loaded: loaded (/usr/lib/systemd/system/httpd.service; enabled; vendor preset: disabled)
   Active: active (running) since Thu 2020-02-13 03:21:49 KST; 11h ago
     Docs: man:httpd(8)
           man:apachectl(8)
  Process: 10265 ExecStop=/bin/kill -WINCH ${MAINPID} (code=exited, status=0/SUCCESS)
 Main PID: 10270 (httpd)
   Status: "Total requests: 67; Current requests/sec: 0; Current traffic:   0 B/sec"
   CGroup: /system.slice/httpd.service
           ├─10270 /usr/sbin/httpd -DFOREGROUND
           ├─10271 /usr/sbin/httpd -DFOREGROUND
           ├─10272 /usr/sbin/httpd -DFOREGROUND
           ├─10273 /usr/sbin/httpd -DFOREGROUND
           ├─10274 /usr/sbin/httpd -DFOREGROUND
           ├─10275 /usr/sbin/httpd -DFOREGROUND
           └─10330 /usr/sbin/httpd -DFOREGROUND

Feb 13 03:21:49 bastion.ocp4.skbb-poc.com systemd[1]: Starting The Apache HTTP Server...
Feb 13 03:21:49 bastion.ocp4.skbb-poc.com systemd[1]: Started The Apache HTTP Server.
```

12-3) dns 확인

```bash
[root@bastion ign]# systemctl status named
● named.service - Berkeley Internet Name Domain (DNS)
   Loaded: loaded (/usr/lib/systemd/system/named.service; enabled; vendor preset: disabled)
   Active: active (running) since Thu 2020-02-13 03:51:46 KST; 11h ago
  Process: 10418 ExecStop=/bin/sh -c /usr/sbin/rndc stop > /dev/null 2>&1 || /bin/kill -TERM $MAINPID (code=exited, status=0/SUCCESS)
  Process: 10433 ExecStart=/usr/sbin/named -u named -c ${NAMEDCONF} $OPTIONS (code=exited, status=0/SUCCESS)
  Process: 10430 ExecStartPre=/bin/bash -c if [ ! "$DISABLE_ZONE_CHECKING" == "yes" ]; then /usr/sbin/named-checkconf -z "$NAMEDCONF"; else echo "Checking of zone files is disabled"; fi (code=exited, status=0/SUCCESS)
 Main PID: 10435 (named)
   CGroup: /system.slice/named.service
           └─10435 /usr/sbin/named -u named -c /etc/named.conf

Feb 13 03:51:46 bastion.ocp4.skbb-poc.com named[10435]: running
Feb 13 03:51:46 bastion.ocp4.skbb-poc.com named[10435]: zone 168.76.10.in-addr.arpa/IN: sending notifies (seri...32)
Feb 13 03:51:46 bastion.ocp4.skbb-poc.com named[10435]: zone skbb-poc.com/IN: sending notifies (serial 4019954001)
Feb 13 03:51:46 bastion.ocp4.skbb-poc.com systemd[1]: Started Berkeley Internet Name Domain (DNS).
Feb 13 03:51:46 bastion.ocp4.skbb-poc.com named[10435]: managed-keys-zone: Key 20326 for zone . acceptance tim...ted
Feb 13 08:59:19 bastion.ocp4.skbb-poc.com named[10435]: trust-anchor-telemetry '_ta-4a5c-4f66/IN' from 10.76.168.40
Feb 13 08:59:20 bastion.ocp4.skbb-poc.com named[10435]: trust-anchor-telemetry '_ta-4a5c-4f66/IN' from 10.76.168.40
Feb 13 08:59:20 bastion.ocp4.skbb-poc.com named[10435]: trust-anchor-telemetry '_ta-4a5c-4f66/IN' from 10.76.168.40
Feb 13 08:59:20 bastion.ocp4.skbb-poc.com named[10435]: trust-anchor-telemetry '_ta-4a5c-4f66/IN' from 10.76.168.40
Feb 13 08:59:21 bastion.ocp4.skbb-poc.com named[10435]: trust-anchor-telemetry '_ta-4a5c-4f66/IN' from 10.76.168.40
Hint: Some lines were ellipsized, use -l to show in full.
```

- resolving 확인

  ```bash
  [root@bastion ign]# nslookup bootstrap.ocp4.skbb-poc.com
  Server:         10.76.168.40
  Address:        10.76.168.40#53
  
  Name:   bootstrap.ocp4.skbb-poc.com
  Address: 10.76.168.41
  
  [root@bastion ign]# dig -x 10.76.168.41 +short
  bootstrap.ocp4.skbb-poc.com.
  
  --- 생략 ---
  ```

12-4) haporxy 확인

```bash
[root@bastion ign]# systemctl status haproxy
● haproxy.service - HAProxy Load Balancer
   Loaded: loaded (/usr/lib/systemd/system/haproxy.service; enabled; vendor preset: disabled)
   Active: active (running) since Thu 2020-02-13 02:40:36 KST; 12h ago
 Main PID: 8094 (haproxy-systemd)
   CGroup: /system.slice/haproxy.service
           ├─8094 /usr/sbin/haproxy-systemd-wrapper -f /etc/haproxy/haproxy.cfg -p /run/haproxy.pid
           ├─8095 /usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg -p /run/haproxy.pid -Ds
           └─8096 /usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg -p /run/haproxy.pid -Ds

Feb 13 02:40:36 bastion.ocp4.skbb-poc.com systemd[1]: Started HAProxy Load Balancer.
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: haproxy-systemd-wrapper: executing /us...Ds
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: [WARNING] 043/024036 (8095) : config :...e.
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: [WARNING] 043/024036 (8095) : config :...e.
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: [WARNING] 043/024036 (8095) : config :...e.
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: [WARNING] 043/024036 (8095) : config :...e.
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: [WARNING] 043/024036 (8095) : config :...e.
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: [WARNING] 043/024036 (8095) : config :...e.
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: [WARNING] 043/024036 (8095) : config :...e.
Feb 13 02:40:36 bastion.ocp4.skbb-poc.com haproxy-systemd-wrapper[8094]: [WARNING] 043/024036 (8095) : config :...e.
Hint: Some lines were ellipsized, use -l to show in full.
```



### 13. 노드 구성

13-1) bootstrap node 구성

* bootstrap node를 시작으로 OCP Cluster를 구성합니다.

* 각 서버를 설치 할 때, ==Tab Key==를 눌러서 아래 명령어를 입력하고 설치를 시작합니다.

* 한줄로 입력 되어야 합니다.

  ```bash
  coreos.inst.install_dev=sda coreos.inst.image_url=http://10.76.168.40:8080/bios.raw.gz
  coreos.inst.ignition_url=http://10.76.168.40:8080/ocp/ign/boot1.ign
  ip=10.76.168.41::10.76.169.254:255.255.255.0:bootstrap.ocp4.skbb-poc.com:ens192:none nameserver=10.76.168.40
  ```

- ==bootstrap node가 정상적으로 올라오면, master node 3대를 순차적으로 빠르게 설치를 시작합니다.==
- ==master node (control-plane) 3대가 정상적으로 올라와야 cluster에 대한 healthy check가 commit 되고, bootstrap을 이용한 cluster 구성이 진행됩니다.==
- ==container workload를 실행하기 위해 하나 이상의 worker node를 함께 시작해야 정상적으로 설치가 완료됩니다.==

13-2) bootstrap node 설치 진행 사항 확인

- bootstrap monitoring log message

  ```bash
  --- 생략 ---
  Feb 13 01:41:39 bootstrap.ocp4.skbb-poc.com bootkube.sh[2987]: https://etcd-0.ocp4.skbb-poc.com:2379 is healthy: successfully committed proposal: took = 12.375175ms
  Feb 13 01:41:39 bootstrap.ocp4.skbb-poc.com bootkube.sh[2987]: https://etcd-1.ocp4.skbb-poc.com:2379 is healthy: successfully committed proposal: took = 12.791562ms
  Feb 13 01:41:39 bootstrap.ocp4.skbb-poc.com bootkube.sh[2987]: https://etcd-2.ocp4.skbb-poc.com:2379 is healthy: successfully committed proposal: took = 16.65764ms
  
  --- 생략 ---
  ```

- bootstrap complete install status monitoring command

  ```bash
  [root@bastion ocp]# openshift-install wait-for bootstrap-complete --dir=/var/www/html/ocp --log-level debug
  DEBUG OpenShift Installer v4.3.0
  DEBUG Built from commit 2055609f95b19322ee6cfdd0bea73399297c4a3e
  INFO Waiting up to 30m0s for the Kubernetes API at https://api.ocp4.skbb-poc.com:6443...
  INFO API v1.16.2 up
  INFO Waiting up to 30m0s for bootstrapping to complete...
  DEBUG Bootstrap status: complete
  INFO It is now safe to remove the bootstrap resources
  ```

- openshift complete install log message

  ```bash
  [root@bastion ~]# openshift-install wait-for install-complete --dir=/var/www/html/ocp --log-level debug
  DEBUG OpenShift Installer v4.3.0
  DEBUG Built from commit 2055609f95b19322ee6cfdd0bea73399297c4a3e
  INFO Waiting up to 30m0s for the cluster at https://api.ocp4.skbb-poc.com:6443 to initialize...
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 21% complete
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 44% complete
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 62% complete
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 79% complete
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 80% complete
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 82% complete
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 97% complete
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 99% complete
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 99% complete, waiting on authentication, console, monitoring
  DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 99% complete, waiting on authentication, console, monitoring
  ---생략---
  ```

13-3) Cluster machines 정보 확인

- 구성한 node 정보를 oc command를 이용하여 확인 합니다.

  ```bash
  [root@bastion ocp]# oc get nodes
  NAME                        STATUS   ROLES    AGE   VERSION
  infra1.ocp4.skbb-poc.com    Ready    infra    23h   v1.16.2
  infra2.ocp4.skbb-poc.com    Ready    infra    23h   v1.16.2
  master1.ocp4.skbb-poc.com   Ready    master   27h   v1.16.2
  master2.ocp4.skbb-poc.com   Ready    master   27h   v1.16.2
  master3.ocp4.skbb-poc.com   Ready    master   27h   v1.16.2
  worker1.ocp4.skbb-poc.com   Ready    worker   23h   v1.16.2
  worker2.ocp4.skbb-poc.com   Ready    worker   23h   v1.16.2
  ```

13-4) cluster certification 정보 확인

- certification 정보를 oc command를 이용하여 확인 합니다.

  ```bash
  [root@bastion ocp]# oc get csr
  NAME        AGE   REQUESTOR                                                                   CONDITION
  csr-48w96   24m   system:serviceaccount:openshift-machine-config-operator:node-bootstrapper   Approved,Issued
  csr-lkhz2   18m   system:node:infra1.ocp4.skbb-poc.com                                        Pending
  
  --- 생략 ---
  ```

- pending된 certification 승인 방법

  > 위에서 pending된 certification을 승인 할 수 있습니다.

  ==command: oc adm certificate approve $CSR_NAME==

  ```bash
  [root@bastion ocp]# oc adm certificate approve csr-lkhz2
  ```

- 승인 이후 csr 확인

  ```bash
  [root@bastion ocp]# oc get csr
  NAME        AGE   REQUESTOR                                                                   CONDITION
  csr-48w96   24m   system:serviceaccount:openshift-machine-config-operator:node-bootstrapper   Approved,Issued
  csr-lkhz2   18m   system:node:infra1.ocp4.skbb-poc.com                                        Approved,Issued
  ```

  > 위와 같이 csr-lkhz2의 상태가 Approved로 변경 된 것을 확인 가능 합니다.

- 모든 CSR이 유효하면 다음 명령을 실행하여 CSR을 모두 승인 할 수 있습니다.

  ```bash
  oc get csr -ojson | jq -r '.items[] | select(.status == {} ) | .metadata.name' | xargs oc adm certificate approve
  ```

13-5) clusteroperators 확인

```bash
[root@bastion ~]# watch -n5 oc get clusteroperators
Every 5.0s: oc get clusteroperators                                                                                                                                                    Fri Feb 12 13:45:15 2020

NAME                                       VERSION   AVAILABLE   PROGRESSING   DEGRADED   SINCE
authentication                                       True        False         False      4m32s
cloud-credential                           4.3.0     True        False         False      147m
cluster-autoscaler                         4.3.0     True        False         False      134m
console                                    4.3.0     True        False         False      2m53s
dns                                        4.3.0     True        False         False      140m
image-registry                             4.3.0     True        False         False      137m
ingress                                    4.3.0     True        False         False      5m2s
insights                                   4.3.0     True        False         False      144m
kube-apiserver                             4.3.0     True        True          False      139m
kube-controller-manager                    4.3.0     True        False         False      138m
kube-scheduler                             4.3.0     True        False         False      142m
machine-api                                4.3.0     True        False         False      142m
machine-config                             4.3.0     True        False         False      140m
marketplace                                4.3.0     True        False         False      136m
monitoring                                 4.3.0     True        False         False      2m23s
network                                    4.3.0     True        False         False      145m
node-tuning                                4.3.0     True        False         False      137m
openshift-apiserver                        4.3.0     True        False         False      135m
openshift-controller-manager               4.3.0     True        False         False      141m
openshift-samples                          4.3.0     True        False         False      133m
operator-lifecycle-manager                 4.3.0     True        False         False      142m
operator-lifecycle-manager-catalog         4.3.0     True        False         False      142m
operator-lifecycle-manager-packageserver   4.3.0     True        False         False      138m
service-ca                                 4.3.0     True        False         False      144m
service-catalog-apiserver                  4.3.0     True        False         False      137m
service-catalog-controller-manager         4.3.0     True        False         False      137m
storage                                    4.3.0     True        False         False      137m
```

13-6) install complete message 확인

```bash
[root@bastion ~]# openshift-install wait-for install-complete --dir=/var/www/html/ocp --log-level debug
DEBUG OpenShift Installer v4.3.0
DEBUG Built from commit 2055609f95b19322ee6cfdd0bea73399297c4a3e
INFO Waiting up to 30m0s for the cluster at https://api.ocp4.skbb-poc.com:6443 to initialize...
DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 21% complete
DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 44% complete
---- 생략 ---
DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 100% complete, waiting on authentication
DEBUG Still waiting for the cluster to initialize: Working towards 4.3.0: 100% complete, waiting on authentication
DEBUG Cluster is initialized
INFO Waiting up to 10m0s for the openshift-console route to be created...
DEBUG Route found in openshift-console namespace: console
DEBUG Route found in openshift-console namespace: downloads
DEBUG OpenShift console route is created
INFO Install complete!
INFO To access the cluster as the system:admin user when using 'oc', run 'export KUBECONFIG=/var/www/html/ocp/auth/kubeconfig'
INFO Access the OpenShift web-console here: https://console-openshift-console.apps.ocp4.skbb-poc.com
INFO Login to the console with user: kubeadmin, password: UEbKS-p9mGY-AapZL-yVeuZ
```

==13-7) 설치 시 주의 사항==

> Openshift installation이 생성하는 ignition 파일에는 24시간 후에 만료되는 인증서를 포함하고 있습니다. 
> 따라서 설치는 24시간내에 완료해야하고, Cluster는 24시간동안 running 상태로 유지되어야 합니다.



### 14. Image registry Settings

14-1) empty Directory에 image registry storage 설정

```bash
oc patch configs.imageregistry.operator.openshift.io cluster --type merge --patch '{"spec":{"storage":{"emptyDir":{}}}}'
```

14-2) Image removed during installation

> Shareable object storage를 제공하지 않는 플랫폼에서는 OpenShift Image Registry Operator는 자체적으로 제거됨으로써 bootstrap 합니다.
>
> 이를 통해 openshift-installer는 이러한 플랫폼 유형에서 설치를 완료 할 수 있습니다.

==설치 이후에 Image Registry Operator Configuration에서 ManagementState 파라미터를 Removed -> Managed로 변경해야 합니다.==

```bash
oc patch configs.imageregistry.operator.openshift.io cluster --type merge --patch '{"spec":{"managementState": "Managed"}}'
```

- 위의 설정과 관련하여 Image Registry가 설치 동안 제거 된 경우에는 콘솔에서 다음과 경고 메시지를 볼 수 있습니다.

  ```bash
  "Image Registry has been removed. ImageStreamTags, BuildConfigs and DeploymentConfigs which reference ImageStreamTags may not work as expected. Please configure storage and update the config to Managed state by editing configs.imageregistry.operator.openshift.io."
  ```



### 15. Infra Node Selecting

> OCP 4.x의 경우에는 초기에 Infra node가 worker node에 기본적으로 배포됩니다. 이를 설치 후에 infra 용도로 사용할 node를 지정하기 위해 node labels 작업과 resource를 옮기는 작업을 해야 합니다.

15-1) OCP Console 접속 (Cluster-admin 권한이 있는 사용자)

- Compute -> Nodes 선택 -> Edit Lables

  - 가이드에서는  [infra1.ocp4.skbb-poc.com](https://console-openshift-console.apps.ocp4.skbb-poc.com/k8s/cluster/nodes/infra1.ocp4.skbb-poc.com),  [infra2.ocp4.skbb-poc.com](https://console-openshift-console.apps.ocp4.skbb-poc.com/k8s/cluster/nodes/infra1.ocp4.skbb-poc.com) Node를 Infra 용도로 만들어 두었기 때문에 해당 노드의 Labels를 변경 합니다.

    ```bash
    worekr -> infra
    ```

    - e.g) optional : router node가 따로 존재하는 경우 router node lables 추가

      ```bash
      worker -> router
      ```

  - Edit Labels 선택

    ```bash
    node-role.kubernetes.io/infra
    ```
  
    - e.g) optional : router node가 따로 존재하는 경우 
  
      ```bash
      node-role.kubernetes.io/router
      ```
  
    > 해당 부분을 추가 후 저장
  
  - 저장이 완료 되면, [infra1.ocp4.skbb-poc.com](https://console-openshift-console.apps.ocp4.skbb-poc.com/k8s/cluster/nodes/infra1.ocp4.skbb-poc.com),  [infra2.ocp4.skbb-poc.com](https://console-openshift-console.apps.ocp4.skbb-poc.com/k8s/cluster/nodes/infra1.ocp4.skbb-poc.com) 의 Role에 infra가 추가 된 것을 확인 할 수 있습니다.
  
  - worker node Lables 삭제
  
    ```bash
    node-role.kubernetes.io/worker
    ```
  
    > 저장 후 infra Lables만 남아 있는것 확인

15-2) Moving the router

> router node를 따로 구분하여 구성한 경우 ingressController Custom Resource는 router node에 적용합니다.

> router pod를 다른 node에 배포 할 수 있습니다. 기본적으로 해당 pod는 worker node에서 보여집니다.

- ==해당 가이드는 infra node에 router를 같이 배포한 예제 입니다.==

- router Operator를 위한 ingressController Custom Resource 확인

  ```bash
  [root@bastion ~]# oc get ingresscontroller default -n openshift-ingress-operator -o yaml
  apiVersion: operator.openshift.io/v1
  kind: IngressController
  metadata:
    creationTimestamp: "2020-02-17T15:34:49Z"
    finalizers:
    - ingresscontroller.operator.openshift.io/finalizer-ingresscontroller
    generation: 1
    name: default
    namespace: openshift-ingress-operator
    resourceVersion: "16814"
    selfLink: /apis/operator.openshift.io/v1/namespaces/openshift-ingress-operator/ingresscontrollers/default
    uid: 665084dc-b8b7-4d10-becd-12b85d00144d
  spec:
    replicas: 2
  status:
    availableReplicas: 2
    conditions:
    - lastTransitionTime: "2020-02-17T15:34:49Z"
      reason: Valid
      status: "True"
      type: Admitted
    - lastTransitionTime: "2020-02-17T15:35:29Z"
      status: "True"
      type: Available
    - lastTransitionTime: "2020-02-17T15:35:29Z"
      message: The deployment has Available status condition set to True
      reason: DeploymentAvailable
      status: "False"
      type: DeploymentDegraded
    - lastTransitionTime: "2020-02-17T15:34:52Z"
      message: The endpoint publishing strategy does not support a load balancer
      reason: UnsupportedEndpointPublishingStrategy
      status: "False"
      type: LoadBalancerManaged
    - lastTransitionTime: "2020-02-17T15:34:52Z"
      message: No DNS zones are defined in the cluster dns config.
      reason: NoDNSZones
      status: "False"
      type: DNSManaged
    - lastTransitionTime: "2020-02-17T15:35:29Z"
      status: "False"
      type: Degraded
    domain: apps.ocp4.skbb-poc.com
    endpointPublishingStrategy:
      type: HostNetwork
    observedGeneration: 1
    selector: ingresscontroller.operator.openshift.io/deployment-ingresscontroller=default
    tlsProfile:
      ciphers:
      - TLS_AES_128_GCM_SHA256
      - TLS_AES_256_GCM_SHA384
      - TLS_CHACHA20_POLY1305_SHA256
      - ECDHE-ECDSA-AES128-GCM-SHA256
      - ECDHE-RSA-AES128-GCM-SHA256
      - ECDHE-ECDSA-AES256-GCM-SHA384
      - ECDHE-RSA-AES256-GCM-SHA384
      - ECDHE-ECDSA-CHACHA20-POLY1305
      - ECDHE-RSA-CHACHA20-POLY1305
      - DHE-RSA-AES128-GCM-SHA256
      - DHE-RSA-AES256-GCM-SHA384
      minTLSVersion: VersionTLS12
  ```

- ingresscontroller resource와 nodeselector를 infra lable을 사용하여 변경합니다.

  ==방법은 yaml를 직접 수정하거나, patch command를 통해 적용 할 수 있습니다.==

  ```bash
  oc edit ingresscontroller default -n openshift-ingress-operator -o yaml
  ```

  - 방법1) 해당 yaml 파일 열어서 spec 부분에 다음을 추가

    - e.g) router node가 따로 존재하는 경우 아래 내용에서 `node-role.kubernetes.io/infra: ""` 대신 `node-role.kubernetes.io/router: ""`를 입력합니다.

    ```bash
      spec:
        nodePlacement:
          nodeSelector:
            matchLabels:
              node-role.kubernetes.io/infra: ""
    ```

  - 방법2) patch command를 이용해서 적용

    - e.g) router node가 따로 존재하는 경우 아래 내용에서 `node-role.kubernetes.io/infra: ""` 대신 `node-role.kubernetes.io/router: ""`를 입력합니다.
    
    ```bash
    oc patch ingresscontroller default -n openshift-ingress-operator --type=merge --patch='{"spec":{"nodePlacement":{"nodeSelector": {"matchLabels":{"node-role.kubernetes.io/infra":""}}}}}'
    ```

- 위의 두 가지 방법 중에 하나를 선택하여 적용하면 되고, 설정 후 router pod가 infra(router) node에 confirm 되었는지 확인

  ```bash
  root@bastion ~]# oc get pod -n openshift-ingress -o wide
  NAME                              READY   STATUS    RESTARTS   AGE   IP              NODE                       NOMINATED NODE   READINESS GATES
  router-default-566b8865d8-4fhxf   1/1     Running   0          48s   10.76.168.146   infra2.ocp4.skbb-poc.com   <none>           <none>
  router-default-566b8865d8-gh6kt   1/1     Running   0          60s   10.76.168.145   infra1.ocp4.skbb-poc.com   <none>           <none>
  ```

- 위에서 확인한 infra node RUNNING상태 확인

  ```bash
  [root@bastion ~]# oc get node infra1.ocp4.skbb-poc.com
  NAME                       STATUS   ROLES          AGE   VERSION
  infra1.ocp4.skbb-poc.com   Ready    infra,worker   13h   v1.16.2
  [root@bastion ~]# set -o vi
  [root@bastion ~]# oc get node infra2.ocp4.skbb-poc.com
  NAME                       STATUS   ROLES          AGE   VERSION
  infra2.ocp4.skbb-poc.com   Ready    infra,worker   12h   v1.16.2
  ```

15-3) Moving default registry

> registry resource를 infra node로 재 배치 합니다.

- patch command를 이용하여 적용

  ```bash
  oc patch configs.imageregistry.operator.openshift.io/cluster -n openshift-image-registry --type=merge --patch '{"spec":{"nodeSelector":{"node-role.kubernetes.io/infra":""}}}'
  ```

- 적용된 부분 확인

  ```bash
  oc get config/cluster -o yaml
  ```

  ```bash
  apiVersion: imageregistry.operator.openshift.io/v1
  kind: Config
  metadata:
    creationTimestamp: "2020-02-17T15:34:25Z"
    finalizers:
    - imageregistry.operator.openshift.io/finalizer
    generation: 2
    name: cluster
    resourceVersion: "257095"
    selfLink: /apis/imageregistry.operator.openshift.io/v1/configs/cluster
    uid: 2993ac73-6a5b-480f-99c5-7633dd40ad28
  spec:
    defaultRoute: false
    disableRedirect: false
    httpSecret: 3acce7fde70728ba8ac10d215d4e3eeab31aebb4eb3e1492fd6c9a5f2927b2ebc017d5d9de069193532d10630a4e9e8da641ecae1b870df92c569473caab5f82
    logging: 2
    managementState: Removed
    nodeSelector:
      node-role.kubernetes.io/infra: ""
  ---- 생략 ----
  ```

15-4) Moving the monitoring solution

> 기본적으로 Prometheus, Grafana 및 AlertManager가 포함된 Prometheus 클러스터 모니터링 스택은 클러스터 모니터링을 제공하기 위해 배포됩니다. 클러스터 모니터링은 운영자가 관리합니다. 구성 요소를 다른 시스템으로 이동하려면 Custom Config Map을 작성하고 적용해야 합니다.

- Infra Node에 떠야 하는 구성 요소가 다른 Node에 예약되지 않도록 설정

  - Infra Node Taints 설정

    ```bash
    oc adm taint node infra1.ocp4.skbb-poc.com infra=reserved:NoSchedule
    oc adm taint node infra1.ocp4.skbb-poc.com infra=reserved:NoExecute
    
    oc adm taint node infra2.ocp4.skbb-poc.com infra=reserved:NoSchedule
    oc adm taint node infra2.ocp4.skbb-poc.com infra=reserved:NoExecute
    ```

    - e.g) router node가 따로 존재하는 경우 router node에도 Taints 설정을 해야 합니다.

      ```bash
      oc adm taint node router1.ocp4.skbb-poc.com infra=reserved:NoSchedule
      oc adm taint node router1.ocp4.skbb-poc.com infra=reserved:NoExecute
      
      oc adm taint node router2.ocp4.skbb-poc.com infra=reserved:NoSchedule
      oc adm taint node router2.ocp4.skbb-poc.com infra=reserved:NoExecute
      ```

  - ingress controller Node Taints 설정 (router node인 경우 router node에 적용)

    - e.g) router node가 따로 존재하는 경우 아래 내용에서 `node-role.kubernetes.io/infra: ""` 대신 `node-role.kubernetes.io/router: ""`를 입력합니다.

    ```bash
    oc patch ingresscontroller default -n openshift-ingress-operator --type=merge --patch='{"spec":{"nodePlacement": {"nodeSelector": {"matchLabels": {"node-role.kubernetes.io/infra": ""}},"tolerations": [{"effect":"NoSchedule","key": "infra","value": "reserved"},{"effect":"NoExecute","key": "infra","value": "reserved"}]}}}'
    ```

  - Scheduler Operator Custom Resource를 ConfigMap에 추가 설정

    ```bash
    oc patch config cluster --type=merge --patch='{"spec":{"nodeSelector": {"node-role.kubernetes.io/infra": ""},"tolerations": [{"effect":"NoSchedule","key": "infra","value": "reserved"},{"effect":"NoExecute","key": "infra","value": "reserved"}]}}'
    ```

- cluster-monitoring-configmap.yaml  작성

  ```bash
  cat <<EOF>> monitoring.yaml
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: cluster-monitoring-config
    namespace: openshift-monitoring
  data:
    config.yaml: |
      alertmanagerMain:
        nodeSelector:
          node-role.kubernetes.io/infra: ""
        tolerations:
        - key: infra
          value: reserved
          effect: NoSchedule
        - key: infra
          value: reserved
          effect: NoExecute
      prometheusK8s:
        nodeSelector:
          node-role.kubernetes.io/infra: ""
        tolerations:
        - key: infra
          value: reserved
          effect: NoSchedule
        - key: infra
          value: reserved
          effect: NoExecute
      prometheusOperator:
        nodeSelector:
          node-role.kubernetes.io/infra: ""
        tolerations:
        - key: infra
          value: reserved
          effect: NoSchedule
        - key: infra
          value: reserved
          effect: NoExecute
      grafana:
        nodeSelector:
          node-role.kubernetes.io/infra: ""
        tolerations:
        - key: infra
          value: reserved
          effect: NoSchedule
        - key: infra
          value: reserved
          effect: NoExecute
      k8sPrometheusAdapter:
        nodeSelector:
          node-role.kubernetes.io/infra: ""
        tolerations:
        - key: infra
          value: reserved
          effect: NoSchedule
        - key: infra
          value: reserved
          effect: NoExecute
      kubeStateMetrics:
        nodeSelector:
          node-role.kubernetes.io/infra: ""
        tolerations:
        - key: infra
          value: reserved
          effect: NoSchedule
        - key: infra
          value: reserved
          effect: NoExecute
      telemeterClient:
        nodeSelector:
          node-role.kubernetes.io/infra: ""
        tolerations:
        - key: infra
          value: reserved
          effect: NoSchedule
        - key: infra
          value: reserved
          effect: NoExecute
  EOF
  ```

- 적용

  ```bash
  [root@bastion ~]# oc create -f monitoring.yaml
  configmap/cluster-monitoring-config created
  ```

- 새로운 Machine으로 monitoring Pod가 이동 했는지 확인

  ```bash
  watch 'oc get pod -n openshift-monitoring -o wide'
  ```

  ```bash
  Every 2.0s: oc get pod -n openshift-monitoring -o wide                                                                                    Tue Feb 18 13:40:40 2020
  
  NAME                                           READY   STATUS    RESTARTS   AGE   IP              NODE                        NOMINATED NODE   READINESS GATES
  alertmanager-main-0                            3/3     Running   0          17s   10.130.0.27     infra1.ocp4.skbb-poc.com    <none>           <none>
  alertmanager-main-1                            3/3     Running   0          28s   10.130.0.26     infra1.ocp4.skbb-poc.com    <none>           <none>
  alertmanager-main-2                            3/3     Running   0          58s   10.130.2.12     infra2.ocp4.skbb-poc.com    <none>           <none>
  cluster-monitoring-operator-7bbc9f9895-d6jf7   1/1     Running   0          13h   10.128.0.28     master2.ocp4.skbb-poc.com   <none>           <none>
  grafana-565b7f4d9d-pw6nq                       2/2     Running   0          58s   10.130.2.11     infra2.ocp4.skbb-poc.com    <none>           <none>
  kube-state-metrics-f7df4b4fc-rbh8n             3/3     Running   0          79s   10.130.2.7      infra2.ocp4.skbb-poc.com    <none>           <none>
  node-exporter-5pd96                            2/2     Running   0          13h   10.76.168.142   master1.ocp4.skbb-poc.com   <none>           <none>
  node-exporter-927g4                            2/2     Running   0          13h   10.76.168.143   master2.ocp4.skbb-poc.com   <none>           <none>
  node-exporter-jd8rt                            2/2     Running   0          13h   10.76.168.145   infra1.ocp4.skbb-poc.com    <none>           <none>
  node-exporter-kpdmt                            2/2     Running   0          13h   10.76.168.146   infra2.ocp4.skbb-poc.com    <none>           <none>
  node-exporter-sqxzt                            2/2     Running   0          13h   10.76.168.148   worker2.ocp4.skbb-poc.com   <none>           <none>
  node-exporter-t9z7v                            2/2     Running   0          13h   10.76.168.144   master3.ocp4.skbb-poc.com   <none>           <none>
  node-exporter-v24lq                            2/2     Running   0          13h   10.76.168.147   worker1.ocp4.skbb-poc.com   <none>           <none>
  openshift-state-metrics-b6755756-89h7l         3/3     Running   0          13h   10.130.0.7      infra1.ocp4.skbb-poc.com    <none>           <none>
  prometheus-adapter-7594cf8dcd-7dvlk            1/1     Running   0          45s   10.130.0.25     infra1.ocp4.skbb-poc.com    <none>           <none>
  prometheus-adapter-7594cf8dcd-jpkhr            1/1     Running   0          64s   10.130.2.10     infra2.ocp4.skbb-poc.com    <none>           <none>
  prometheus-k8s-0                               7/7     Running   1          12h   10.130.0.24     infra1.ocp4.skbb-poc.com    <none>           <none>
  prometheus-k8s-1                               6/7     Running   1          38s   10.130.2.13     infra2.ocp4.skbb-poc.com    <none>           <none>
  prometheus-operator-6bf9c6f988-9w9t8           1/1     Running   0          79s   10.130.2.8      infra2.ocp4.skbb-poc.com    <none>           <none>
  telemeter-client-66fcbff8f5-pzjr9              3/3     Running   0          69s   10.130.2.9      infra2.ocp4.skbb-poc.com    <none>           <none>
  thanos-querier-684db5bccc-4gh5q                4/4     Running   0          12h   10.130.2.3      infra2.ocp4.skbb-poc.com    <none>           <none>
  thanos-querier-684db5bccc-sdrp2                4/4     Running   0          12h   10.129.0.36     master3.ocp4.skbb-poc.com   <none>           <none>
  ```

  > prometheus 관련 Pod가 infra node로 이동한 것을 확인 할 수 있습니다.
>
  > 또한, 위의 설정을 적용하면, infra node의 요소들이 다시 재 스케줄링 되면서 정리 됩니다.

  

### 16. Console 접속

> Console 접속을 위한 hosts 파일 수정

```bash
10.76.168.40          console-openshift-console.apps.ocp4.skbb-poc.com
10.76.168.40          oauth-openshift.apps.ocp4.skbb-poc.com
```

> Console 접속 URL 및 IP/PWD는 install complete log에서 확인이 가능하며, 추후에 계정을 생성하여 사용 가능 합니다.



- Console URL 정보

  https://console-openshift-console.apps.ocp4.skbb-poc.com

  ID: kubeadmin / PWD : UEbKS-p9mGY-AapZL-yVeuZ

- OpenShift API 정보

   https://api.ocp4.skbb-poc.com:6443



### 17. 계정 생성 (Configuring an HTPasswd identity provider)

17-1) 계정 생성

- OCP 설치 디렉토리에서 계정 생성 명령어 실행

```bash
# htpasswd -c -B -b ./htpasswd admin redhat
```

17-2) HTPasswd Secret 생성

```bash
[root@bastion ocp]# oc create secret generic htpass-secret --from-file=htpasswd=./htpasswd -n openshift-config
secret/opentlc-ldap-secret created
```

17-2) Cluster 권한 부여

```bash
# oc adm policy add-cluster-role-to-user cluster-admin admin
```

> 17-1)에서 생성한 admin 계정에 cluster-admin 권한을 부여합니다.

- Sample HTPasswd CR 

  > 다음 Custom Resource (CR)은 HTPasswd identity provider의 매개 변수 및 허용 가능한 값을 보여준다.

  - sample yaml

  ```yaml
  apiVersion: config.openshift.io/v1
  kind: OAuth
  metadata:
    name: cluster
  spec:
    identityProviders:
    - name: my_htpasswd_provider 1)
      mappingMethod: claim 2)
      type: HTPasswd
      htpasswd:
        fileData:
          name: htpass-secret 3)
  ```

  - 1) 이 제공자 이름은 제공자 이름에 접두어로 ID 이름을 형성합니다.
  - 2) 이 공급자의 ID와 사용자 개체간에 매핑을 설정하는 방법을 제어합니다.
  - 3) htpasswd를 사용하여 생성 된 파일을 포함하는 기존 secret

- yaml

  ```yaml
  vi passwd.yaml
  apiVersion: config.openshift.io/v1
  kind: OAuth
  metadata:
    name: cluster
  spec:
    identityProviders:
    - name: skbb-poc
      mappingMethod: claim 
      type: HTPasswd
      htpasswd:
        fileData:
          name: htpass-secret 
  ```

- Cluster에 identity provider 추가

  > 위에서 생성한 passwd.yaml을 적용한다.

  ```bash
  [root@registry ocp]# oc apply -f passwd.yaml
  Warning: oc apply should be used on resource created by either oc create --save-config or oc apply
  ```

- oc login 확인

  - 새로 생성한 계정으로 바로 로그인이 되지 않을 경우 조금 기다렸다가 하면 됩니다.
  - 변경 사항이 적용 되는데 시간이 조금 걸릴 수 있습니다.
  
  ```bash
  # oc login -u <username>
  
  [root@bastion ocp]# oc login -u admin
  Authentication required for https://api.ocp4.skbb-poc.com:6443 (openshift)
  Username: admin
  Password:
  Login successful.
  
  You have access to 53 projects, the list has been suppressed. You can list all projects with 'oc projects'
  
  Using project "default".
  [root@bastion ocp]# oc projects
  You have access to the following projects and can switch between them with 'oc project <projectname>':
  
    * default
      kube-node-lease
      kube-public
      kube-system
      openshift
      openshift-apiserver
      openshift-apiserver-operator
      openshift-authentication
      openshift-authentication-operator
      openshift-cloud-credential-operator
      openshift-cluster-machine-approver
      openshift-cluster-node-tuning-operator
      openshift-cluster-samples-operator
      
  ---- 생략 ----
  
  Using project "default" on server "https://api.ocp4.skbb-poc.com:6443".
  ```
  
- login이 성공하면 id 확인 

  ```bash
  [root@bastion ocp]# oc whoami
  admin
  ```

  - admin 계정으로도 Console  접속이 가능하다.

17-4) kubeadmin 계정 삭제

```bash
oc delete secrets kubeadmin -n kube-system
```



### 18. Adding worker nodes to the OCP 4 UPI cluster (worker node 추가)

> 설치 이후에 기존 OCP Cluster에 worker node를 추가하는 방법입니다.

18-1) 추가 node ignition 구성을 위한 network script 생성

- worker4 network-script 내용 작성

  ```bash
  TYPE=Ethernet
  PROXY_METHOD=none
  BROWSER_ONLY=no
  BOOTPROTO=static
  IPADDR=10.76.168.49
  NETMASK=255.255.254.0
  GATEWAY=10.76.169.254
  DEFROUTE=yes
  IPV4_FAILURE_FATAL=no
  NAME=ens192
  DEVICE=ens192
  ONBOOT=yes
  DOMAIN=ocp4.skbb-poc.com
  DNS1=10.76.168.40
  ```

- network-script를 base64 인코딩

  ```bash
  [root@bastion ign]# cat worker4-net.txt | base64 -w0
  VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjUwCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==
  ```

18-2) ignition 생성

> 기존에 만들어 놓은 worker node의 ignition 파일을 복사하여, base64 인코딩 값 부분과 hostname을 변경합니다.

- worker4.ign

```bash
{"ignition":{"config":{"append":[{"source":"https://api-int.ocp4.skbb-poc.com:22623/config/worker","verification":{}}]},"security":{"tls":{"certificateAuthorities":[{"source":"data:text/plain;charset=utf-8;base64,LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURFRENDQWZpZ0F3SUJBZ0lJRC80VEI2dDVGSjB3RFFZSktvWklodmNOQVFFTEJRQXdKakVTTUJBR0ExVUUKQ3hNSmIzQmxibk5vYVdaME1SQXdEZ1lEVlFRREV3ZHliMjkwTFdOaE1CNFhEVEl3TURJeU1URTJOVGsxTjFvWApEVE13TURJeE9ERTJOVGsxTjFvd0pqRVNNQkFHQTFVRUN4TUpiM0JsYm5Ob2FXWjBNUkF3RGdZRFZRUURFd2R5CmIyOTBMV05oTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF3NVhnM3dpZ3ptdXQKdFd1c2hHcTd5UWlOUVlLcXNmVkgxZ3dRdk42Ui9EZ3BYRjVJYmJValRlZm8rUE1tcEdkL2lnblNneDlVWFpPYgpuSkxRZkkwT2VoZ3B2Z2ErcnVyNDJEVHdHbjhmUTUraEw0WFgrV2tGcUdTOEJ6Ri9DY2J4RU9lTllGVWRoSklhCnpKS3BHTUVUY1ZUYVJsTEI1UW1pTXdLMC84NVM3RzJ3M2h3eXB5ZUJEaW5zWGw3cUdMWmhqUjEza29QUjRycVgKdDZhbCs3NjVSdjRCNWhKUGZDVkhJaEI5b29sWGNreXNwdEkxRzkzeGF3OVNUcEhWdWR1SGFKSFQreDZCYmNtcgp1V2RpZHA1S1Rrd1RYUW82M0kvVG5iU1NidTY0M2ZCRkFabUhFcmttRmU4cUV3ME0zUTRWcnIxdXllMWthSXNKCm9OSDh5Lzh4eXdJREFRQUJvMEl3UURBT0JnTlZIUThCQWY4RUJBTUNBcVF3RHdZRFZSMFRBUUgvQkFVd0F3RUIKL3pBZEJnTlZIUTRFRmdRVU9XeEFkdWJUTnF1Y3BnMElKY1pKNmM2QU9yY3dEUVlKS29aSWh2Y05BUUVMQlFBRApnZ0VCQUN1ZlIvZlFEeVZTNUZCRWZkNDFhR2h1dEtkZHFRNDAvd3FDMXF3RGNadWhXdkM3L3ZzZmMyZVZGU2FVCm8zdlg3b1ZPZHErSDMxWmd5WFJZQmx1VjFHcVRYeE9pazZQMjFtSXlIZDBpMUJMWTR5ZEMyck9OZ1JzVmtRUHkKV2xLaEQyRUc3TjEyaHVPMm4vc2Z1V2o2ZklBOGVvZSt6ZGk1NVduNDZqeGZ1M21vdE1aVDd1ZGx5bHBMRyt4RQp0eHJRT1NIWi9mczlDR2pETnMvR0hYaHZIRmdiSEU5azFMRmJhRlZTeE4zdXV4c3YwNDFsSWQ1ZEJSZ053dlE2ClpiVEVvM3I5Znh6b05qWXY5TDNBVFIva2NJeXcxVWRVSTkzQyt3RksydGlSUjFNYWVGcE9NSlphaTNqdno4cmkKdmRvdjF6Ti84TWxpWTlOS1JUUDE4Q1lOSHB3PQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==","verification":{}}]}},"timeouts":{},"version":"2.2.0"},"networkd":{},"passwd":{},"storage":{"files":[{"contents":{"source":"data:text/plain;charset=utf-8,worker4.ocp4.skbb-poc.com","verification":{}},"filesystem":"root","group":{},"mode":420,"path":"/etc/hostname","user":{}},{"contents":{"source":"data:text/plain;charset=utf-8;base64,VFlQRT1FdGhlcm5ldApQUk9YWV9NRVRIT0Q9bm9uZQpCUk9XU0VSX09OTFk9bm8KQk9PVFBST1RPPXN0YXRpYwpJUEFERFI9MTAuNzYuMTY4LjUwCk5FVE1BU0s9MjU1LjI1NS4yNTQuMApHQVRFV0FZPTEwLjc2LjE2OS4yNTQKREVGUk9VVEU9eWVzCklQVjRfRkFJTFVSRV9GQVRBTD1ubwpOQU1FPWVuczE5MgpERVZJQ0U9ZW5zMTkyCk9OQk9PVD15ZXMKRE9NQUlOPW9jcDQuc2tiYi1wb2MuY29tCkROUzE9MTAuNzYuMTY4LjQwCg==","verification":{}},"filesystem":"root","path":"/etc/sysconfig/network-scripts/ifcfg-ens192","mode":420,"user":{}}]},"systemd":{}}
```

- 파일 생성 방식은 11번 ignition 파일 생성 부분을 참고하여 작업합니다.

18-3) 설치 시작

- 위의 사전 작업이 완료 되면, CoreOS VM을 하나 더 생성하고 설치를 진행 합니다.

18-4) 인증서 승인

- 설치가 완료 되면, oc command를 이용하여 인증서 승인을 합니다.

```bash
[root@bastion ign]# oc get csr
NAME        AGE   REQUESTOR                                                                   CONDITION
csr-jw2hx   1s    system:node:worker4.ocp4.skbb-poc.com                                       Pending
csr-m7t4g   10m   system:serviceaccount:openshift-machine-config-operator:node-bootstrapper   Approved,Issued
[root@bastion ign]# oc adm certificate approve csr-jw2hx
certificatesigningrequest.certificates.k8s.io/csr-jw2hx approved

[root@bastion ign]# oc get csr
NAME        AGE   REQUESTOR                                                                   CONDITION
csr-jw2hx   68s   system:node:worker4.ocp4.skbb-poc.com                                       Approved,Issued
csr-m7t4g   11m   system:serviceaccount:openshift-machine-config-operator:node-bootstrapper   Approved,Issued
```

18-5) Console 확인

> OpenShift Console > Compute > Nodes에서 새로 추가한 worker4.ocp4.skbb-poc.com Node가 추가된 것을 확인 할 수 있습니다.




### 19. 참고 URL

- 공식 문서 URL)

  OCP 4.3 install Guide :  https://access.redhat.com/documentation/en-us/openshift_container_platform/4.3/html/installing_on_vsphere/installing-on-vsphere#installation-initializing-manual_installing-vsphere 

  Set up static IP configuration for an RHCOS node :  https://access.redhat.com/solutions/4531011 

