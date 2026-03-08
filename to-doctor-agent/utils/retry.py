"""
utils/retry.py
通用重试装饰器 — 指数退避
"""
import asyncio
import functools
import logging
from typing import Type

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """异步重试装饰器，指数退避"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"[Retry] {func.__name__} 最终失败 "
                            f"(尝试 {attempt}/{max_attempts}): {e}"
                        )
                        raise
                    logger.warning(
                        f"[Retry] {func.__name__} 第 {attempt} 次失败: {e}, "
                        f"{delay:.1f}s 后重试"
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
            raise last_exception  # 不会到这里，但 type-checker 需要
        return wrapper
    return decorator
