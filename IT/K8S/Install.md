## Brief

We'll build a three-node Kubernetes cluster using `kubeadm`, `containerd`, and `Calico` as the container runtime and network plugin.

I'll use one machine as the control-plane node and the other two as worker nodes. The commands below assume a fresh Rocky Linux 9.8 installation and root or `sudo` access.

## 1. Cluster architecture

| Node          | Role          | Example IP      | Components                                      |
| ------------- | ------------- | --------------- | ----------------------------------------------- |
| `k8s-master`  | Control plane | `192.168.10.11` | API server, scheduler, controller manager, etcd |
| `k8s-worker1` | Worker        | `192.168.10.12` | kubelet, containerd                             |
| `k8s-worker2` | Worker        | `192.168.10.13` | kubelet, containerd                             |

The control plane exposes the Kubernetes API and coordinates the cluster.

These IP addresses are examples. Replace them with the actual static IP addresses of your three machines.

| Component          | Choice          |
| ------------------ | --------------- |
| Operating system   | Rocky Linux 9.8 |
| Kubernetes         | v1.37.x         |
| Installation       | kubeadm         |
| Container runtime  | containerd      |
| CNI network plugin | Calico          |
| Pod network CIDR   | `10.244.0.0/16` |
| Service CIDR       | `10.96.0.0/12`  |

Version note: Kubernetes v1.37 is a version-specific requirement. Confirm that the v1.37 packages and compatible Calico release are published before installation. Don't silently substitute a different Kubernetes minor version if the repository doesn't contain v1.37 packages.

## 2. Prepare all three machines

Run the following steps on all three nodes.

### 2.1 Set hostnames

Run the appropriate command on each machine.

On the control plane:

```bash
sudo hostnamectl set-hostname k8s-master
```

On worker 1:

```bash
sudo hostnamectl set-hostname k8s-worker1
```

On worker 2:

```bash
sudo hostnamectl set-hostname k8s-worker2
```

Configure `/etc/hosts` on every node:

```bash
sudo tee -a /etc/hosts <<'EOF'
192.168.10.11 k8s-master
192.168.10.12 k8s-worker1
192.168.10.13 k8s-worker2
EOF
```

Verify:

```bash
hostname
getent hosts k8s-master k8s-worker1 k8s-worker2
```

Ensure that the IP addresses are correct and reachable.

### 2.2 Update the operating system and install utilities

```bash
sudo dnf update -y
sudo dnf install -y curl wget vim chrony tar iproute-tc \
  socat conntrack-tools iptables
sudo systemctl enable --now chronyd
```

Check the OS:

```bash
cat /etc/rocky-release
uname -r
timedatectl
```

### 2.3 Disable swap

Kubelet normally requires swap to be disabled unless you deliberately configure supported swap behavior.

```bash
sudo swapoff -a
sudo cp -a /etc/fstab /etc/fstab.bak
sudo sed -ri '/^[^#].*\sswap\s/s/^/#/' /etc/fstab
```

Verify:

```bash
swapon --show
free -h
```

`swapon --show` should return no active swap devices.

### 2.4 Configure kernel modules and networking

```bash
sudo tee /etc/modules-load.d/k8s.conf <<'EOF'
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

Configure sysctl:

```bash
sudo tee /etc/sysctl.d/99-kubernetes-cri.conf <<'EOF'
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system
```

Verify:

```bash
lsmod | egrep 'overlay|br_netfilter'
sysctl net.ipv4.ip_forward
sysctl net.bridge.bridge-nf-call-iptables
```

Expected IPv4 forwarding value:

```
net.ipv4.ip_forward = 1
```

### 2.5 Configure SELinux and the firewall

For a straightforward initial lab installation, the Kubernetes v1.37 documentation recommends permissive SELinux mode. This reduces SELinux protection, so for production, prefer a properly tested SELinux policy where possible.

```bash
sudo setenforce 0
sudo sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' \
  /etc/selinux/config
