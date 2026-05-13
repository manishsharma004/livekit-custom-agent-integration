from __future__ import annotations

from pathlib import Path

import yaml


def test_voice_agent_manifest_uses_cluster_dns_with_host_network():
    manifest = yaml.safe_load(Path("k8s/agent.yaml").read_text())
    pod_spec = manifest["spec"]["template"]["spec"]

    assert pod_spec["hostNetwork"] is True
    assert pod_spec["dnsPolicy"] == "ClusterFirstWithHostNet"
    assert "dnsConfig" not in pod_spec
