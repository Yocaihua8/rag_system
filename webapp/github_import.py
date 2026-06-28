from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from webapp.config import runtime_dir
from webapp.ingestion import import_directory
from webapp.models import ImportResult, Project
from webapp.storage import KnowledgeStore


CloneRunner = Callable[[list[str]], None]
_GITHUB_SSH_URL = re.compile(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
_SAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class GitHubRepoReference:
    owner: str
    repo: str
    clone_url: str


@dataclass(frozen=True)
class GitHubRepoImport:
    project: Project
    result: ImportResult


def import_github_repo(
    store: KnowledgeStore,
    repo_url: str,
    branch: str = "",
    project_name: str = "",
    clone_root: Path | None = None,
    clone_runner: CloneRunner | None = None,
) -> GitHubRepoImport:
    reference = parse_github_repo_url(repo_url)
    clean_branch = branch.strip()
    root = Path(clone_root) if clone_root is not None else github_clone_root()
    root.mkdir(parents=True, exist_ok=True)
    target = _clone_target(root, reference, clean_branch)
    _prepare_clone_target(root, target)

    runner = clone_runner or run_git_clone
    runner(_clone_command(reference.clone_url, clean_branch, target))
    if not target.exists() or not target.is_dir():
        raise ValueError("git clone did not create repository directory")

    project = store.create_project(project_name.strip() or reference.repo, target)
    result = import_directory(store, project.id, target)
    return GitHubRepoImport(project=project, result=result)


def github_clone_root() -> Path:
    return runtime_dir() / "github-repos"


def parse_github_repo_url(repo_url: str) -> GitHubRepoReference:
    text = str(repo_url or "").strip()
    if not text:
        raise ValueError("repo_url is required")

    ssh_match = _GITHUB_SSH_URL.match(text)
    if ssh_match:
        owner, repo = ssh_match.groups()
        return _repo_reference(owner, repo, f"git@github.com:{owner}/{repo}.git")

    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").lower() != "github.com":
        raise ValueError("github repository url is invalid")
    if parsed.username or parsed.password:
        raise ValueError("github repository url must not include credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("github repository url is invalid")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        raise ValueError("github repository url is invalid")
    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    return _repo_reference(owner, repo, f"https://github.com/{owner}/{repo}.git")


def run_git_clone(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
    except FileNotFoundError as exc:
        raise ValueError("git executable not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("git clone timed out") from exc
    except subprocess.CalledProcessError as exc:
        detail = _safe_git_error(exc.stderr or exc.stdout)
        raise ValueError(f"git clone failed: {detail}") from exc


def _repo_reference(owner: str, repo: str, clone_url: str) -> GitHubRepoReference:
    owner = owner.strip()
    repo = repo.strip()
    if not owner or not repo:
        raise ValueError("github repository url is invalid")
    if not _is_safe_github_name(owner) or not _is_safe_github_name(repo):
        raise ValueError("github repository url is invalid")
    return GitHubRepoReference(owner=owner, repo=repo, clone_url=clone_url)


def _is_safe_github_name(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+", value))


def _clone_command(clone_url: str, branch: str, target: Path) -> list[str]:
    command = ["git", "clone", "--depth", "1"]
    if branch:
        command.extend(["--branch", branch])
    command.extend([clone_url, str(target)])
    return command


def _clone_target(clone_root: Path, reference: GitHubRepoReference, branch: str) -> Path:
    safe_owner = _safe_path_part(reference.owner)
    safe_repo = _safe_path_part(reference.repo)
    safe_branch = _safe_path_part(branch) if branch else "default"
    digest = hashlib.sha256(f"{reference.clone_url}\n{branch}".encode("utf-8")).hexdigest()[:12]
    return clone_root / f"{safe_owner}-{safe_repo}-{safe_branch}-{digest}"


def _safe_path_part(value: str) -> str:
    cleaned = _SAFE_NAME_CHARS.sub("-", value.strip()).strip(".-")
    return cleaned or "repo"


def _prepare_clone_target(clone_root: Path, target: Path) -> None:
    root = clone_root.resolve()
    target_path = target.resolve()
    if not _is_relative_to(target_path, root):
        raise ValueError("clone target is outside managed directory")
    if target.exists():
        shutil.rmtree(target)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _safe_git_error(output: str | None) -> str:
    text = " ".join((output or "").split())
    if not text:
        return "unknown error"
    return text[:300]
