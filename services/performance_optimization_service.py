# D:\major_project-copy\backend\services\performance_optimization_service.py

import asyncio
import time
import json
import logging
import gc
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from functools import wraps

import redis
import psutil
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("performance_service")
logger.setLevel(logging.INFO)


# =========================
# Exceptions
# =========================

class CacheError(Exception):
    pass


class OptimizationError(Exception):
    pass


# =========================
# Service
# =========================

class PerformanceOptimizationService:
    """
    Production-grade performance optimization service:
    - Redis caching
    - Query profiling
    - Memory optimization
    - Auto optimization suggestions
    - Performance monitoring
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 1,
        slow_query_threshold: float = 1.0,
        cache_ttl: int = 3600,
    ):
        try:
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
            )
            self.redis.ping()
        except Exception as e:
            logger.warning(f"Redis not available, caching disabled: {e}")
            self.redis = None

        self.slow_query_threshold = slow_query_threshold
        self.cache_ttl = cache_ttl

        self._metrics_buffer: List[Dict[str, Any]] = []

    # =========================
    # CACHE LAYER
    # =========================

    def cache_get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None

        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
            return None

    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None):
        if not self.redis:
            return

        try:
            self.redis.setex(
                key,
                ttl or self.cache_ttl,
                json.dumps(value, default=str),
            )
        except Exception as e:
            logger.error(f"Cache SET error: {e}")

    def cache_delete(self, key: str):
        if not self.redis:
            return

        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache DELETE error: {e}")

    # =========================
    # PERFORMANCE DECORATOR
    # =========================

    def monitor(self, cache_key: Optional[str] = None):
        """
        Decorator: tracks execution time + memory usage + caching
        """

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cached = None
                if cache_key:
                    cached = self.cache_get(cache_key)
                    if cached is not None:
                        return cached

                start_time = time.time()
                process = psutil.Process()

                mem_before = process.memory_info().rss / 1024 / 1024

                try:
                    result = func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)
                    raise
                finally:
                    mem_after = process.memory_info().rss / 1024 / 1024
                    duration = time.time() - start_time

                    metric = {
                        "function": func.__name__,
                        "duration": duration,
                        "memory_mb": mem_after,
                        "memory_delta": mem_after - mem_before,
                        "success": success,
                        "error": error,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    self._store_metric(metric)

                    if duration > self.slow_query_threshold:
                        logger.warning(
                            f"SLOW: {func.__name__} took {duration:.2f}s"
                        )

                if cache_key and success:
                    self.cache_set(cache_key, result)

                return result

            return wrapper

        return decorator

    # =========================
    # METRICS
    # =========================

    def _store_metric(self, metric: Dict[str, Any]):
        self._metrics_buffer.append(metric)

        if len(self._metrics_buffer) > 1000:
            self._metrics_buffer = self._metrics_buffer[-1000:]

    def get_metrics(self) -> List[Dict[str, Any]]:
        return self._metrics_buffer

    # =========================
    # MEMORY OPTIMIZATION
    # =========================

    def optimize_memory(self) -> Dict[str, Any]:
        process = psutil.Process()

        before = process.memory_info().rss / 1024 / 1024
        gc.collect()
        after = process.memory_info().rss / 1024 / 1024

        return {
            "memory_before_mb": before,
            "memory_after_mb": after,
            "freed_mb": before - after,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # =========================
    # CACHE OPTIMIZATION
    # =========================

    def cache_stats(self) -> Dict[str, Any]:
        if not self.redis:
            return {"status": "redis_not_available"}

        try:
            info = self.redis.info("memory")

            used = info.get("used_memory", 0)
            max_mem = info.get("maxmemory", 0)

            percent = (used / max_mem * 100) if max_mem else 0

            return {
                "used_memory": used,
                "max_memory": max_mem,
                "usage_percent": round(percent, 2),
            }
        except Exception as e:
            return {"error": str(e)}

    # =========================
    # DATABASE OPTIMIZATION HELPERS
    # =========================

    def analyze_slow_queries(self) -> Dict[str, Any]:
        slow = [
            m for m in self._metrics_buffer
            if m.get("duration", 0) > self.slow_query_threshold
        ]

        grouped = {}

        for m in slow:
            fn = m["function"]
            grouped.setdefault(fn, []).append(m["duration"])

        analysis = {}

        for fn, durations in grouped.items():
            analysis[fn] = {
                "count": len(durations),
                "avg": sum(durations) / len(durations),
                "max": max(durations),
            }

        return {
            "total_slow_queries": len(slow),
            "analysis": analysis,
        }

    # =========================
    # AUTO OPTIMIZATION
    # =========================

    async def auto_optimize(self) -> Dict[str, Any]:
        try:
            memory = self.optimize_memory()
            cache = self.cache_stats()
            slow = self.analyze_slow_queries()

            return {
                "memory": memory,
                "cache": cache,
                "slow_queries": slow,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "optimized",
            }

        except Exception as e:
            logger.error(f"Auto optimization failed: {e}")
            raise OptimizationError(str(e))

    # =========================
    # REPORTING
    # =========================

    def performance_report(self) -> Dict[str, Any]:
        if not self._metrics_buffer:
            return {"message": "No metrics available"}

        total = len(self._metrics_buffer)

        avg_time = sum(m["duration"] for m in self._metrics_buffer) / total
        error_count = sum(1 for m in self._metrics_buffer if not m["success"])

        slow_count = sum(
            1 for m in self._metrics_buffer
            if m["duration"] > self.slow_query_threshold
        )

        return {
            "total_requests": total,
            "avg_execution_time": round(avg_time, 4),
            "error_rate": round((error_count / total) * 100, 2),
            "slow_queries": slow_count,
            "timestamp": datetime.utcnow().isoformat(),
        }


# =========================
# GLOBAL INSTANCE
# =========================

performance_service = PerformanceOptimizationService()


# =========================
# BACKGROUND TASK
# =========================

async def periodic_optimization_task():
    """
    Runs lightweight system optimization periodically
    """
    while True:
        try:
            await performance_service.auto_optimize()
            await asyncio.sleep(3600)  # 1 hour
        except Exception as e:
            logger.error(f"Periodic optimization error: {e}")
            await asyncio.sleep(3600)