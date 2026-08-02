from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PACKAGES = {"react-router", "react-router-dom"}
ALLOWED_ADVISORY = "https://github.com/advisories/GHSA-qwww-vcr4-c8h2"
FORBIDDEN_RSC_MARKERS = (
    "unstable_rsc",
    "routerscserverrequest",
    "rschydratedrouter",
    "serverrouter",
    "react-server",
    "@react-router/dev",
    "@react-router/node",
    "@react-router/serve",
)


def main() -> int:
    npm = shutil.which("npm")
    if npm is None:
        print("npm executable was not found", file=sys.stderr)
        return 2

    result = subprocess.run(
        [npm, "audit", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(result.stderr or result.stdout or "npm audit returned no JSON", file=sys.stderr)
        return 2

    vulnerabilities = report.get("vulnerabilities", {})
    if result.returncode == 0 and not vulnerabilities:
        print("npm audit: 0 known vulnerabilities")
        return 0

    if not _is_allowed_router_exception(report):
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        print("npm audit contains an unapproved vulnerability", file=sys.stderr)
        return 1

    rsc_hits = _find_rsc_markers()
    if rsc_hits:
        for hit in rsc_hits:
            print(f"RSC security exception invalidated by {hit}", file=sys.stderr)
        return 1

    print(
        "npm audit: accepted 2 high findings for GHSA-qwww-vcr4-c8h2; "
        "frontend-v3 is a client-only HashRouter SPA and RSC/server entrypoints are absent"
    )
    return 0


def _is_allowed_router_exception(report: dict[str, Any]) -> bool:
    vulnerabilities = report.get("vulnerabilities")
    metadata = report.get("metadata", {}).get("vulnerabilities", {})
    if not isinstance(vulnerabilities, dict):
        return False
    if set(vulnerabilities) != ALLOWED_PACKAGES:
        return False
    if metadata.get("high") != 2 or metadata.get("total") != 2:
        return False

    advisory_urls: set[str] = set()
    for package, item in vulnerabilities.items():
        if not isinstance(item, dict) or item.get("severity") != "high":
            return False
        for via in item.get("via", []):
            if isinstance(via, dict):
                url = via.get("url")
                if isinstance(url, str):
                    advisory_urls.add(url)
            elif not isinstance(via, str) or via not in ALLOWED_PACKAGES:
                return False
        if package == "react-router-dom" and item.get("isDirect") is not True:
            return False
    return advisory_urls == {ALLOWED_ADVISORY}


def _find_rsc_markers() -> list[str]:
    candidates = [ROOT / "frontend-v3" / "package.json"]
    candidates.extend(
        path
        for path in (ROOT / "frontend-v3" / "src").rglob("*")
        if path.suffix in {".ts", ".tsx", ".js", ".jsx"} and ".test." not in path.name
    )
    hits: list[str] = []
    for path in candidates:
        content = path.read_text(encoding="utf-8").lower()
        for marker in FORBIDDEN_RSC_MARKERS:
            if marker in content:
                hits.append(f"{path.relative_to(ROOT)}: {marker}")
    return hits


if __name__ == "__main__":
    raise SystemExit(main())
