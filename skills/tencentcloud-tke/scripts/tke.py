#!/usr/bin/env python3
"""
Tencent Cloud TKE (Tencent Kubernetes Engine) Management Tool

Manage TKE clusters, nodes, workloads, and services via Tencent Cloud API.

Usage:
  python3 $SKILL_DIR/scripts/tke.py clusters [--region REGION]
  python3 $SKILL_DIR/scripts/tke.py cluster <cluster_id> [--region REGION]
  python3 $SKILL_DIR/scripts/tke.py nodes <cluster_id> [--region REGION] [--pool POOL_ID]
  python3 $SKILL_DIR/scripts/tke.py pools <cluster_id> [--region REGION]
  python3 $SKILL_DIR/scripts/tke.py workloads <cluster_id> --namespace <ns> [--region REGION] [--kind Deployment|StatefulSet|DaemonSet]
  python3 $SKILL_DIR/scripts/tke.py services <cluster_id> --namespace <ns> [--region REGION]
  python3 $SKILL_DIR/scripts/tke.py pods <cluster_id> --namespace <ns> [--region REGION] [--name POD_NAME]
  python3 $SKILL_DIR/scripts/tke.py events <cluster_id> --namespace <ns> [--region REGION]
  python3 $SKILL_DIR/scripts/tke.py kubeconfig <cluster_id> [--region REGION] [--internal]
  python3 $SKILL_DIR/scripts/tke.py scale <cluster_id> --namespace <ns> --name <name> --replicas <n> [--region REGION] [--kind Deployment]
  python3 $SKILL_DIR/scripts/tke.py restart <cluster_id> --namespace <ns> --name <name> [--region REGION] [--kind Deployment]

Environment:
  Reads TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY from
  sandbox env vars (TENCENTCLOUD_SECRET_ID / SECRET_KEY)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

DEFAULT_REGION = os.environ.get("TENCENTCLOUD_REGION", "ap-hongkong")




def get_client(region):
    try:
        from tencentcloud.common import credential
        from tencentcloud.tke.v20180525 import tke_client
    except ImportError:
        print(
            "ERROR: tencentcloud-sdk-python not installed.\n"
            "Run: pip3 install tencentcloud-sdk-python",
            file=sys.stderr,
        )
        sys.exit(1)

    secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")
    if not secret_id or not secret_key:
        print(
            "ERROR: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set.",
            file=sys.stderr,
        )
        sys.exit(1)

    cred = credential.Credential(secret_id, secret_key)
    return tke_client.TkeClient(cred, region)


def pp(data):
    """Pretty-print JSON data."""
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def cmd_clusters(args):
    """List all TKE clusters."""
    from tencentcloud.tke.v20180525 import models

    client = get_client(args.region)
    req = models.DescribeClustersRequest()
    req.Limit = 100
    resp = client.DescribeClusters(req)
    data = json.loads(resp.to_json_string())

    clusters = data.get("Clusters", [])
    if not clusters:
        print("No clusters found.")
        return

    print(f"Found {data.get('TotalCount', len(clusters))} cluster(s):\n")
    for c in clusters:
        status = c.get("ClusterStatus", "Unknown")
        emoji = "●" if status == "Running" else "○"
        print(f"  {emoji} {c.get('ClusterId', 'N/A'):20s} {c.get('ClusterName', 'N/A'):30s} "
              f"v{c.get('ClusterVersion', '?'):10s} {status:12s} "
              f"Nodes: {c.get('ClusterNodeNum', 0)}")


def cmd_cluster(args):
    """Get cluster details."""
    from tencentcloud.tke.v20180525 import models

    client = get_client(args.region)
    req = models.DescribeClustersRequest()
    req.ClusterIds = [args.cluster_id]
    resp = client.DescribeClusters(req)
    data = json.loads(resp.to_json_string())

    clusters = data.get("Clusters", [])
    if not clusters:
        print(f"Cluster {args.cluster_id} not found.")
        return

    pp(clusters[0])


def cmd_nodes(args):
    """List cluster nodes (instances)."""
    from tencentcloud.tke.v20180525 import models

    client = get_client(args.region)
    req = models.DescribeClusterInstancesRequest()
    req.ClusterId = args.cluster_id
    req.Limit = 100
    if args.pool:
        req.Filters = [{"Name": "nodepool-id", "Values": [args.pool]}]
    resp = client.DescribeClusterInstances(req)
    data = json.loads(resp.to_json_string())

    instances = data.get("InstanceSet", [])
    if not instances:
        print("No nodes found.")
        return

    print(f"Found {data.get('TotalCount', len(instances))} node(s):\n")
    for n in instances:
        state = n.get("InstanceState", "Unknown")
        emoji = "●" if state == "running" else "○"
        print(f"  {emoji} {n.get('InstanceId', 'N/A'):22s} {n.get('InstanceRole', 'N/A'):10s} "
              f"{n.get('LanIP', 'N/A'):16s} {state:12s} "
              f"CPU: {n.get('CPU', '?')}  Mem: {n.get('Memory', '?')}GB")


def cmd_pools(args):
    """List cluster node pools."""
    from tencentcloud.tke.v20180525 import models

    client = get_client(args.region)
    req = models.DescribeClusterNodePoolsRequest()
    req.ClusterId = args.cluster_id
    resp = client.DescribeClusterNodePools(req)
    data = json.loads(resp.to_json_string())

    pools = data.get("NodePoolSet", [])
    if not pools:
        print("No node pools found.")
        return

    print(f"Found {len(pools)} node pool(s):\n")
    for p in pools:
        status = p.get("LifeState", "Unknown")
        print(f"  {p.get('NodePoolId', 'N/A'):30s} {p.get('Name', 'N/A'):30s} "
              f"Nodes: {p.get('NodeCountSummary', {}).get('ManuallyAdded', {}).get('Total', '?')}  "
              f"Status: {status}")


def cmd_kubeconfig(args):
    """Get cluster kubeconfig."""
    from tencentcloud.tke.v20180525 import models

    client = get_client(args.region)
    req = models.DescribeClusterKubeconfigRequest()
    req.ClusterId = args.cluster_id
    req.IsExtranet = not args.internal
    resp = client.DescribeClusterKubeconfig(req)
    data = json.loads(resp.to_json_string())

    kubeconfig = data.get("Kubeconfig", "")
    if not kubeconfig:
        print("ERROR: Could not retrieve kubeconfig. Ensure cluster endpoint is enabled.")
        return

    if args.save:
        path = Path(args.save).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(kubeconfig)
        print(f"Kubeconfig saved to: {path}")
    else:
        print(kubeconfig)


def _get_kubeconfig_path(args):
    """Helper to get a temporary kubeconfig for kubectl commands."""
    from tencentcloud.tke.v20180525 import models

    client = get_client(args.region)
    req = models.DescribeClusterKubeconfigRequest()
    req.ClusterId = args.cluster_id
    req.IsExtranet = True
    resp = client.DescribeClusterKubeconfig(req)
    data = json.loads(resp.to_json_string())

    kubeconfig = data.get("Kubeconfig", "")
    if not kubeconfig:
        print("ERROR: Could not retrieve kubeconfig.", file=sys.stderr)
        sys.exit(1)

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    tmp.write(kubeconfig)
    tmp.close()
    return tmp.name


def _run_kubectl(kubeconfig_path, *kubectl_args):
    """Run kubectl with the given kubeconfig."""
    cmd = ["kubectl", f"--kubeconfig={kubeconfig_path}"] + list(kubectl_args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"kubectl error: {result.stderr}", file=sys.stderr)
            return None
        return result.stdout
    except FileNotFoundError:
        print("ERROR: kubectl not found. Install it first.", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("ERROR: kubectl command timed out.", file=sys.stderr)
        return None


def cmd_workloads(args):
    """List workloads in a namespace (via kubectl)."""
    kc = _get_kubeconfig_path(args)
    try:
        kind = args.kind or "Deployment"
        output = _run_kubectl(kc, "get", kind.lower(), "-n", args.namespace, "-o", "wide")
        if output:
            print(f"=== {kind}s in namespace '{args.namespace}' ===\n")
            print(output)
    finally:
        os.unlink(kc)


def cmd_services(args):
    """List services in a namespace (via kubectl)."""
    kc = _get_kubeconfig_path(args)
    try:
        output = _run_kubectl(kc, "get", "svc", "-n", args.namespace, "-o", "wide")
        if output:
            print(f"=== Services in namespace '{args.namespace}' ===\n")
            print(output)
    finally:
        os.unlink(kc)


def cmd_pods(args):
    """List or describe pods in a namespace (via kubectl)."""
    kc = _get_kubeconfig_path(args)
    try:
        if args.name:
            output = _run_kubectl(kc, "describe", "pod", args.name, "-n", args.namespace)
        else:
            output = _run_kubectl(kc, "get", "pods", "-n", args.namespace, "-o", "wide")
        if output:
            print(output)
    finally:
        os.unlink(kc)


def cmd_events(args):
    """Get recent events in a namespace (via kubectl)."""
    kc = _get_kubeconfig_path(args)
    try:
        output = _run_kubectl(kc, "get", "events", "-n", args.namespace,
                              "--sort-by=.lastTimestamp", "-o", "wide")
        if output:
            print(f"=== Events in namespace '{args.namespace}' ===\n")
            print(output)
    finally:
        os.unlink(kc)


def cmd_scale(args):
    """Scale a workload."""
    kc = _get_kubeconfig_path(args)
    try:
        kind = args.kind or "deployment"
        output = _run_kubectl(kc, "scale", f"{kind}/{args.name}",
                              f"--replicas={args.replicas}", "-n", args.namespace)
        if output:
            print(output)
    finally:
        os.unlink(kc)


def cmd_restart(args):
    """Restart a workload (rollout restart)."""
    kc = _get_kubeconfig_path(args)
    try:
        kind = args.kind or "deployment"
        output = _run_kubectl(kc, "rollout", "restart", f"{kind}/{args.name}",
                              "-n", args.namespace)
        if output:
            print(output)
    finally:
        os.unlink(kc)


def main():
    parser = argparse.ArgumentParser(
        description="Tencent Cloud TKE Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--region", "-r", default=DEFAULT_REGION, help=f"Region (default: {DEFAULT_REGION})")
    sub = parser.add_subparsers(dest="command", required=True)

    # clusters
    sub.add_parser("clusters", help="List all clusters")

    # cluster
    p = sub.add_parser("cluster", help="Get cluster details")
    p.add_argument("cluster_id", help="Cluster ID (e.g. cls-xxxxxxxx)")

    # nodes
    p = sub.add_parser("nodes", help="List cluster nodes")
    p.add_argument("cluster_id")
    p.add_argument("--pool", help="Filter by node pool ID")

    # pools
    p = sub.add_parser("pools", help="List node pools")
    p.add_argument("cluster_id")

    # kubeconfig
    p = sub.add_parser("kubeconfig", help="Get cluster kubeconfig")
    p.add_argument("cluster_id")
    p.add_argument("--internal", action="store_true", help="Use internal endpoint")
    p.add_argument("--save", help="Save to file path (e.g. ~/.kube/config-tke)")

    # workloads (kubectl)
    p = sub.add_parser("workloads", help="List workloads (Deployment/StatefulSet/DaemonSet)")
    p.add_argument("cluster_id")
    p.add_argument("--namespace", "-n", required=True, help="Kubernetes namespace")
    p.add_argument("--kind", "-k", default="Deployment", help="Workload kind (default: Deployment)")

    # services (kubectl)
    p = sub.add_parser("services", help="List services in namespace")
    p.add_argument("cluster_id")
    p.add_argument("--namespace", "-n", required=True, help="Kubernetes namespace")

    # pods (kubectl)
    p = sub.add_parser("pods", help="List or describe pods")
    p.add_argument("cluster_id")
    p.add_argument("--namespace", "-n", required=True, help="Kubernetes namespace")
    p.add_argument("--name", help="Pod name to describe")

    # events (kubectl)
    p = sub.add_parser("events", help="Get recent events")
    p.add_argument("cluster_id")
    p.add_argument("--namespace", "-n", required=True, help="Kubernetes namespace")

    # scale
    p = sub.add_parser("scale", help="Scale a workload")
    p.add_argument("cluster_id")
    p.add_argument("--namespace", "-n", required=True)
    p.add_argument("--name", required=True, help="Workload name")
    p.add_argument("--replicas", required=True, type=int, help="Target replica count")
    p.add_argument("--kind", default="deployment", help="Workload kind (default: deployment)")

    # restart
    p = sub.add_parser("restart", help="Restart a workload (rollout restart)")
    p.add_argument("cluster_id")
    p.add_argument("--namespace", "-n", required=True)
    p.add_argument("--name", required=True, help="Workload name")
    p.add_argument("--kind", default="deployment", help="Workload kind (default: deployment)")

    args = parser.parse_args()

    commands = {
        "clusters": cmd_clusters,
        "cluster": cmd_cluster,
        "nodes": cmd_nodes,
        "pools": cmd_pools,
        "kubeconfig": cmd_kubeconfig,
        "workloads": cmd_workloads,
        "services": cmd_services,
        "pods": cmd_pods,
        "events": cmd_events,
        "scale": cmd_scale,
        "restart": cmd_restart,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
