## Firewall

Question: CentOS7 uses firewalld, why does iptables command still works

> **`firewalld` is not a replacement for `iptables`; it is a management layer on top of `iptables` on CentOS 7.**

                 firewall-cmd
                      │
                      ▼
                 firewalld daemon
                      │
             translates rules into
                      │
                      ▼
                iptables (kernel)
                      │
                      ▼
             Linux Netfilter framework

On newer systems, such as **RHEL 8/9**, **CentOS Stream 8/9**, and **Rocky Linux 8/9**, the backend is often **nftables** instead of legacy iptables.