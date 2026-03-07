"""
utils/time_utils.py
新加坡时区 (SGT, UTC+8) 处理 + 周切片逻辑
"""
from datetime import datetime, timedelta, timezone

SGT = timezone(timedelta(hours=8))


def now_sgt() -> datetime:
    """当前新加坡时间"""
    return datetime.now(SGT)


def today_sgt() -> datetime:
    """今天 00:00 SGT"""
    n = now_sgt()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


def week_start_sgt(dt: datetime | None = None) -> datetime:
    """获取某天所在周的周一 00:00 SGT"""
    if dt is None:
        dt = now_sgt()
    monday = dt - timedelta(days=dt.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def week_end_sgt(dt: datetime | None = None) -> datetime:
    """获取某天所在周的周日 23:59 SGT"""
    start = week_start_sgt(dt)
    return start + timedelta(days=6, hours=23, minutes=59, seconds=59)


def days_since(past_date: datetime | None) -> int | None:
    """计算距今天数"""
    if past_date is None:
        return None
    delta = now_sgt() - past_date.replace(tzinfo=SGT) if past_date.tzinfo is None else now_sgt() - past_date
    return max(0, delta.days)


def hours_since_last_meal(meals: list) -> float | None:
    """距上次用餐的小时数"""
    if not meals:
        return None
    latest = max(m.get("timestamp") or m.get("taken_at") or datetime.min for m in meals
                 if isinstance(m, dict))
    if latest == datetime.min:
        return None
    now = now_sgt()
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=SGT)
    delta = now - latest
    return delta.total_seconds() / 3600