```

Check:

```bash
getenforce
```

Expected:

```
Permissive
```

Firewall: Do not expose the Kubernetes API or node ports to untrusted networks. Allow the required traffic between the three nodes and any authorized administration network.

For this cluster, the important default ports include:

| Port / protocol  | Purpose                          |
| ---------------- | -------------------------------- |
| TCP 6443         | Kubernetes API server            |
| TCP 2379–2380    | etcd, control plane              |
| TCP 10250        | Kubelet API                      |
| TCP 10257, 10259 | Controller manager and scheduler |
| UDP 4789         | Calico VXLAN, if using VXLAN     |
| TCP 179          | Calico BGP, if using BGP         |

The control-plane ports are not all required on workers. Calico's actual networking mode determines whether UDP 4789 or TCP 179 is needed.

If `firewalld` is enabled, design the rules for your network rather than disabling it blindly. In particular, don't expose etcd ports to ordinary client networks.

## 3. Install containerd on all three nodes

Kubernetes needs a container runtime. We'll use containerd directly rather than Docker Engine, so there is no need for the separate `cri-dockerd` adapter.

### 3.1 Add the Docker RPM repository

On all three machines:

```bash
sudo dnf config-manager --add-repo \
  https://download.docker.com/linux/centos/docker-ce.repo
```

If `config-manager` is unavailable, install the DNF plugins first:

```bash
sudo dnf install -y dnf-plugins-core
```

Then run the repository command again.

### 3.2 Install containerd

```bash
sudo dnf install -y containerd.io
```

Generate the default configuration:

```bash
sudo mkdir -p /etc/containerd
sudo containerd config default | \
  sudo tee /etc/containerd/config.toml >/dev/null
```

### 3.3 Configure the systemd cgroup driver

Kubernetes and containerd should use compatible cgroup drivers. With Rocky Linux 9's systemd and cgroup v2 setup, use the `systemd` driver.

For the containerd 2.x configuration generated above, run:

```bash
sudo sed -i \
  's/SystemdCgroup = false/SystemdCgroup = true/' \
  /etc/containerd/config.toml
```

Check the resulting setting:

```bash
grep -n 'SystemdCgroup' /etc/containerd/config.toml
```

It should show `SystemdCgroup = true` in the runtime options section. If the generated file contains multiple occurrences, verify that the setting for the `runc` runtime is the one changed.

Check that the CRI plugin isn't disabled:

```bash
grep -n 'disabled_plugins' /etc/containerd/config.toml
```

If `cri` appears in `disabled_plugins`, remove it from that list.

Enable and start containerd:

```bash
sudo systemctl enable --now containerd
sudo systemctl status containerd --no-pager
```

Confirm the runtime socket exists:

```bash
ls -l /run/containerd/containerd.sock
```

If you already have a different containerd version installed, inspect it with `containerd --version` before applying version-specific configuration.


### 3.4 Configure image registry mirrors and the pause image

Run on all three nodes. These settings configure containerd to use the Daocloud mirrors for Docker Hub and Quay, and replace the sandbox (pause) image with the Aliyun image.

Create the Docker Hub mirror configuration:

```bash
sudo mkdir -p /etc/containerd/certs.d/docker.io
sudo tee /etc/containerd/certs.d/docker.io/hosts.toml <<'EOF'
server = "https://docker.m.daocloud.io"

[host."https://docker.m.daocloud.io"]
  capabilities = ["pull", "resolve"]
EOF
```

Create the Quay mirror configuration:

```bash
sudo mkdir -p /etc/containerd/certs.d/quay.io
sudo tee /etc/containerd/certs.d/quay.io/hosts.toml <<'EOF'
server = "https://quay.m.daocloud.io"

[host."https://quay.m.daocloud.io"]
  capabilities = ["pull", "resolve"]
EOF
```

For containerd 2.x, edit `/etc/containerd/config.toml` and ensure the following settings exist in the corresponding sections. Merge these values into the existing configuration; do not add duplicate sections.

```toml
[plugins.'io.containerd.cri.v1.images'.registry]
  config_path = "/etc/containerd/certs.d"

[plugins.'io.containerd.cri.v1.images'.pinned_images]
  sandbox = "registry.aliyuncs.com/google_containers/pause:3.10.2"
