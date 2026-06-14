from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from typing import ParamSpec, TypeVar

from .recorder import trace_recorder

P = ParamSpec("P")
R = TypeVar("R")


def _default_name(func: Callable[..., object]) -> str:
    return f"{func.__module__}.{func.__qualname__}"


def traced(
    name: str | None = None,
    *,
    kind: str = "function",
    detail: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        span_name = name or _default_name(func)

        if iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                with trace_recorder.span(span_name, kind=kind, detail=detail):
                    return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with trace_recorder.span(span_name, kind=kind, detail=detail):
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator
