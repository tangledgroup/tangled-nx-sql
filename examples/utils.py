import asyncio
import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable)


def print_docstring(func: F) -> F:
    """Decorator that prints the function's docstring when called.

    Works with both sync and async functions.
    """

    @functools.wraps(func)
    def wrapper_sync(*args: Any, **kwargs: Any) -> Any:
        if func.__doc__:
            print(f"\n{'─' * 60}")
            print(f"📝 {func.__name__}: {func.__doc__.strip()}")
            print("─" * 60)
        return func(*args, **kwargs)

    @functools.wraps(func)
    async def wrapper_async(*args: Any, **kwargs: Any) -> Any:
        if func.__doc__:
            print(f"\n{'─' * 60}")
            print(f"📝 {func.__name__}: {func.__doc__.strip()}")
            print("─" * 60)
        return await func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return wrapper_async  # type: ignore[return-value]
    return wrapper_sync  # type: ignore[return-value]
