"""Verify infrastructure exposure and preservation of the approved source artifacts."""

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_original_phase7_hashes_preserved():
    for line in (ROOT / "SIPRE_FASE7_SHA256.txt").read_text(encoding="utf-8").splitlines():
        expected, name = line.split(maxsplit=1)
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected


def test_database_has_no_host_port_and_api_is_local():
    configuration = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = configuration["services"]
    assert "ports" not in services["db"]
    for service in ("api", "metabase"):
        assert all(port.startswith("127.0.0.1:") for port in services[service]["ports"])
    assert services["api"]["depends_on"]["migrate"]["condition"] == (
        "service_completed_successfully"
    )
    assert services["api"]["read_only"] is True


def test_image_lock_contains_immutable_digests():
    entries = json.loads((ROOT / "docker/images.lock.json").read_text(encoding="utf-8"))["images"]
    assert len(entries) == 3
    for entry in entries.values():
        assert entry["reference"].endswith("@" + entry["digest"])
        assert len(entry["digest"]) == 71
        assert "latest" not in entry["reference"]
