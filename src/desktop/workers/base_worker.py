"""
BaseWorker — Qt 线程安全基础类。

所有长时操作（摄入 / 查询 / 生成）继承此类，在独立 QThread 中执行。
主线程通过 Signal 接收进度和结果，不直接调用 Worker 方法。

铁律：
  - _execute() 中可以做任意 I/O / LLM 调用
  - _execute() 中禁止操作任何 Qt 控件（会崩溃）
  - Signal.emit() 是线程安全的，Qt 自动将其排队到主线程
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from PySide6.QtCore import QThread, Signal


@dataclass
class WorkerResult:
    success: bool
    data: Any = None
    error: Optional[str] = None


class BaseWorker(QThread):
    """所有 Worker 的基类。子类只需实现 _execute()。"""

    # 进度信号：(百分比 0-100, 描述消息)
    progress_updated = Signal(int, str)

    # 完成信号：无论成功或失败都会触发，携带 WorkerResult
    result_ready = Signal(object)

    # 独立错误信号（result_ready 失败时同时触发，方便只关注错误的槽）
    error_occurred = Signal(str)

    def run(self) -> None:
        """QThread 入口，不要覆盖此方法，覆盖 _execute() 代替。"""
        try:
            data = self._execute()
            self.result_ready.emit(WorkerResult(success=True, data=data))
        except Exception as exc:
            msg = str(exc)
            self.error_occurred.emit(msg)
            self.result_ready.emit(WorkerResult(success=False, error=msg))

    def _execute(self) -> Any:
        """子类实现：在 Worker 线程中执行业务逻辑，返回结果数据。"""
        raise NotImplementedError