```

The `config_path` setting enables containerd to read the `hosts.toml` files. The `sandbox` setting replaces the default pause image with `registry.aliyuncs.com/google_containers/pause:3.10.2`.

Restart containerd on each node:

```bash
sudo systemctl restart containerd
sudo systemctl status containerd --no-pager
```

Check the settings:

```bash
egrep -n -A4 -B2 'config_path\\|pinned_images\\|sandbox' /etc/containerd/config.toml
cat /etc/containerd/certs.d/docker.io/hosts.toml
cat /etc/containerd/certs.d/quay.io/hosts.toml
```

> **Note:** These mirror files only redirect image pulls for `docker.io` and `quay.io`. They do not mirror `registry.k8s.io`. The pause image is changed separately through containerd's `pinned_images.sandbox` setting. If your installed containerd uses the older 1.x configuration format, the equivalent settings are under `plugins."io.containerd.grpc.v1.cri"`; do not paste the 2.x section into a 1.x configuration.

## 4. Install Kubernetes v1.37 on all three nodes

The Kubernetes RPM repository is organized by minor version. Use the dedicated v1.37 repository rather than the old, frozen `yum.kubernetes.io` repository.

### 4.1 Add the Kubernetes repository

Run on all three machines:

```bash
sudo tee /etc/yum.repos.d/kubernetes.repo <<'EOF'
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.37/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.37/rpm/repodata/repomd.xml.key
exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni
EOF
```

Refresh metadata and check available packages:

```bash
sudo dnf clean all
sudo dnf makecache
sudo dnf --disableexcludes=kubernetes list --showduplicates \
  kubelet kubeadm kubectl
```

### 4.2 Install kubelet, kubeadm, and kubectl

```bash
sudo dnf install -y kubelet kubeadm kubectl \
  --disableexcludes=kubernetes
```

Verify:

```bash
kubelet --version
kubeadm version
kubectl version --client
```

The binaries should report Kubernetes `v1.37.x`. All three nodes should use the same minor version, and for this setup, matching patch versions is preferable.

Enable kubelet:

```bash
sudo systemctl enable --now kubelet
```

It's normal for kubelet to restart or report errors before `kubeadm init` or `kubeadm join` completes its configuration.

### 4.3 Install CNI binaries

Run on all three nodes:

```bash
CNI_VERSION=v1.7.1
ARCH=amd64

sudo mkdir -p /opt/cni/bin

curl -fL \
  "https://github.com/containernetworking/plugins/releases/download/${CNI_VERSION}/cni-plugins-linux-${ARCH}-${CNI_VERSION}.tgz" \
  -o /tmp/cni-plugins.tgz

sudo tar -C /opt/cni/bin -xzf /tmp/cni-plugins.tgz
```

If your machines use ARM64 rather than x86-64, change `ARCH` to `arm64`.

Verify:

```bash
ls /opt/cni/bin
```

You should see binaries such as `loopback` and `bridge`.

## 5. Initialize the control plane

Run the following section only on `k8s-master`.

### 5.1 Check prerequisites

```bash
ip -br addr
ip route
containerd --version
kubeadm version
```

Make sure `192.168.10.11` is the correct control-plane IP and that it is reachable from both workers.

For the example below, we'll use `192.168.0.0/16` as the Pod CIDR to match Calico's default installation configuration. Confirm that this range doesn't overlap with your physical network, VPNs, or other routed networks before proceeding.

### 5.2 Pull the required images

```bash
sudo kubeadm config images pull \
  --kubernetes-version=v1.37.1 \
  --cri-socket=unix:///run/containerd/containerd.sock
```

This is an optional pre-pull step. It uses `v1.37.1` as an example; if the installed repository provides a newer v1.37 patch, replace it with the exact intended patch version. You can also let `kubeadm init` pull the images automatically.

### 5.3 Initialize Kubernetes

First, determine the actual version installed:

```bash
kubeadm version -o short
```

Then use that exact version in the initialization command. For example, if the installed version is `v1.37.1`:

```bash
sudo kubeadm init \
  --apiserver-advertise-address=192.168.10.11 \
  --kubernetes-version=v1.37.1 \
  --pod-network-cidr=192.168.0.0/16 \
  --cri-socket=unix:///run/containerd/containerd.sock
