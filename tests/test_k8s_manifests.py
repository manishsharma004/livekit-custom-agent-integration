from __future__ import annotations

from pathlib import Path


def test_voice_agent_manifest_uses_cluster_dns_with_host_network():
    manifest = Path("k8s/agent.yaml").read_text()

    assert "hostNetwork: true" in manifest
    assert "dnsPolicy: ClusterFirstWithHostNet" in manifest
    assert "dnsPolicy: None" not in manifest
