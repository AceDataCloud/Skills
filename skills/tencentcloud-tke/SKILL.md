---
name: tencentcloud-tke
description: |
  Manage Tencent Cloud TKE (Tencent Kubernetes Engine) clusters and
  workloads. Use when the user asks to: list clusters, check cluster /
  node health, list pods or services, scale a Deployment, do a rolling
  restart, fetch kubeconfig, view recent K8s events, manage node pools.
  Combines the official tencentcloud-sdk-python TKE client (cluster
  metadata) with kubectl for in-cluster operations.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
connections: [tencentcloud]
---

# Tencent Cloud TKE (Kubernetes)

Manage TKE clusters and the workloads inside them.

> **Setup:** See [tencentcloud authentication](../_shared/tencentcloud.md). Cluster discovery and kubeconfig retrieval go through the SDK; everything inside the cluster (pods, services, scale, restart) goes through `kubectl` against the kubeconfig we fetch.

## CLI (preferred)

The skill ships [`scripts/tke.py`](scripts/tke.py) — wraps cluster discovery, kubeconfig retrieval, and the most common in-cluster operations.

```bash
# $SKILL_DIR can point at another skill loaded this turn — anchor on our own
# script (re-run this at the top of every fresh-shell Bash block).
TKE="$SKILL_DIR/scripts/tke.py"; [ -f "$TKE" ] || TKE=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tke.py' 2>/dev/null | head -1)
[ -f "$TKE" ] || { echo "tencentcloud-tke script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }

python3 $TKE clusters                                              # list clusters
python3 $TKE cluster cls-xxxxxxxx                                  # one cluster's details
python3 $TKE nodes cls-xxxxxxxx
python3 $TKE pools cls-xxxxxxxx                                    # node pools
python3 $TKE kubeconfig cls-xxxxxxxx --save ~/.kube/config-tke     # write kubeconfig
python3 $TKE workloads cls-xxxxxxxx -n my-namespace
python3 $TKE pods cls-xxxxxxxx -n my-namespace
python3 $TKE events cls-xxxxxxxx -n my-namespace                   # recent events
python3 $TKE scale cls-xxxxxxxx -n my-namespace --name my-deploy --replicas 4
python3 $TKE restart cls-xxxxxxxx -n my-namespace --name my-deploy
```