```

Replace `v1.37.1` with the version you actually installed. The Kubernetes control-plane components will be initialized at that version.

Wait for the command to finish successfully. At the end, `kubeadm` prints a `kubeadm join` command. Save that command; you'll need it on both worker nodes.

If `kubeadm init` fails, fix the reported cause first (see the troubleshooting checklist), then reset the failed state and retry:

```bash
sudo kubeadm reset \
  --cri-socket=unix:///run/containerd/containerd.sock
sudo rm -rf /etc/cni/net.d
```

`kubeadm reset` does not clean up the CNI configuration, iptables rules, or `$HOME/.kube`. On the control plane, also remove the kubectl configuration if you had already created it:

```bash
rm -rf "$HOME/.kube"
```

Optionally flush leftover traffic rules before retrying (`kubeadm reset` does not clean iptables, nftables, or IPVS rules applied by kube-proxy, but leaving them usually causes no issues when the host is reused as a Kubernetes node):

```bash
sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F
sudo systemctl restart containerd kubelet
```

Then re-run the `kubeadm init` command above.

### 5.4 Configure kubectl

On `k8s-master`, for the user who will administer the cluster:

```bash
mkdir -p "$HOME/.kube"
sudo cp -i /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

Verify the API server responds:

```bash
kubectl cluster-info
kubectl get nodes
```

The control-plane node will commonly show `NotReady` at this point because the Pod network has not yet been installed. That's expected.

## 6. Install Calico networking

Calico allows Pods on different nodes to communicate. We'll use the operator-based installation documented for Calico 3.33, which supports Kubernetes 1.37.

Run these commands on `k8s-master`.

### 6.1 Install Calico CRDs

```bash
kubectl create -f \
https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/v3_projectcalico_org.yaml
```

### 6.2 Install the Tigera operator

```bash
kubectl create -f \
https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/tigera-operator.yaml
```

### 6.3 Configure the Pod network

Download the custom resource manifest so you can inspect it:

```bash
curl -fL \
https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/custom-resources.yaml \
  -o custom-resources.yaml
```

Check the default IP pool:

```bash
egrep -A8 -B3 'cidr:' custom-resources.yaml
```

The default IP pool should match the Pod CIDR passed to `kubeadm init`, namely `192.168.0.0/16`. If you chose a different Pod CIDR, edit the manifest accordingly.

Apply the configuration:

```bash
kubectl apply -f custom-resources.yaml
```

Wait for Calico to start:

```bash
kubectl get pods -n tigera-operator
kubectl get pods -n calico-system -w
```

Press `Ctrl+C` to stop watching once the Calico Pods are ready.

## 7. Join both worker nodes

Run the following on `k8s-worker1` and `k8s-worker2`, not on the control plane.

Use the exact `kubeadm join` command printed by your successful `kubeadm init`. It will look similar to this:

```bash
sudo kubeadm join 192.168.10.11:6443 \
  --token <TOKEN> \
  --discovery-token-ca-cert-hash sha256:<CA_CERT_HASH> \
  --cri-socket=unix:///run/containerd/containerd.sock
```

Replace `<TOKEN>` and `<CA_CERT_HASH>` with the actual values. These are placeholders, not literal values to run.

If you didn't save the command, generate a new one on `k8s-master`:

```bash
kubeadm token create --print-join-command
```

Append the CRI socket option to the generated command:

```bash
--cri-socket=unix:///run/containerd/containerd.sock
```

Execute the resulting command on each worker.

If `kubeadm join` fails on a worker, the same reset procedure as in section 5.3 applies: run `sudo kubeadm reset --cri-socket=unix:///run/containerd/containerd.sock` and `sudo rm -rf /etc/cni/net.d`, then retry. The `$HOME/.kube` cleanup is not needed on workers.

## 8. Verify the cluster

Return to `k8s-master`.

### 8.1 Check node status

```bash
kubectl get nodes -o wide
```

