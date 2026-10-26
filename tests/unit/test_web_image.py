"""The Next.js image and its release (RS-77).

The Dockerfile, compose.yaml and the workflows are checked as text. The docker job builds
the image and checks the running containers (user, read-only root, health) for real.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
COMPOSE = (ROOT / "compose.yaml").read_text(encoding="utf-8")
CI = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
RELEASE = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")


def _service(name: str) -> str:
    return COMPOSE.split(f"\n  {name}:\n", 1)[1].split("\n\n", 1)[0]


# Criterion 1: the web image builds in stages, runs as non-root with a read-only root
# filesystem, and both containers become healthy.


@pytest.mark.req("RS-77", criterion=1)
def test_the_web_image_builds_in_stages_and_runs_as_node() -> None:
    stages = re.findall(r"^FROM \S+ AS (\w+)$", DOCKERFILE, re.M)
    assert len(stages) >= 3
    assert stages[-1] == "runtime"
    runtime = DOCKERFILE.split("AS runtime", 1)[1]
    assert re.search(r"^USER node$", runtime, re.M)
    assert "HEALTHCHECK" in runtime


@pytest.mark.req("RS-77", criterion=1)
def test_the_web_service_has_a_read_only_root_without_privileges() -> None:
    web = _service("web")
    assert "read_only: true" in web
    assert "cap_drop: [ALL]" in web
    assert "no-new-privileges:true" in web


@pytest.mark.req("RS-77", criterion=1)
def test_the_docker_job_waits_for_both_containers_and_checks_the_web_user() -> None:
    for service in ("api", "web"):
        assert f'"$(docker compose ps -q {service})")" = healthy' in CI
    assert 'test "$(docker compose exec -T web id -u)" != 0' in CI


# Criterion 2: a release pushes both images with the same tag, SBOM and provenance.


@pytest.mark.req("RS-77", criterion=2)
def test_a_release_pushes_both_images_with_the_same_tags_sbom_and_provenance() -> None:
    publish = RELEASE.split("\n  publish-image:\n", 1)[1].split("\n\n  ", 1)[0]
    metas = re.findall(r"images: (.+)\n\s+tags: \|\n((?:\s+type=.*\n)+)", publish)
    assert [image for image, _ in metas] == [
        "ghcr.io/${{ github.repository }}",
        "ghcr.io/${{ github.repository }}-web",
    ]
    assert metas[0][1] == metas[1][1]
    pushes = publish.split("docker/build-push-action")[1:]
    assert len(pushes) == 2
    for push in pushes:
        assert "push: true" in push
        assert "provenance: mode=max" in push
        assert "sbom: true" in push
