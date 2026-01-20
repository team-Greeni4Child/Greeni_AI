# common/errors.py
from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException


@dataclass
class AppError(Exception):
    """
    서비스 계층에서 쓰는 표준 예외
    - code: 프론트/로깅에서 안정적으로 분기 가능한 문자열
    - status_code: HTTP status
    - message: 사용자(또는 클라이언트)에게 보여줄 에러 메시지
    - detail: 내부 디버깅용
    """
    message: str
    code: str = "internal_error"
    status_code: int = 500
    detail: Optional[Any] = None

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=self.status_code,
            detail={"error": self.message, "code": self.code},
        )


def http_error(status_code: int, message: str, code: Optional[str] = None) -> HTTPException:

    payload: Dict[str, Any] = {"error": message}
    if code is not None:
        payload["code"] = code
    return HTTPException(status_code=status_code, detail=payload)

def register_exception_handlers(app: FastAPI, logger=None) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        # 응답은 항상 {"error": "...", "code": "..."} 형태로 고정
        if logger:
            logger.warning("app_error", extra={"code": exc.code, "status_code": exc.status_code})
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "code": exc.code},
        )


# 자주 쓰는 에러 팩토리(아직 미적용)
def bad_request(message: str = "bad request", code: str = "bad_request") -> AppError:
    return AppError(message=message, code=code, status_code=400)


def not_found(message: str = "not found", code: str = "not_found") -> AppError:
    return AppError(message=message, code=code, status_code=404)


def upstream_error(message: str = "upstream error", code: str = "upstream_error") -> AppError:
    return AppError(message=message, code=code, status_code=502)