In-cluster commands shell out to `kubectl` against an SDK-fetched kubeconfig. `kubectl` must be installed in the sandbox (`pip install` doesn't ship it).

## When to Use

- List TKE clusters across regions
- Check node health and node-pool resource usage
- List Deployments / StatefulSets / DaemonSets in a namespace
- List Services / Pods / recent Events
- Scale a workload up or down
- Rolling restart a Deployment (e.g. after a config change)
- Fetch kubeconfig for ad-hoc `kubectl` work

## Dependencies

```bash
pip install tencentcloud-sdk-python
brew install kubectl   # macOS;  apt install kubectl on Debian/Ubuntu
```

## Quick start — list clusters

```python
import os
from tencentcloud.common import credential
from tencentcloud.tke.v20180525 import tke_client, models

cred = credential.EnvironmentVariableCredential().get_credential()
client = tke_client.TkeClient(cred, os.environ["TENCENTCLOUD_REGION"])

req = models.DescribeClustersRequest()
req.Limit = 100
resp = client.DescribeClusters(req)
for c in resp.Clusters:
    print(c.ClusterId, c.ClusterName, c.ClusterStatus, c.ClusterVersion)
```

> Cluster IDs look like `cls-xxxxxxxx`. The `ap-hongkong` region typically holds the production clusters; `DescribeClusters` is region-scoped — call it per region you care about.

## Workflows

### Get cluster details + worker node count

```python
req = models.DescribeClustersRequest()
req.ClusterIds = ["cls-xxxxxxxx"]
resp = client.DescribeClusters(req)
c = resp.Clusters[0]
print(c.ClusterName, c.ClusterStatus, c.ClusterNodeNum, c.ClusterVersion)
```

### List worker nodes (and their CVM instance types)

```python
req = models.DescribeClusterInstancesRequest()
req.ClusterId = "cls-xxxxxxxx"
req.Limit = 100
resp = client.DescribeClusterInstances(req)
for i in resp.InstanceSet:
    print(i.InstanceId, i.InstanceRole, i.InstanceState, i.NodePoolId)
```

### Fetch kubeconfig

```python
req = models.DescribeClusterKubeconfigRequest()
req.ClusterId = "cls-xxxxxxxx"
req.IsExtranet = True            # False for VPC-internal kubeconfig
resp = client.DescribeClusterKubeconfig(req)

# Save and use immediately
import os, pathlib
kubeconfig = pathlib.Path(os.path.expanduser("~/.kube/config-tke-cls-xxxxxxxx"))
kubeconfig.parent.mkdir(parents=True, exist_ok=True)
kubeconfig.write_text(resp.Kubeconfig)
print("export KUBECONFIG=" + str(kubeconfig))
```

> Many TKE clusters expose only the **internal** API endpoint by default. If `IsExtranet=True` returns an empty / unusable config, the cluster's public API access isn't enabled — set `IsExtranet=False` and run `kubectl` from a host inside the same VPC (e.g. CVM, jump host).

### Run kubectl commands (with the fetched kubeconfig)

```python
import subprocess

KUBECONFIG = os.path.expanduser("~/.kube/config-tke-cls-xxxxxxxx")
NS = "acedatacloud"

def kubectl(*args):
    return subprocess.run(
        ["kubectl", f"--kubeconfig={KUBECONFIG}", *args],
        check=True, capture_output=True, text=True,
    ).stdout

print(kubectl("get", "pods", "-n", NS))
print(kubectl("get", "deploy", "-n", NS))
print(kubectl("get", "svc", "-n", NS))
print(kubectl("get", "events", "-n", NS, "--sort-by=.lastTimestamp"))
```

### Describe a misbehaving pod

```python
print(kubectl("describe", "pod", "<pod-name>", "-n", NS))
print(kubectl("logs", "<pod-name>", "-n", NS, "--tail=200"))
```

### Scale a Deployment

```python
# To 4 replicas. Confirm with the user before running for prod workloads.
print(kubectl("scale", "deploy/platform-backend", "-n", NS, "--replicas=4"))
```

### Rolling restart a Deployment

```python
# Forces every pod to recycle through the rolling-update strategy.
print(kubectl("rollout", "restart", "deploy/platform-backend", "-n", NS))
print(kubectl("rollout", "status", "deploy/platform-backend", "-n", NS, "--timeout=300s"))
```

### List node pools (TKE concept above raw nodes)

```python
req = models.DescribeClusterNodePoolsRequest()
req.ClusterId = "cls-xxxxxxxx"
resp = client.DescribeClusterNodePools(req)
for np in resp.NodePoolSet:
    print(np.NodePoolId, np.Name, np.LifeState, np.DesiredNodesNum, np.AutoscalingGroupId)
```

## Troubleshooting flow

```
1. python: DescribeClusters → cluster status / version
2. python: DescribeClusterInstances → any nodes "failed" / "running"
3. kubectl get events → recent failures (image pulls, scheduling, OOM)
4. kubectl get pods → which pod is in CrashLoopBackOff / ImagePullBackOff
5. kubectl describe pod <name> → conditions, events on the pod
6. kubectl logs <name> --tail=200 → application logs
7. (optional) tencentcloud-cls skill → CLS query for the same window
```

## Important reminders

- **Confirm scale / restart actions** with the user before running for production workloads. A `replicas=0` typo takes the service down.
- **Kubeconfigs contain a long-lived bearer token.** Treat the file like a credential — `chmod 600`, never commit, regenerate after offboarding people.
- **Internal vs external endpoint:** `IsExtranet=False` gives a kubeconfig usable only from inside the cluster VPC. From a laptop, use `IsExtranet=True` and ensure the cluster has a public API endpoint enabled (TKE console → Cluster → Basic Info → API Server access).
- **Region matters.** Cluster `cls-xxxxxxxx` in `ap-hongkong` is invisible from a TKE client constructed for `ap-guangzhou`.

## Console links

- TKE console: <https://console.cloud.tencent.com/tke2/cluster>
- API reference: <https://www.tencentcloud.com/document/product/457/31862>
