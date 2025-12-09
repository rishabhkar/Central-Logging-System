"""Exception wrapper utilities to forward errors to OpenTelemetry-enabled logging."""
from __future__ import annotations

import logging
import sys
import threading
from types import TracebackType
from typing import Any, Callable, Optional, Type

_ExceptionHook = Callable[[Type[BaseException], BaseException, Optional[TracebackType]], None]
_ThreadHook = Callable[[threading.ExceptHookArgs], None]

_default_logger = logging.getLogger("central_logging.exceptions")
_hook_installed = False
_previous_sys_hook: Optional[_ExceptionHook] = None
_previous_thread_hook: Optional[_ThreadHook] = None


def _select_logger(logger: Optional[logging.Logger]) -> logging.Logger:
    return logger if logger is not None else _default_logger


def install_global_exception_handlers(
    *, logger: Optional[logging.Logger] = None, propagate_previous_hooks: bool = True
) -> None:
    """Route uncaught exceptions (main thread + threads) through the provided logger."""

    global _hook_installed, _previous_sys_hook, _previous_thread_hook, _default_logger

    if _hook_installed:
        if logger is not None:
            _default_logger = logger
        return

    _default_logger = _select_logger(logger)

    _previous_sys_hook = sys.excepthook

    def _sys_hook(exc_type: Type[BaseException], exc: BaseException, tb: Optional[TracebackType]) -> None:
        _default_logger.exception(
            "Unhandled exception bubbled to global handler",
            exc_info=(exc_type, exc, tb),
        )
        if propagate_previous_hooks and _previous_sys_hook is not None:
            _previous_sys_hook(exc_type, exc, tb)

    sys.excepthook = _sys_hook

    if hasattr(threading, "excepthook"):
        _previous_thread_hook = threading.excepthook  # type: ignore[attr-defined]

        def _thread_hook(args: threading.ExceptHookArgs) -> None:  # type: ignore[name-defined]
            thread_name = args.thread.name if args.thread else "<unknown>"
            _default_logger.exception(
                "Unhandled exception in thread %s", thread_name, exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
            )
            if propagate_previous_hooks and _previous_thread_hook is not None:
                _previous_thread_hook(args)

        threading.excepthook = _thread_hook  # type: ignore[attr-defined]

    _hook_installed = True


def run_with_exception_logging(
    func: Callable[..., Any],
    *args: Any,
    logger: Optional[logging.Logger] = None,
    rethrow: bool = False,
    **kwargs: Any,
) -> Any:
    """Execute *func* and log any exception before optionally propagating it."""

    active_logger = _select_logger(logger)
    try:
        return func(*args, **kwargs)
    except Exception:  # noqa: BLE001 - we intentionally want to capture everything
        func_name = getattr(func, "__qualname__", repr(func))
        active_logger.exception("Exception raised inside %s", func_name)
        if rethrow:
            raise
        return None


def exception_safe(
    *, logger: Optional[logging.Logger] = None, rethrow: bool = False
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator version of :func:`run_with_exception_logging`."""

    def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            return run_with_exception_logging(func, *args, logger=logger, rethrow=rethrow, **kwargs)

        return _wrapped

    return _decorator

