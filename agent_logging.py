from collections.abc import Callable
from contextvars import ContextVar
from functools import wraps
import inspect
import json
import logging
import re
from time import time
import time
from typing import Any, Mapping, Sequence

LOGGER_NAME = "xiaojie_agent"

_LOG_CONTEXT: ContextVar[tuple[str, str]] = ContextVar("course_log_context",
                                                       default=("-", "-"))
_MODEL_CALLED: ContextVar[bool] = ContextVar("course_model_called",
                                             default=False)
_TEACHING_EVENT_COUNT: ContextVar[int] = ContextVar(
    "course_teaching_event_count", default=0)
SECRET_KEYS = {
    "api_key", "apikey", "authorization", "password", "secret", "token",
    "access_token", "refresh_token", "cookie"
}
PRIVATE_KEY_MARKS = ("phone", "mobile", "address", "email", "id_card",
                     "identity_card", "bank_card")
PRIVATE_KEYS = {
    "nickname", "runtime_nickname", "runtime_user_id", "user_id",
    "customer_id", "customer_name", "user_name", "full_name"
}
HIDDEN_REASONING_KEYS = {
    "reasoning_content", "hidden_reasoning", "hidden_cot", "chain_of_thought"
}
VECTOR_ARRAY_KEYS = {"embedding", "embeddings", "vector", "vectors"}
_CURRENT_LESSON_ID = "-"

_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+\-/=]+")
_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
_CREDENTIAL = re.compile(
    r"(?i)((?:api[_-]?key|password|secret|access[_-]?token|refresh[_-]?token|cookie)\s*[:=]\s*)[^\s,，;；]+"
)
_PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
_ADDRESS = re.compile(r"(地址\s*[:：]\s*)[^\n,，;；]{4,80}")
_EMAIL = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b")


def _decorate_decorate_operation(func: Callable[..., Any],
                                 operation: str) -> Callable[..., Any]:
    lession_id = _CURRENT_LESSON_ID
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            token, model_token, teaching_token, started = _begin(
                args, kwargs, operation, lession_id)
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:

                raise e
            finally:
                _LOG_CONTEXT.reset(token)
                _MODEL_CALLED.reset(model_token)
                _TEACHING_EVENT_COUNT.reset(teaching_token)
    else:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            token, model_token, teaching_token, started = _begin(
                args, kwargs, operation, lession_id)
            try:
                result = func(*args, **kwargs)
                _finish(result, started, lession_id, operation)
                return result
            except Exception as e:
                _fail(e, operation)
                raise e
            finally:
                _LOG_CONTEXT.reset(token)
                _MODEL_CALLED.reset(model_token)
                _TEACHING_EVENT_COUNT.reset(teaching_token)

    return wrapper


def _begin(args: tuple[Any, ...], kwargs: dict[str, Any], operation_name: str,
           lession_id: str):
    request = _reqest(args, kwargs)
    token = _LOG_CONTEXT.set(
        (lession_id, str(getattr(request, "session_id", "-"))))
    model_token = _MODEL_CALLED.set(False)
    teaching_token = _TEACHING_EVENT_COUNT.set(0)
    if operation_name == "chat":
        message = "收到聊天请求，输入长度为%d"
        params = (len(str(getattr(request, "user_message", ""))), )
    else:
        message, params = f"开始{operation_name}操作", ()
    event_code = "CHAT_REQUEST_STARTED" if operation_name == "chat" else f"{operation_name.upper()}_STARTED"
    logger = logging.getLogger(LOGGER_NAME)
    logger.info(message, *params, extra={"event_code": event_code})
    if request is not None:
        request_detail = vars(request) if hasattr(request,
                                                  "__dict__") else request
        logger.debug("请求结构=%s",
                     sanitize(request_detail),
                     extra={"event_code": "REQUEST_DETAIL"})
    return token, model_token, teaching_token, time.perf_counter()


def _finish(result: Any, started: float, lession_id: str, operation_name: str):
    logger = logging.getLogger(LOGGER_NAME)
    data = _dump(result)


def _fail(e: Exception, operation_name: str):
    logger = logging.getLogger(LOGGER_NAME)


def _reqest(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any | None:
    return next(
        (item
         for item in (args, kwargs.values()) if hasattr(item, "session_id")),
        None)


def _dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return dict(value) if isinstance(value, Mapping) else {}


def _redact_text(value: str) -> str:
    value = _BEARER.sub("Bearer ***", value)
    value = _KEY.sub("sk-***", value)
    value = _CREDENTIAL.sub(r"\1***", value)
    value = _PHONE.sub("***手机号***", value)
    value = _ADDRESS.sub(r"\1***地址***", value)
    return _EMAIL.sub("***邮箱***", value)


def observe_chat(func: Callable[..., Any]) -> Callable[..., Any]:
    """用一处装饰器记录聊天请求，避免在 Agent 分支里堆日志。"""
    return _decorate_decorate_operation(func, "chat")


def sanitize(value: Any) -> Any:
    """做教学日志的最小必要脱敏，同时保留可学习的业务结构。"""
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            name = str(key).lower()
            normalized_name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
            if normalized_name in SECRET_KEYS or normalized_name.endswith((
                    "_api_key",
                    "_password",
                    "_secret",
                    "_token",
                    "_authorization",
                    "_cookie",
            )):
                result[str(key)] = "***敏感凭据***"
            elif normalized_name in PRIVATE_KEYS or normalized_name.endswith(
                    "_user_id") or any(mark in normalized_name
                                       for mark in PRIVATE_KEY_MARKS):
                result[str(key)] = "***个人隐私***"
            elif name in HIDDEN_REASONING_KEYS:
                result[str(key)] = "***隐藏推理不记录***"
            elif name in VECTOR_ARRAY_KEYS and isinstance(
                    item,
                    Sequence) and not isinstance(item,
                                                 (str, bytes, bytearray)):
                first = item[0] if item else []
                nested = isinstance(first, Sequence) and not isinstance(
                    first, (str, bytes, bytearray))
                result[str(key)] = {
                    "数组已省略": True,
                    "输入数": len(item) if nested else 1,
                    "维度": len(first) if nested else len(item)
                }
            else:
                result[str(key)] = sanitize(item)
        return result
    if isinstance(value, Sequence) and not isinstance(value,
                                                      (str, bytes, bytearray)):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, (Mapping, list)):
                    return json.dumps(sanitize(parsed), ensure_ascii=False)
            except (TypeError, ValueError):
                pass
        return _redact_text(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _redact_text(str(value))
