from contextvars import ContextVar, Token
from typing import Optional

_REQUEST_ID_CTX: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> Token:
    return _REQUEST_ID_CTX.set(request_id)


def get_request_id() -> Optional[str]:
    return _REQUEST_ID_CTX.get()


def reset_request_id(token: Token) -> None:
    _REQUEST_ID_CTX.reset(token)