Expected result after networking and node registration finish:

```
NAME          STATUS   ROLES           VERSION
k8s-master    Ready    control-plane   v1.37.x
k8s-worker1   Ready    <none>          v1.37.x
k8s-worker2   Ready    <none>          v1.37.x
```

The exact ages, IPs, and patch versions depend on your installation.

### 8.2 Check system Pods

```bash
kubectl get pods -A
```

Pay particular attention to:

```bash
kubectl get pods -n kube-system
kubectl get pods -n calico-system
```

The API server, scheduler, controller manager, etcd, kube-proxy (if enabled), and Calico components should be healthy.

### 8.3 Deploy a test application

Create a small Nginx deployment:

```bash
kubectl create deployment nginx --image=nginx:stable
kubectl scale deployment nginx --replicas=3
```

Expose it internally:

```bash
kubectl expose deployment nginx \
  --port=80 \
  --target-port=80 \
  --type=ClusterIP
```

Check the Pods and Service:

```bash
kubectl get deployments
kubectl get pods -o wide
kubectl get svc nginx
```

The three Nginx Pods should become `Running`, with Pods scheduled across the available nodes where scheduling permits.

Test the Service from a temporary Pod:

```bash
kubectl run curl-test \
  --image=curlimages/curl:latest \
  --restart=Never \
  --rm -it \
  --curl -sS http://nginx
```

You should receive the Nginx welcome page's HTML. If the test Pod is still starting, wait briefly and retry.

## 9. Troubleshooting checklist

| Symptom                                 | What to check                                                                                  |
| --------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Node stays `NotReady`                   | `kubectl describe node k8s-worker1`; inspect Calico Pods and kubelet logs                      |
| `kubeadm init` fails                    | `sudo journalctl -u kubelet -xe`; check containerd and image pulls                             |
| `CRI v1 runtime API is not implemented` | Check containerd's CRI plugin and `/etc/containerd/config.toml`                                |
| Worker cannot join                      | Check TCP 6443 reachability, token expiry, firewall rules, and time synchronization            |
| Calico Pods fail                        | Check Pod CIDR consistency, CNI configuration, kernel modules, and NetworkManager interference |
| Nginx Pods cannot start                 | `kubectl describe pod <pod-name>` and `kubectl get events -A --sort-by=.lastTimestamp`         |

For a more detailed containerd diagnosis:

```bash
sudo systemctl status containerd --no-pager
sudo journalctl -u containerd -n 100 --no-pager
sudo crictl --runtime-endpoint \
  unix:///run/containerd/containerd.sock info
```

If `crictl` isn't installed, install the appropriate `cri-tools` package from the Kubernetes repository or use the containerd logs first.

Official references:

- Kubernetes kubeadm installation guide — [Install kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/?utm_source=chatgpt.com)
- Kubernetes cluster creation guide — [Create a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/?utm_source=chatgpt.com)
- Containerd runtime configuration — [Container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/?utm_source=chatgpt.com)
- Calico installation guide — [Install Calico on premises](https://docs.tigera.io/calico/latest/getting-started/kubernetes/self-managed-onprem/onpremises?utm_source=chatgpt.com)

One important operational note: a single control-plane node is not highly available. If `k8s-master` goes down, your existing workloads may continue running, but cluster management and scheduling are affected. For a production cluster that needs control-plane availability, consider three control-plane nodes and a highly available API endpoint instead.

## 10. Final configuration consistency check

One correction to the examples above: the initial architecture lists `10.244.0.0/16`, while the initialization and Calico sections use `192.168.0.0/16`. Choose one Pod CIDR and use it consistently.

For example, if you choose `10.244.0.0/16`, use it in `kubeadm init`:

```bash
--pod-network-cidr=10.244.0.0/16
```

Then edit `custom-resources.yaml` so the Calico `IPPool` CIDR is also:

```yaml
cidr: 10.244.0.0/16
```

Only do this before applying the Calico configuration on a fresh cluster. First ensure that the range does not overlap with your LAN, VPN, or other routed networks.

That consistency is essential for Pod networking to work correctly.
