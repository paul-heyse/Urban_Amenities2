"""Typed wrappers around Dash helpers that lack stubs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

from dash import Dash
from dash import register_page as _register_page

P = ParamSpec("P")
R = TypeVar("R")

RegisterPageCallable = Callable[..., None]
DashCallbackDecorator = Callable[[Callable[..., Any]], Callable[..., Any]]


_REGISTER_PAGE = cast(RegisterPageCallable, _register_page)


def register_page(*args: Any, **kwargs: Any) -> None:
    """Typed façade for :func:`dash.register_page`."""

    _REGISTER_PAGE(*args, **kwargs)


def register_callback(
    app: Dash,
    *callback_args: Any,
    **callback_kwargs: Any,
) -> DashCallbackDecorator:
    """Return a typed callback decorator bound to ``app``."""

    callback_factory = cast(Callable[..., DashCallbackDecorator], app.callback)
    return callback_factory(*callback_args, **callback_kwargs)


__all__ = ["register_callback", "register_page"]
