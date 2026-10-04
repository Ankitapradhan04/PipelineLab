"""Build the static report site that the `pages` job publishes to GitLab Pages.

Reads the artifacts produced by the `test` job (junit.xml, coverage.xml, htmlcov/),
asks the FastAPI app for its OpenAPI schema, and writes everything to ./public.
Standard library only, apart from importing the app itself.
"""

import html
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
sys.path.insert(0, str(ROOT))

STAGES = [
    ("lint", "ruff check and format"),
    ("test", "pytest, 90% coverage gate, Python 3.11 to 3.13"),
    ("security", "SAST, secret detection, pip-audit"),
    ("build", "Docker image, smoke test, push to registry"),
    ("deploy", "this page"),
]


def read_junit(path: Path) -> dict | None:
    if not path.exists():
        return None
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    for suite in ET.parse(path).getroot().iter("testsuite"):
        for key in ("tests", "failures", "errors", "skipped"):
            totals[key] += int(suite.get(key, 0))
        totals["time"] += float(suite.get("time", 0))
    totals["passed"] = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    return totals


def read_coverage(path: Path) -> float | None:
    if not path.exists():
        return None
    return round(float(ET.parse(path).getroot().get("line-rate", 0)) * 100, 1)


def read_endpoints() -> list[tuple[str, str, str]]:
    from app.main import app

    schema = app.openapi()
    (PUBLIC / "openapi.json").write_text(json.dumps(schema, indent=2))
    rows = []
    for route, methods in schema["paths"].items():
        for method, op in methods.items():
            rows.append((method.upper(), route, op.get("summary", "")))
    return rows


def stage_rail() -> str:
    items = []
    for name, detail in STAGES:
        items.append(
            f'<li><span class="dot"></span><strong>{html.escape(name)}</strong>'
            f"<span>{html.escape(detail)}</span></li>"
        )
    return "\n".join(items)


def endpoint_rows(rows: list[tuple[str, str, str]]) -> str:
    return "\n".join(
        f'<tr><td><code class="m m-{m.lower()}">{m}</code></td>'
        f"<td><code>{html.escape(p)}</code></td><td>{html.escape(s)}</td></tr>"
        for m, p, s in rows
    )


def main() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()

    junit = read_junit(ROOT / "junit.xml")
    coverage = read_coverage(ROOT / "coverage.xml")
    if (ROOT / "htmlcov").exists():
        shutil.copytree(ROOT / "htmlcov", PUBLIC / "coverage")

    env = os.environ.get
    image = env("CI_REGISTRY_IMAGE", "registry.gitlab.com/<you>/pipelinelab")
    page = Template((ROOT / "docs" / "site_template.html").read_text()).substitute(
        commit=html.escape(env("CI_COMMIT_SHORT_SHA", "local")),
        branch=html.escape(env("CI_COMMIT_REF_NAME", "local")),
        pipeline=html.escape(env("CI_PIPELINE_ID", "n/a")),
        pipeline_url=html.escape(env("CI_PIPELINE_URL", "#")),
        built=datetime.now(UTC).strftime("%d %b %Y, %H:%M UTC"),
        tests=f"{junit['passed']} of {junit['tests']}" if junit else "n/a",
        duration=f"{junit['time']:.1f}s" if junit else "n/a",
        coverage=f"{coverage}%" if coverage is not None else "n/a",
        coverage_link='<a href="coverage/index.html">Open the coverage report</a>'
        if coverage is not None
        else "",
        stages=stage_rail(),
        endpoints=endpoint_rows(read_endpoints()),
        image=html.escape(image),
    )
    (PUBLIC / "index.html").write_text(page)
    print(f"Site written to {PUBLIC}")


if __name__ == "__main__":
    main()
