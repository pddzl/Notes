cd ~/vmware-alarm-aggregation

make image-import                          # build binary + image, load into containerd

make deploy NAMESPACE=vmware-log-monitor                 # secret + configmap + deployment

kubectl -n vmware-log-monitor rollout status deploy/vmware-vcenter


kubectl -n vmware-log-monitor logs deploy/vmware-vcenter | head


### Enter the pod

```shell
kubectl -n vmware-log-monitor exec -it deploy/vmware-vcenter -- sh
```

(`deploy/vmware-vcenter` targets the pod via the Deployment; you can also use the pod name, e.g. `vmware-vcenter-84f89c88f6-xxxxx`. Use `bash` instead of `sh` if the image has it.)


### If you just want the pods to pick up changes / retry

Since the Deployment spec itself is unchanged, kick the pods:

bash

```bash
kubectl -n vmware-log-monitor rollout restart deploy/vmware-vcenter
kubectl -n vmware-log-monitor rollout status  deploy/vmware-vcenter
```

This deletes pods and creates new ones — new pods will re-resolve the image, which fixes your earlier `ErrImageNeverPull` situation _if_ the image is now present on the node where they land.

## If you rebuilt the image (`localhost/vmware-vcenter:latest`) and want pods to run the new build

With `imagePullPolicy: Never` + a `:latest` tag there's a gotcha: kubelet resolves images **by name**, and it may consider the old local copy "present" even after you've imported a rebuilt one. The safe sequence on the pod's node:

bash

```bash
# remove the old copy so kubelet can't reuse it
crictl rmi localhost/vmware-vcenter:latest
ctr  -n k8s.io images import /tmp/vmware-vcenter.tar   # import the fresh build

# then restart
kubectl -n vmware-log-monitor rollout restart deploy/vmware-vcenter
kubectl -n vmware-log-monitor get pods -w
```

(Longer-term, this dance is why immutable tags like `:v1.2.3` beat `:latest` — the Deployment spec change alone triggers a rollout, no pod-deletion rituals.)