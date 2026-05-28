"""领域异常层级。"""
from __future__ import annotations


class DomainError(Exception):
    """所有领域异常的基类。"""


class NotFoundError(DomainError):
    """请求的资源不存在。"""
    def __init__(self, resource: str, id: str) -> None:
        super().__init__(f"{resource} not found: {id!r}")
        self.resource = resource
        self.id = id


class ValidationError(DomainError):
    """输入数据不符合领域规则。"""


class ConfigurationError(DomainError):
    """配置缺失或无效（如 kb_root 不存在）。"""


class IndexNotReadyError(DomainError):
    """工作区尚未完成索引，无法执行检索。"""
    def __init__(self, workspace_id: str) -> None:
        super().__init__(f"Workspace {workspace_id!r} has not been indexed yet.")
        self.workspace_id = workspace_id
