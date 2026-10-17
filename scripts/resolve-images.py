"""Freeze official Docker image manifest digests without needing a Docker daemon.

Only explicit --write updates the lock; ordinary execution verifies existing digests.
No image layers are downloaded. Run before testing, never during confirmatory runs.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

IMAGES = {
    "PYTHON_IMAGE": ("library/python", "3.12.14-slim-bookworm"),
    "POSTGIS_IMAGE": ("postgis/postgis", "16-3.5"),
    "METABASE_IMAGE": ("metabase/metabase", "v0.64.1"),
}
ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


def resolve(repository: str, reference: str) -> tuple[str, list[str]]:
    query = urlencode({"service": "registry.docker.io", "scope": f"repository:{repository}:pull"})
    with urlopen("https://auth.docker.io/token?" + query, timeout=30) as response:
        token = json.load(response)["token"]
    request = Request(
        f"https://registry-1.docker.io/v2/{repository}/manifests/{reference}",
        headers={"Authorization": f"Bearer {token}", "Accept": ACCEPT},
    )
    with urlopen(request, timeout=30) as response:
        digest = response.headers["Docker-Content-Digest"]
        manifest = json.load(response)
    platforms = [
        f"{item['platform']['os']}/{item['platform']['architecture']}"
        for item in manifest.get("manifests", [])
        if item.get("platform", {}).get("os") not in (None, "unknown")
    ]
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise ValueError("Registry did not return a valid SHA256 digest")
    return digest, sorted(set(platforms))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Explicitly update image digests")
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / "docker" / "images.lock.json"
    if args.write:
        images = {}
        for key, (repository, tag) in IMAGES.items():
            digest, platforms = resolve(repository, tag)
            images[key] = {
                "repository": repository,
                "tag": tag,
                "reference": f"{repository}:{tag}@{digest}",
                "digest": digest,
                "declared_platforms": platforms,
            }
        destination.write_text(
            json.dumps(
                {"resolved_at_utc": datetime.now(UTC).isoformat(), "images": images}, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        print("Image manifest digests pinned; runtime validation still required.")
    else:
        images = json.loads(destination.read_text(encoding="utf-8"))["images"]
        for key, entry in images.items():
            digest, _ = resolve(entry["repository"], entry["digest"])
            if digest != entry["digest"]:
                raise ValueError(f"Digest mismatch: {key}")
        print("Pinned manifests are available in the registry.")


if __name__ == "__main__":
    main()
