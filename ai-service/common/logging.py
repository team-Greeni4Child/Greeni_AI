# common/logging.py

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

from config import settings


class _JsonFormatter(logging.Formatter):
    """한 줄 JSON 로그 포맷터(파서 친화)."""

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "ts": int(time.time() * 1000),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # LoggerAdapter / extra 로 들어온 컨텍스트
        for k in ("request_id", "session_id", "path", "method", "status_code", "code"):
            if hasattr(record, k):
                base[k] = getattr(record, k)

        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)

        return json.dumps(base, ensure_ascii=False)


# common/logging.py

def setup_logging() -> None:
    level = logging.DEBUG if getattr(settings, "ENV", "dev") == "dev" else logging.INFO

    root = logging.getLogger()
    root.setLevel(level)

    formatter = _JsonFormatter()

    # 이미 핸들러가 있으면 덮어쓰기
    if root.handlers:
        for h in root.handlers:
            h.setLevel(level)
            h.setFormatter(formatter)
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        root.addHandler(handler)

    # uvicorn 로거들이 자체 핸들러를 갖고 있으면 JSON 포맷이 안 먹을 수 있으니 루트로 전파
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.setLevel(level)
        lg.propagate = True
        lg.handlers = []


class Logger(logging.LoggerAdapter):
    """context를 extra로 붙이는 LoggerAdapter."""

    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        merged = {**self.extra, **extra}
        kwargs["extra"] = merged
        return msg, kwargs

    def bind(
        self,
        *,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
    ) -> "Logger":
        new_extra = dict(self.extra)
        if request_id is not None:
            new_extra["request_id"] = request_id
        if session_id is not None:
            new_extra["session_id"] = session_id
        if path is not None:
            new_extra["path"] = path
        if method is not None:
            new_extra["method"] = method
        return Logger(self.logger, new_extra)


def get_logger(name: str = "greeni") -> Logger:
    """
    사용 예:
      from common.logging import get_logger
      log = get_logger(__name__).bind(session_id=req.session_id)
      log.info("roleplay reply ok", extra={"turn": turn})
    """
    setup_logging()
    return Logger(logging.getLogger(name), {})


# 모듈 레벨 기본 로거
log = get_logger("greeni")
