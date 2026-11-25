"""Render an opt-in seller tool; this does not change the generic Hermes chart."""

import argparse
import json
import re
from pathlib import Path

import yaml


def render(
    *,
    name,
    namespace,
    image,
    receiver_label,
    config,
    pull_secret,
    allow_client_egress=False,
):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,50}", name):
        raise ValueError("Use a Kubernetes-safe name")
    if not re.fullmatch(r".+@sha256:[0-9a-f]{64}", image):
        raise ValueError("Use a verified digest-pinned image with python3")
    if not receiver_label or not all(
        isinstance(k, str) and k and isinstance(v, str) and v
        for k, v in receiver_label.items()
    ):
        raise ValueError("Provide the exact receiving Pod label")
    labels = {"app.kubernetes.io/name": name}

    def meta():
        return {"name": name, "namespace": namespace}

    documents = [
        {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": meta(),
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "storageClassName": "cbs-ssd",
                "resources": {"requests": {"storage": "1Gi"}},
            },
        },
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": meta(),
            "data": {
                "broker.py": Path(__file__).with_name("broker.py").read_text(),
                "config.json": json.dumps(config),
            },
        },
        {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": meta(),
            "spec": {
                "replicas": 1,
                "strategy": {"type": "Recreate"},
                "selector": {"matchLabels": labels},
                "template": {
                    "metadata": {"labels": labels},
                    "spec": {
                        "automountServiceAccountToken": False,
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 10000,
                            "runAsGroup": 10000,
                            "fsGroup": 10000,
                            "seccompProfile": {"type": "RuntimeDefault"},
                        },
                        "imagePullSecrets": [{"name": pull_secret}],
                        "containers": [
                            {
                                "name": "fulfillment",
                                "image": image,
                                "command": ["python3", "/config/broker.py"],
                                "env": [
                                    {"name": "PYTHONDONTWRITEBYTECODE", "value": "1"}
                                ],
                                "securityContext": {
                                    "allowPrivilegeEscalation": False,
                                    "readOnlyRootFilesystem": True,
                                    "capabilities": {"drop": ["ALL"]},
                                },
                                "ports": [{"containerPort": 8031, "name": "http"}],
                                "readinessProbe": {
                                    "httpGet": {"path": "/health", "port": "http"},
                                    "initialDelaySeconds": 2,
                                },
                                "resources": {
                                    "requests": {"cpu": "50m", "memory": "64Mi"},
                                    "limits": {"cpu": "500m", "memory": "256Mi"},
                                },
                                "volumeMounts": [
                                    {"name": "inventory", "mountPath": "/data"},
                                    {
                                        "name": "config",
                                        "mountPath": "/config",
                                        "readOnly": True,
                                    },
                                    {
                                        "name": "credentials",
                                        "mountPath": "/secrets",
                                        "readOnly": True,
                                    },
                                ],
                            }
                        ],
                        "volumes": [
                            {
                                "name": "inventory",
                                "persistentVolumeClaim": {"claimName": name},
                            },
                            {"name": "config", "configMap": {"name": name}},
                            {
                                "name": "credentials",
                                "secret": {"secretName": name, "defaultMode": 0o440},
                            },
                        ],
                    },
                },
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": meta(),
            "spec": {
                "selector": labels,
                "ports": [{"port": 8031, "targetPort": "http"}],
            },
        },
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": meta(),
            "spec": {
                "podSelector": {"matchLabels": labels},
                "policyTypes": ["Ingress"],
                "ingress": [
                    {
                        "from": [{"podSelector": {"matchLabels": receiver_label}}],
                        "ports": [{"protocol": "TCP", "port": 8031}],
                    }
                ],
            },
        },
    ]
    if allow_client_egress:
        documents.append(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {"name": name + "-client", "namespace": namespace},
                "spec": {
                    "podSelector": {"matchLabels": receiver_label},
                    "policyTypes": ["Egress"],
                    "egress": [
                        {
                            "to": [{"podSelector": {"matchLabels": labels}}],
                            "ports": [{"protocol": "TCP", "port": 8031}],
                        }
                    ],
                },
            }
        )
    return documents


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for arg in (
        "name",
        "namespace",
        "image",
        "receiver-label",
        "config",
        "output",
        "pull-secret",
    ):
        parser.add_argument("--" + arg, required=True)
    parser.add_argument(
        "--allow-client-egress",
        action="store_true",
        help="Add the narrow tool route only when the receiving Pod already has egress isolation",
    )
    args = parser.parse_args()
    label_key, label_value = args.receiver_label.split("=", 1)
    documents = render(
        name=args.name,
        namespace=args.namespace,
        image=args.image,
        receiver_label={label_key: label_value},
        config=json.loads(Path(args.config).read_text()),
        pull_secret=args.pull_secret,
        allow_client_egress=args.allow_client_egress,
    )
    Path(args.output).write_text(yaml.safe_dump_all(documents, sort_keys=False))
