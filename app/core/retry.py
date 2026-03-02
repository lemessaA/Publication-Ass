from __future__ import annotations

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Callable, TypeVar


T = TypeVar("T")

logger = logging.getLogger(__name__)


def _run_with_timeout(fn: Callable[[], T], timeout_seconds: float) -> T:
  """Run a callable with a hard timeout using a thread pool."""
  with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(fn)
    return future.result(timeout=timeout_seconds)


def call_with_retries(
  fn: Callable[[], T],
  *,
  description: str,
  max_attempts: int = 3,
  base_delay: float = 0.5,
  max_delay: float = 4.0,
  timeout_seconds: float = 30.0,
) -> T | None:
  """Call fn with retry + exponential backoff and a per-attempt timeout.

  Returns None if all attempts fail or time out.
  """
  last_error: Exception | None = None

  for attempt in range(1, max_attempts + 1):
    try:
      return _run_with_timeout(fn, timeout_seconds=timeout_seconds)
    except FuturesTimeout as exc:
      last_error = exc  # type: ignore[assignment]
      logger.warning(
        "call_timeout description=%s attempt=%s/%s timeout=%ss",
        description,
        attempt,
        max_attempts,
        timeout_seconds,
      )
    except Exception as exc:
      last_error = exc
      logger.warning(
        "call_failed description=%s attempt=%s/%s error=%s",
        description,
        attempt,
        max_attempts,
        repr(exc),
      )

    if attempt < max_attempts:
      # Exponential backoff with jitter.
      delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
      delay *= random.uniform(0.7, 1.3)
      time.sleep(delay)

  logger.error(
    "call_gave_up description=%s attempts=%s last_error=%s",
    description,
    max_attempts,
    repr(last_error),
  )
  return None

